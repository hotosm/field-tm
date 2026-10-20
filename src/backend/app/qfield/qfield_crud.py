# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Logic for interaction with QFieldCloud & data."""

import asyncio
import base64
import json
import logging
import os
import re
import shutil
import tempfile
import zipfile
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from copy import deepcopy
from functools import partial
from io import BytesIO
from pathlib import Path
from random import getrandbits
from typing import Optional
from uuid import uuid4

import httpx
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import AsyncConnection
from qfieldcloud_sdk.sdk import (
    FileTransferType,
    JobTypes,
    ProjectCollaboratorRole,
)

from app.config import decrypt_value, encrypt_value, settings
from app.db.models import DbProject
from app.helpers.geometry_utils import stamp_missing_task_ids
from app.i18n import _
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud
from app.qfield.qfield_utils import resolve_backend_qfc_url

log = logging.getLogger(__name__)

# Slightly longer than the wrapper's QGIS_DISPATCH_TIMEOUT_SECONDS so the
# server-side timeout fires first with its descriptive error message.
QGIS_REQUEST_TIMEOUT = httpx.Timeout(660)
QFC_NAME_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")

# Field-TM QField plugin: bundled and sent to the QGIS wrapper on every
# field-project generation.  The wrapper unpacks ``main.qml`` as the
# project plugin and applies any ``styles/{layer_name}.qml`` to matching
# layers.  Path is overridable via env for tests / non-standard layouts.
QFIELD_PLUGIN_DIR = os.environ.get("QFIELD_PLUGIN_DIR", "/opt/qfield-plugin")
_qfield_plugin_zip_b64: Optional[str] = None


def _build_qfield_plugin_zip_b64() -> Optional[str]:
    """Build (once) a base64-encoded zip of the bundled QField plugin dir."""
    global _qfield_plugin_zip_b64
    if _qfield_plugin_zip_b64 is not None:
        return _qfield_plugin_zip_b64 or None

    plugin_dir = Path(QFIELD_PLUGIN_DIR)
    if not plugin_dir.is_dir():
        log.warning(
            "QFIELD_PLUGIN_DIR %s not found; sending no plugin to wrapper", plugin_dir
        )
        _qfield_plugin_zip_b64 = ""
        return None

    buf = BytesIO()
    files_added = 0
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(plugin_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(plugin_dir)
            arcname = str(rel)
            # The plugin .qml at the root is renamed to ``main.qml`` so the
            # wrapper can rebrand it to ``{title}.qml`` per QField convention.
            if rel.parent == Path(".") and rel.suffix == ".qml":
                arcname = "main.qml"
            zf.write(path, arcname)
            files_added += 1

    if files_added == 0:
        log.warning(
            "QFIELD_PLUGIN_DIR %s is empty; sending no plugin to wrapper", plugin_dir
        )
        _qfield_plugin_zip_b64 = ""
        return None

    _qfield_plugin_zip_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    log.info(
        "Built QField plugin zip (%d files, %d bytes b64)",
        files_added,
        len(_qfield_plugin_zip_b64),
    )
    return _qfield_plugin_zip_b64


# Geometry helpers


_COORD_NESTING = {
    "Point": 0,
    "LineString": 1,
    "MultiPoint": 1,
    "Polygon": 2,
    "MultiLineString": 2,
    "MultiPolygon": 3,
}


def _flatten_geom_coords(geom: dict) -> list:
    """Flatten all coordinates in a GeoJSON geometry to a list of [lon, lat] pairs."""
    geom_type = geom.get("type", "")
    if geom_type == "GeometryCollection":
        return [
            c for sub in geom.get("geometries", []) for c in _flatten_geom_coords(sub)
        ]
    if geom_type not in _COORD_NESTING:
        return []
    coords = [geom.get("coordinates", [])]
    for _level in range(_COORD_NESTING[geom_type]):
        coords = [c for part in coords for c in part]
    return coords


def _outline_to_bbox_str(outline: dict) -> str:
    """Compute a comma-separated bbox string (xmin,ymin,xmax,ymax) from outline.

    The outline may be a raw GeoJSON geometry, a Feature, or a FeatureCollection.
    """
    geometry = _extract_geometry(outline)
    if not geometry:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Project outline is missing or has no geometry."),
        )
    coords = _flatten_geom_coords(geometry)
    if not coords:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Project outline geometry has no coordinates."),
        )
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return f"{min(lons)},{min(lats)},{max(lons)},{max(lats)}"


def _extract_geometry(geojson_obj: dict) -> Optional[dict]:
    """Extract the geometry dict from a GeoJSON object of any type."""
    if not geojson_obj or not isinstance(geojson_obj, dict):
        return None
    obj_type = geojson_obj.get("type", "")
    if obj_type == "FeatureCollection":
        features = geojson_obj.get("features", [])
        if features and isinstance(features[0], dict):
            return features[0].get("geometry", features[0])
        return None
    if obj_type == "Feature":
        return geojson_obj.get("geometry")
    if "coordinates" in geojson_obj:
        return geojson_obj
    return None


def _dominant_geom_type(data_extract: Optional[dict]) -> DbGeomType:
    """Determine the dominant geometry type from a FeatureCollection."""
    if not data_extract or not isinstance(data_extract, dict):
        return DbGeomType.POINT
    features = data_extract.get("features", [])
    if not features:
        return DbGeomType.POINT

    counts = {"point": 0, "polygon": 0, "line": 0}
    for feat in features:
        gtype = (feat.get("geometry") or {}).get("type", "").lower()
        if "polygon" in gtype:
            counts["polygon"] += 1
        elif "line" in gtype:
            counts["line"] += 1
        else:
            counts["point"] += 1

    dominant = max(counts, key=counts.get)
    mapping = {
        "point": DbGeomType.POINT,
        "polygon": DbGeomType.POLYGON,
        "line": DbGeomType.LINESTRING,
    }
    return mapping[dominant]


def _sanitize_qfc_project_name(name: str) -> str:
    """Normalize a QFieldCloud project name to API-accepted characters."""
    cleaned = QFC_NAME_SANITIZE_PATTERN.sub("-", (name or "").strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-.")
    return cleaned or f"FieldTM-project-{getrandbits(32)}"


# Data preparation helpers


def clean_tags_for_qgis(
    geojson_data: dict,
) -> dict:
    """Flatten tags to key=value;... and stringify other non-scalar properties.

    QGIS cannot write nested JSON or lists back to GeoJSON.
    """
    if not geojson_data or "features" not in geojson_data:
        return geojson_data

    safe_geojson = deepcopy(geojson_data)

    for feature in safe_geojson.get("features", []):
        properties = feature.get("properties", {})
        safe_properties = {
            key: _qgis_safe_property_value(key, value)
            for key, value in properties.items()
        }
        safe_properties["tags"] = _qgis_safe_tags_value(safe_properties.get("tags"))
        feature["properties"] = safe_properties

    return safe_geojson


def _qgis_safe_property_value(key: str, value):
    """Normalize non-scalar property values before writing GeoJSON for QGIS."""
    if key == "tags":
        return value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _parse_json_tags(tags):
    """Return a dict for JSON object strings, else the value unchanged."""
    if not (isinstance(tags, str) and tags.startswith("{") and tags.endswith("}")):
        return tags
    try:
        parsed = json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        return tags
    return parsed if isinstance(parsed, dict) else tags


def _qgis_safe_tags_value(tags) -> str:
    """Normalize the ``tags`` property to a QGIS-safe string."""
    if not tags:
        return ""
    tags = _parse_json_tags(tags)
    if isinstance(tags, dict):
        return ";".join(f"{k}={v}" for k, v in tags.items())
    if isinstance(tags, list):
        return json.dumps(tags, ensure_ascii=False, separators=(",", ":"))
    return str(tags)


def _build_tasks_geojson(project: DbProject) -> dict:
    """Build tasks from the task plan, falling back to the outline.

    The QField plugin reads ``group`` (the planner's ``assigned_group``);
    field progress lives in the separate ``tasks_events`` layer.
    """
    task_areas = project.task_areas_geojson
    if task_areas and isinstance(task_areas, dict) and task_areas.get("features"):
        # Stored ids are authoritative; stamping covers legacy rows in memory.
        features = stamp_missing_task_ids(task_areas)["features"]
    else:
        geometry = _extract_geometry(project.outline)
        if not geometry:
            return {"type": "FeatureCollection", "features": []}
        features = [{"type": "Feature", "geometry": geometry, "properties": {}}]

    tasks = []
    for task_id, feature in enumerate(features, start=1):
        properties = feature.get("properties") or {}
        tasks.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": {
                    "task_id": properties.get("task_id", task_id),
                    "group": properties.get("assigned_group") or None,
                },
            }
        )
    return {"type": "FeatureCollection", "features": tasks}


def _build_features_geojson(project: DbProject) -> dict:
    """Return the data extract FeatureCollection, or an empty one."""
    extract = project.data_extract_geojson
    if (
        extract
        and isinstance(extract, dict)
        and extract.get("type") == "FeatureCollection"
    ):
        return extract
    return {"type": "FeatureCollection", "features": []}


def _strip_feature_properties_for_qfield(features_geojson: dict) -> dict:
    """Keep seeded geometries, but drop source attributes before QGIS conversion."""
    if not isinstance(features_geojson, dict):
        return {"type": "FeatureCollection", "features": []}

    stripped = deepcopy(features_geojson)
    sanitized_features = []
    for feature in stripped.get("features", []):
        if not isinstance(feature, dict):
            continue
        sanitized_feature = {
            "type": feature.get("type", "Feature"),
            "geometry": feature.get("geometry"),
            "properties": {},
        }
        if "id" in feature:
            sanitized_feature["id"] = feature["id"]
        sanitized_features.append(sanitized_feature)

    stripped["features"] = sanitized_features
    return stripped


def _should_open_in_edit_mode(data_extract: Optional[dict]) -> bool:
    """Keep edit mode only for collect-new-data projects with no seed features."""
    if not isinstance(data_extract, dict):
        return True
    features = data_extract.get("features")
    return not isinstance(features, list) or len(features) == 0


def _resolve_backend_qfc_url(url: str) -> str:
    """Use the internal QFieldCloud URL for browser-facing *.localhost hosts."""
    return resolve_backend_qfc_url(url)


def _resolve_project_qfield_credentials(project: DbProject) -> QFieldCloud | None:
    """Return stored project credentials, or None to use deployment defaults."""
    if not all(
        [
            project.external_project_instance_url,
            project.external_project_username,
            project.external_project_password_encrypted,
        ]
    ):
        return None

    try:
        password = decrypt_value(project.external_project_password_encrypted)
    except Exception as exc:
        log.warning(
            "Failed to decrypt stored QField credentials for project %s: %s",
            project.id,
            exc,
        )
        return None

    backend_url = _resolve_backend_qfc_url(project.external_project_instance_url)

    return QFieldCloud(
        qfield_cloud_url=backend_url,
        qfield_cloud_user=project.external_project_username,
        qfield_cloud_password=password,
    )


def get_missing_basemap_attach_config(project: DbProject | None = None) -> list[str]:
    """Return required config keys missing for basemap attach workflow."""
    missing: list[str] = []
    if not (settings.QFIELDCLOUD_QGIS_URL or "").strip():
        missing.append("QFIELDCLOUD_QGIS_URL")

    custom_creds = _resolve_project_qfield_credentials(project) if project else None
    if custom_creds:
        return missing

    if not (settings.QFIELDCLOUD_URL or "").strip():
        missing.append("QFIELDCLOUD_URL")
    if not (settings.QFIELDCLOUD_USER or "").strip():
        missing.append("QFIELDCLOUD_USER")
    if not (
        settings.QFIELDCLOUD_PASSWORD
        and settings.QFIELDCLOUD_PASSWORD.get_secret_value().strip()
    ):
        missing.append("QFIELDCLOUD_PASSWORD")

    return missing


# Core: create QField project


@asynccontextmanager
async def _generate_qgis_project(
    db: AsyncConnection,
    project: DbProject,
    xlsform_bytes: bytes,
    form_language: str = "",
):
    """Generate the QGIS project via the wrapper; yield a dir with its files."""
    features_geojson = _build_features_geojson(project)
    features_geojson = _strip_feature_properties_for_qfield(features_geojson)
    features_geojson = clean_tags_for_qgis(features_geojson)
    tasks_geojson = clean_tags_for_qgis(_build_tasks_geojson(project))

    job_id = uuid4()
    await _insert_qgis_job(db, job_id, xlsform_bytes, features_geojson, tasks_geojson)
    await db.commit()

    tmp_dir = tempfile.mkdtemp(prefix="qfield_upload_")
    try:
        await _call_qgis_wrapper(
            job_id=str(job_id),
            title=project.project_name or f"project-{project.id}",
            description=project.description or "Created by the Field Tasking Manager",
            author=project.created_by_sub or "Field Tasking Manager",
            language=form_language,
            extent=_outline_to_bbox_str(project.outline),
            open_in_edit_mode=_should_open_in_edit_mode(project.data_extract_geojson),
        )

        output_files = await _read_qgis_job_outputs(db, job_id)
        await db.commit()
        if not output_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_("QGIS wrapper completed but wrote no output files."),
            )

        for filename, b64_content in output_files.items():
            target = Path(tmp_dir) / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(b64_content))

        qgz_files = list(Path(tmp_dir).glob("*.qgz"))
        if not qgz_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_("QGIS wrapper completed but no .qgz file in output."),
            )
        log.info("QGIS project generated: %s", qgz_files[0].name)
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        await _delete_qgis_job(db, job_id)
        await db.commit()


async def create_qfield_project(
    db: AsyncConnection,
    project: DbProject,
    custom_qfield_creds: QFieldCloud | None = None,
    default_language: str | None = None,
) -> str:
    """Generate a QGIS project, upload it, and return its QFieldCloud URL.

    Raises HTTPException on failure.
    """
    if not project.outline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Project outline is required for QField project creation."),
        )
    if not project.xlsform_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("XLSForm is required for QField project creation."),
        )

    form_language, final_form = await modify_form_for_qfield(
        BytesIO(project.xlsform_content),
        geom_layer_type=_dominant_geom_type(project.data_extract_geojson),
        default_language=default_language,
    )
    xlsform_bytes = final_form.getvalue()
    if not xlsform_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Failed to modify XLSForm for QField."),
        )

    log.debug("Saving QField XLSForm to DB for project %s", project.id)
    await DbProject.update(
        db,
        project.id,
        ProjectUpdate(xlsform_content=xlsform_bytes),
    )
    await db.commit()

    async with _generate_qgis_project(
        db, project, xlsform_bytes, form_language or ""
    ) as tmp_dir:
        title = project.project_name or f"project-{project.id}"
        qfc_project_name = _sanitize_qfc_project_name(
            f"FieldTM-{title}-{getrandbits(32)}"
        )
        return await _upload_to_qfieldcloud(
            project=project,
            description=project.description or "Created by the Field Tasking Manager",
            qfc_project_name=qfc_project_name,
            final_project_dir=tmp_dir,
            custom_qfield_creds=custom_qfield_creds,
            db=db,
        )


# Re-sync replaces only the task layers: re-uploading the survey or features
# GeoPackages would overwrite data mappers already synced to QFieldCloud.
QFIELD_TASK_LAYER_FILES = frozenset({"tasks.gpkg", "project-area.gpkg"})


async def resync_qfield_tasks(db: AsyncConnection, project: DbProject) -> None:
    """Regenerate the QGIS project and re-upload its task layers to QFieldCloud."""
    async with _generate_qgis_project(db, project, project.xlsform_content) as tmp_dir:
        for path in Path(tmp_dir).iterdir():
            if path.name in QFIELD_TASK_LAYER_FILES:
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

        loop = get_running_loop()
        creds = _resolve_project_qfield_credentials(project)
        async with qfield_client(creds) as client:
            await loop.run_in_executor(
                None,
                partial(
                    client.upload_files,
                    project_id=project.external_project_id,
                    upload_type=FileTransferType.PROJECT,
                    project_path=tmp_dir,
                    filter_glob="*",
                    throw_on_error=True,
                    force=True,
                ),
            )


async def attach_basemap_to_qfield_project(
    db: AsyncConnection,
    project: DbProject,
    basemap_url: str,
) -> None:
    """Attach an MBTiles basemap to an existing QField project via QGIS wrapper."""
    if not project.external_project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("QField project ID is missing; cannot attach basemap."),
        )

    custom_qfield_creds = _resolve_project_qfield_credentials(project)

    job_id = uuid4()

    try:
        await _insert_qgis_job(
            db,
            job_id,
            b"",
            {},
            {},
            operation="basemap",
            project_id=str(project.external_project_id),
            basemap_url=basemap_url,
        )
        await db.commit()

        await _call_qgis_wrapper(
            job_id=str(job_id),
            title=project.project_name or f"project-{project.id}",
            description=project.description or "Created by the Field Tasking Manager",
            author=project.created_by_sub or "Field Tasking Manager",
            language="",
            extent="0,0,0,0",
            open_in_edit_mode=False,
            endpoint="/basemap",
            qfield_cloud=custom_qfield_creds,
        )

        output_files = await _read_qgis_job_outputs(db, job_id)
        await db.commit()
        if not output_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_("Basemap attach completed but produced no project files."),
            )

        upload_dir = tempfile.mkdtemp(prefix="qfield_basemap_upload_")
        try:
            for filename, b64_content in output_files.items():
                target = Path(upload_dir) / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base64.b64decode(b64_content))

            await _download_file_for_qfield_upload(
                basemap_url,
                Path(upload_dir) / "basemap.mbtiles",
            )

            loop = get_running_loop()
            async with qfield_client(custom_qfield_creds) as client:
                await loop.run_in_executor(
                    None,
                    partial(
                        client.upload_files,
                        project_id=project.external_project_id,
                        upload_type=FileTransferType.PROJECT,
                        project_path=upload_dir,
                        filter_glob="*",
                        throw_on_error=True,
                        force=True,
                    ),
                )
        finally:
            shutil.rmtree(upload_dir, ignore_errors=True)
    finally:
        await _delete_qgis_job(db, job_id)
        await db.commit()


async def _insert_qgis_job(
    db: AsyncConnection,
    job_id,
    xlsform: bytes,
    features: dict,
    tasks: dict,
    operation: str = "field",
    project_id: Optional[str] = None,
    basemap_url: Optional[str] = None,
) -> None:
    """Insert a new QGIS job with input files into the database."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO qgis_jobs (
                job_id,
                xlsform,
                features,
                tasks,
                operation,
                project_id,
                basemap_url
            )
            VALUES (
                %(job_id)s,
                %(xlsform)s,
                %(features)s,
                %(tasks)s,
                %(operation)s,
                %(project_id)s,
                %(basemap_url)s
            )
            """,
            {
                "job_id": job_id,
                "xlsform": xlsform,
                "features": json.dumps(features),
                "tasks": json.dumps(tasks),
                "operation": operation,
                "project_id": project_id,
                "basemap_url": basemap_url,
            },
        )
    log.debug("Inserted QGIS job %s", job_id)


async def _read_qgis_job_outputs(
    db: AsyncConnection,
    job_id,
) -> dict | None:
    """Read the output_files dict written by the QGIS wrapper."""
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT output_files FROM qgis_jobs WHERE job_id = %(job_id)s",
            {"job_id": job_id},
        )
        row = await cur.fetchone()
    if not row or not row[0]:
        return None
    return row[0]


async def _delete_qgis_job(db: AsyncConnection, job_id) -> None:
    """Delete a completed or failed QGIS job."""
    async with db.cursor() as cur:
        await cur.execute(
            "DELETE FROM qgis_jobs WHERE job_id = %(job_id)s",
            {"job_id": job_id},
        )
    log.debug("Deleted QGIS job %s", job_id)


async def _wait_for_projectfile_processing(
    *,
    loop,
    client,
    api_project_id: str,
    attempts: int = 3,
    poll_interval: float = 2.0,
    poll_timeout: float = 180.0,
) -> None:
    """Trigger projectfile processing, poll for completion, and retry failures.

    Gunicorn worker rotation can interrupt uploads or auto-enqueued jobs,
    leaving an incomplete project. Force processing after all files are uploaded.
    """
    last_status: Optional[str] = None
    for attempt in range(1, attempts + 1):
        job = await loop.run_in_executor(
            None,
            partial(
                client.job_trigger,
                api_project_id,
                JobTypes.PROCESS_PROJECTFILE,
                force=True,
            ),
        )
        job_id = job.get("id")
        if not job_id:
            log.warning(
                "QFC job_trigger returned no id on attempt %d for project %s",
                attempt,
                api_project_id,
            )
            continue

        elapsed = 0.0
        while elapsed < poll_timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            try:
                status_resp = await loop.run_in_executor(
                    None, partial(client.job_status, job_id)
                )
            except Exception as exc:
                log.warning(
                    "QFC job_status failed on attempt %d for job %s: %s",
                    attempt,
                    job_id,
                    exc,
                )
                continue
            last_status = status_resp.get("status")
            if last_status == "finished":
                log.info(
                    "QFC process_projectfile finished on attempt %d for project %s",
                    attempt,
                    api_project_id,
                )
                return
            if last_status == "failed":
                log.warning(
                    "QFC process_projectfile failed on attempt %d for project %s",
                    attempt,
                    api_project_id,
                )
                break
        else:
            log.warning(
                "QFC process_projectfile timed out on attempt %d for project %s "
                "(last status: %s)",
                attempt,
                api_project_id,
                last_status,
            )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=_(
            "QFieldCloud did not finish processing the project file after "
            "%(attempts)d attempts (last status: %(status)s)."
        )
        % {"attempts": attempts, "status": last_status or "unknown"},
    )


async def _call_qgis_wrapper(  # noqa: PLR0913
    *,
    job_id: str,
    title: str,
    description: str,
    author: str,
    language: str,
    extent: str,
    open_in_edit_mode: bool,
    endpoint: str = "/",
    qfield_cloud: QFieldCloud | None = None,
) -> None:
    """Request project generation using a job_id and processing parameters.

    Input and output files are exchanged through the shared qgis_jobs table.
    """
    qgis_url = settings.QFIELDCLOUD_QGIS_URL
    payload = {
        "job_id": job_id,
        "title": title,
        "description": description,
        "author": author,
        "language": language,
        "extent": extent,
        "open_in_edit_mode": open_in_edit_mode,
    }
    if endpoint in ("/", "/field"):
        plugin_zip_b64 = _build_qfield_plugin_zip_b64()
        if plugin_zip_b64:
            payload["plugin_zip"] = plugin_zip_b64
    if qfield_cloud:
        if qfield_cloud.qfield_cloud_url:
            payload["qfield_cloud_url"] = qfield_cloud.qfield_cloud_url
        if qfield_cloud.qfield_cloud_user:
            payload["qfield_cloud_user"] = qfield_cloud.qfield_cloud_user
        if qfield_cloud.qfield_cloud_password:
            payload["qfield_cloud_password"] = qfield_cloud.qfield_cloud_password

    log.info("Calling QGIS wrapper at %s for project '%s'", qgis_url, title)

    async with httpx.AsyncClient(timeout=QGIS_REQUEST_TIMEOUT) as client:
        response = await client.post(f"{qgis_url}{endpoint}", json=payload)
    body = response.text
    if response.status_code != status.HTTP_200_OK:
        log.error("QGIS wrapper returned %s: %s", response.status_code, body)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QGIS project generation failed: %(error)s") % {"error": body},
        )
    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QGIS wrapper returned invalid JSON."),
        ) from exc
    if result.get("status") != "success":
        msg = result.get("message", "Unknown error")
        log.error("QGIS wrapper reported failure: %s", msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QGIS project generation failed: %(error)s") % {"error": msg},
        )

    log.debug("QGIS wrapper call succeeded for job %s", job_id)


async def _download_file_for_qfield_upload(url: str, destination: Path) -> None:
    """Download a remote file directly to disk for QFieldCloud upload."""
    async with (
        httpx.AsyncClient(timeout=600, follow_redirects=True) as client,
        client.stream("GET", url) as response,
    ):
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    _(
                        "Failed to download basemap MBTiles for upload "
                        "(HTTP %(status)s)."
                    )
                    % {"status": response.status_code}
                ),
            )

        with destination.open("wb") as output:
            async for chunk in response.aiter_bytes(1024 * 1024):
                if chunk:
                    output.write(chunk)

    if not destination.exists() or destination.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Downloaded basemap MBTiles is empty."),
        )


async def _upload_to_qfieldcloud(
    *,
    project: DbProject,
    description: str,
    qfc_project_name: str,
    final_project_dir: str,
    custom_qfield_creds: QFieldCloud | None,
    db: AsyncConnection,
) -> str:
    """Create a public QFieldCloud project, upload files, and return its URL.

    Any QFieldCloud user can open the project and sync data as an editor, so
    mappers need no invites or shared accounts.
    """
    loop = get_running_loop()

    log.info("Creating QFieldCloud project: %s", qfc_project_name)
    async with qfield_client(custom_qfield_creds) as client:
        qfc_owner = _resolve_qfc_owner(client, custom_qfield_creds)

        qfield_project = await loop.run_in_executor(
            None,
            partial(
                client.create_project,
                qfc_project_name,
                owner=qfc_owner,
                description=description,
                is_public=True,
                public_collaborator_role=ProjectCollaboratorRole.EDITOR,
            ),
        )
        log.debug("QFieldCloud project created: %s", qfield_project)

        api_project_id = qfield_project.get("id")

        try:
            log.info(f"Uploading files to QFieldCloud project {qfc_project_name}")
            upload_info = await loop.run_in_executor(
                None,
                partial(
                    client.upload_files,
                    project_id=api_project_id,
                    upload_type=FileTransferType.PROJECT,
                    project_path=final_project_dir,
                    filter_glob="*",
                    throw_on_error=True,
                    force=True,
                ),
            )
            log.debug("Upload complete: %s", upload_info)

            # Retry processing after uploads in case worker rotation interrupted it.
            await _wait_for_projectfile_processing(
                loop=loop,
                client=client,
                api_project_id=api_project_id,
            )
        except Exception as e:
            # Rollback: delete the QFieldCloud project on upload failure
            log.warning(
                "Upload failed, deleting QFieldCloud project %s", api_project_id
            )
            try:
                await loop.run_in_executor(
                    None,
                    partial(client.delete_project, api_project_id),
                )
            except Exception:
                log.warning("Failed to clean up QFieldCloud project %s", api_project_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=_("Failed to upload files to QFieldCloud: %(error)s")
                % {"error": e},
            ) from e

    # Prefer a canonical URL returned by QFieldCloud, otherwise fall back to
    # the instance root instead of guessing an internal route.
    qfield_url = _resolve_qfield_project_url(qfield_project, custom_qfield_creds)

    update_payload = ProjectUpdate(
        external_project_id=api_project_id,
        external_project_instance_url=qfield_url,
    )
    # Keep custom credentials so later resyncs, basemaps and exports reach
    # the same instance; deployment defaults need nothing stored.
    if custom_qfield_creds:
        update_payload.external_project_username = custom_qfield_creds.qfield_cloud_user
        update_payload.external_project_password_encrypted = encrypt_value(
            custom_qfield_creds.qfield_cloud_password
        )
    await DbProject.update(db, project.id, update_payload)
    await db.commit()
    log.info("QFieldCloud project created: %s", qfield_url)

    return qfield_url


def _resolve_qfc_owner(client, custom_creds: QFieldCloud | None) -> str:
    """Choose the project owner.

    Custom credentials use their organisation or username; deployment
    credentials use QFIELDCLOUD_PROJECT_OWNER or the authenticated user.
    """
    client_username = getattr(client, "username", None)

    if custom_creds:
        candidates = [
            custom_creds.qfield_cloud_org,
            client_username,
            custom_creds.qfield_cloud_user,
        ]
    else:
        candidates = [settings.QFIELDCLOUD_PROJECT_OWNER, client_username]

    for candidate in candidates:
        if candidate:
            return candidate
    return settings.QFIELDCLOUD_USER or "admin"


def _qfield_base_url(custom_creds: QFieldCloud | None) -> str:
    """Build the external QFieldCloud base UI URL."""
    if custom_creds and custom_creds.qfield_cloud_url:
        base = custom_creds.qfield_cloud_url.rstrip("/")
        if base.endswith("/api/v1"):
            base = base[: -len("/api/v1")]
    elif settings.DEBUG:
        base = (
            f"http://qfield.{settings.FTM_DOMAIN}:{settings.FTM_DEV_PORT}"
            if settings.FTM_DEV_PORT
            else f"http://qfield.{settings.FTM_DOMAIN}"
        )
    else:
        base_url = settings.QFIELDCLOUD_URL or ""
        base = base_url.split("/api/v1")[0].rstrip("/")
        if not base and settings.FTM_DOMAIN:
            base = (
                f"http://qfield.{settings.FTM_DOMAIN}:{settings.FTM_DEV_PORT}"
                if settings.FTM_DEV_PORT
                else f"http://qfield.{settings.FTM_DOMAIN}"
            )
    return base


def _resolve_qfield_project_url(
    qfield_project: dict,
    custom_creds: QFieldCloud | None,
) -> str:
    """Resolve the best user-facing URL for a created QFieldCloud project."""
    base = _qfield_base_url(custom_creds)

    for key in ("public_url", "url", "absolute_url", "detail_url"):
        value = qfield_project.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = value.strip()
        if candidate.startswith(("http://", "https://")):
            return candidate.rstrip("/")
        if candidate.startswith("/"):
            return f"{base}{candidate}"

    return base


# Credential testing


async def qfc_credentials_test(qfc_creds: QFieldCloud):
    """Test QFieldCloud credentials by attempting to open a session.

    Returns HTTP 200 if credentials are valid, otherwise raises HTTPException.
    """
    try:
        creds = QFieldCloud(
            qfield_cloud_url=qfc_creds.qfield_cloud_url,
            qfield_cloud_user=qfc_creds.qfield_cloud_user,
            qfield_cloud_password=qfc_creds.qfield_cloud_password,
        )
        async with qfield_client(creds):
            pass
        return status.HTTP_200_OK
    except Exception as e:
        msg = f"QFieldCloud credential test failed: {e}"
        log.debug(msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("QFieldCloud credentials are invalid."),
        ) from e


# Export project data as GeoJSON


# Polling cadence for the QFieldCloud ``package`` job.  Packaging usually
# finishes in a few seconds for small projects; cap at 5 minutes for larger
# ones so the request doesn't hang forever if the QFC worker stalls.
_EXPORT_POLL_INTERVAL = 2.0
_EXPORT_POLL_TIMEOUT = 300.0
# Timeout for the GPKG→GeoJSON wrapper call (large gpkgs can take a while).
_GPKG_CONVERT_TIMEOUT = httpx.Timeout(600)
# Name of the QGIS layer that holds the survey submissions in every FTM
# project file (see src/qfield/field_project.py).
SURVEY_LAYER_NAME = "survey"


async def export_qfield_project_geojson(
    db: AsyncConnection,
    project: DbProject,
) -> dict:
    """Package the latest QFieldCloud data and convert its GeoPackages to GeoJSON.

    The QGIS wrapper reprojects to EPSG:4326. Features are merged into one
    FeatureCollection with a _layer property identifying each source layer.
    """
    if not project.external_project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("This project is not linked to a QFieldCloud project."),
        )

    qgis_url = (settings.QFIELDCLOUD_QGIS_URL or "").strip()
    if not qgis_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QFIELDCLOUD_QGIS_URL is not configured."),
        )

    custom_creds = _resolve_project_qfield_credentials(project)
    api_project_id = str(project.external_project_id)
    loop = get_running_loop()

    async with qfield_client(custom_creds) as client:
        await _wait_for_package_job(
            loop=loop, client=client, api_project_id=api_project_id
        )

        download_dir = tempfile.mkdtemp(prefix="ftm_qfc_export_")
        try:
            await loop.run_in_executor(
                None,
                partial(
                    client.package_download,
                    project_id=api_project_id,
                    local_dir=download_dir,
                    filter_glob="*.gpkg",
                    throw_on_error=True,
                ),
            )

            gpkg_paths = sorted(Path(download_dir).rglob("*.gpkg"))
            if not gpkg_paths:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_(
                        "No GeoPackage files were found in the QFieldCloud package."
                    ),
                )

            survey_features: list[dict] = []
            for gpkg_path in gpkg_paths:
                layers = await _convert_gpkg_via_wrapper(qgis_url, gpkg_path)
                # Export only submissions; omit task areas and form choice layers.
                survey_fc = layers.get(SURVEY_LAYER_NAME)
                if not survey_fc:
                    continue
                survey_features.extend(survey_fc.get("features", []))
        finally:
            shutil.rmtree(download_dir, ignore_errors=True)

    if not survey_features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_(
                "No survey data found in the QFieldCloud package. "
                "Mappers may not have submitted any responses yet."
            ),
        )

    return {"type": "FeatureCollection", "features": survey_features}


async def _wait_for_package_job(
    *,
    loop,
    client,
    api_project_id: str,
) -> None:
    """Trigger a ``package`` job on QFieldCloud and poll until it finishes."""
    job = await loop.run_in_executor(
        None,
        partial(client.job_trigger, api_project_id, JobTypes.PACKAGE, force=True),
    )
    job_id = job.get("id")
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QFieldCloud did not return a package job id."),
        )

    elapsed = 0.0
    last_status: Optional[str] = None
    while elapsed < _EXPORT_POLL_TIMEOUT:
        await asyncio.sleep(_EXPORT_POLL_INTERVAL)
        elapsed += _EXPORT_POLL_INTERVAL
        status_resp = await loop.run_in_executor(
            None, partial(client.job_status, job_id)
        )
        last_status = status_resp.get("status")
        if last_status == "finished":
            return
        if last_status == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_("QFieldCloud failed to package the project."),
            )

    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail=_(
            "Timed out waiting for QFieldCloud to package the project "
            "(last status: %(status)s)."
        )
        % {"status": last_status or "unknown"},
    )


async def _convert_gpkg_via_wrapper(qgis_url: str, gpkg_path: Path) -> dict:
    """POST a .gpkg to the QGIS wrapper's /export endpoint, return its layers dict."""
    gpkg_bytes = gpkg_path.read_bytes()
    headers = {"Content-Type": "application/octet-stream"}
    async with httpx.AsyncClient(timeout=_GPKG_CONVERT_TIMEOUT) as client:
        response = await client.post(
            f"{qgis_url.rstrip('/')}/export", content=gpkg_bytes, headers=headers
        )
    body = response.text
    if response.status_code != status.HTTP_200_OK:
        log.error("QGIS wrapper /export returned %s: %s", response.status_code, body)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("GeoPackage conversion failed: %(error)s") % {"error": body},
        )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("QGIS wrapper returned invalid JSON for /export."),
        ) from exc
    return payload.get("layers", {}) or {}
