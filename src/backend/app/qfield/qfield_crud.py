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

import json
import logging
import shutil
from asyncio import get_running_loop
from functools import partial
from io import BytesIO
from pathlib import Path
from random import getrandbits
from typing import Optional
from uuid import uuid4

import geojson
from aiohttp import ClientSession, ClientTimeout
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import AsyncConnection
from qfieldcloud_sdk.sdk import FileTransferType
from shapely.geometry import shape

from app.config import settings
from app.db.models import DbProject
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud

log = logging.getLogger(__name__)

# Shared Docker volume mounted in both backend and qfield-qgis containers
SHARED_VOLUME_PATH = "/opt/qfield"

# Timeout for QGIS wrapper HTTP calls (project generation can be slow)
QGIS_REQUEST_TIMEOUT = ClientTimeout(total=300)  # 5 minutes


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _outline_to_bbox_str(outline: dict) -> str:
    """Compute a comma-separated bbox string (xmin,ymin,xmax,ymax) from outline.

    The outline may be a raw GeoJSON geometry, a Feature, or a FeatureCollection.
    """
    geometry = _extract_geometry(outline)
    if not geometry:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project outline is missing or has no geometry.",
        )
    geom = shape(geometry)
    minx, miny, maxx, maxy = geom.bounds
    return f"{minx},{miny},{maxx},{maxy}"


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
    # Assume it is already a geometry object (has "coordinates")
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


# ---------------------------------------------------------------------------
# Data preparation helpers
# ---------------------------------------------------------------------------


def clean_tags_for_qgis(
    geojson_data: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Clean tags field in GeoJSON to be compatible with QGIS.

    QGIS has issues with JSON string tags like '{"building": "yes"}', so we
    convert them to a flat ``key=value;…`` format.
    """
    if not geojson_data or "features" not in geojson_data:
        return geojson_data

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        properties["tags"] = _qgis_safe_tags_value(properties.get("tags"))
        feature["properties"] = properties

    return geojson_data


def _qgis_safe_tags_value(tags) -> str:
    """Normalize the ``tags`` property to a QGIS-safe string."""
    if not tags:
        return ""
    if not (isinstance(tags, str) and tags.startswith("{") and tags.endswith("}")):
        return str(tags)

    try:
        tags_dict = json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        return str(tags)

    if not isinstance(tags_dict, dict):
        return str(tags)
    return ";".join(f"{k}={v}" for k, v in tags_dict.items())


def _build_tasks_geojson(project: DbProject) -> dict:
    """Build a tasks FeatureCollection from project data.

    If ``task_areas_geojson`` contains features, use them (and ensure each has
    a ``task_id``).  If empty/absent, create a single task from the outline.
    """
    task_areas = project.task_areas_geojson
    if task_areas and isinstance(task_areas, dict) and task_areas.get("features"):
        for idx, feature in enumerate(task_areas["features"], start=1):
            props = feature.setdefault("properties", {})
            if "task_id" not in props:
                props["task_id"] = idx
        return task_areas

    # Fallback: single task from outline
    geometry = _extract_geometry(project.outline)
    if not geometry:
        return {"type": "FeatureCollection", "features": []}

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {"task_id": 1},
            }
        ],
    }


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


# ---------------------------------------------------------------------------
# Core: create QField project
# ---------------------------------------------------------------------------


async def create_qfield_project(
    db: AsyncConnection,
    project: DbProject,
    custom_qfield_creds: QFieldCloud | None = None,
) -> str:
    """Create QField project in QFieldCloud via the QGIS wrapper service.

    Steps:
        1. Prepare local files (XLSForm, features, tasks).
        2. Call the QGIS wrapper HTTP service to generate a ``.qgz`` project.
        3. Create a project on QFieldCloud and upload the generated files.

    Returns:
        URL to the QFieldCloud project dashboard.

    Raises:
        HTTPException: On validation or processing errors.
    """
    # ── Validate prerequisites ──────────────────────────────────────────
    if not project.outline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project outline is required for QField project creation.",
        )
    if not project.xlsform_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="XLSForm is required for QField project creation.",
        )

    # ── Compute derived values ──────────────────────────────────────────
    bbox_str = _outline_to_bbox_str(project.outline)
    geom_type = _dominant_geom_type(project.data_extract_geojson)

    # ── Modify XLSForm for QField ──────────────────────────────────────
    form_language, final_form = await modify_form_for_qfield(
        BytesIO(project.xlsform_content),
        geom_layer_type=geom_type,
    )
    xlsform_bytes = final_form.getvalue()
    if not xlsform_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to modify XLSForm for QField.",
        )

    # ── Prepare local data ──────────────────────────────────────────────
    features_geojson = _build_features_geojson(project)
    features_geojson = clean_tags_for_qgis(features_geojson)

    tasks_geojson = _build_tasks_geojson(project)
    tasks_geojson = clean_tags_for_qgis(tasks_geojson)

    # ── Write files to shared volume ────────────────────────────────────
    qgis_job_id = str(uuid4())
    job_dir = Path(SHARED_VOLUME_PATH) / qgis_job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        _write_job_files(job_dir, xlsform_bytes, features_geojson, tasks_geojson)

        # Persist the QField-modified XLSForm back to DB
        log.debug("Saving QField XLSForm to DB for project %s", project.id)
        await DbProject.update(
            db,
            project.id,
            ProjectUpdate(xlsform_content=xlsform_bytes),
        )
        await db.commit()

        # ── Step 1: Generate QGIS project via wrapper ──────────────────
        qgis_project_name = project.slug
        await _call_qgis_wrapper(
            job_dir=str(job_dir),
            title=qgis_project_name,
            language=form_language or "",
            extent=bbox_str,
        )

        # Verify output was created
        final_project_file = job_dir / "final" / f"{qgis_project_name}.qgz"
        if not final_project_file.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"QGIS wrapper completed but output file missing: "
                    f"{final_project_file.name}"
                ),
            )
        log.info("QGIS project generated: %s", final_project_file)

        # ── Step 2: Upload to QFieldCloud ──────────────────────────────
        qfc_project_name = f"FieldTM-{qgis_project_name}-{getrandbits(32)}"
        qfield_url = await _upload_to_qfieldcloud(
            project=project,
            qfc_project_name=qfc_project_name,
            final_project_dir=str(final_project_file.parent),
            custom_qfield_creds=custom_qfield_creds,
            db=db,
        )

        return qfield_url

    finally:
        # Always clean up the temp job directory
        shutil.rmtree(job_dir, ignore_errors=True)


def _write_job_files(
    job_dir: Path,
    xlsform_bytes: bytes,
    features_geojson: dict,
    tasks_geojson: dict,
) -> None:
    """Write the input files the QGIS wrapper expects."""
    (job_dir / "xlsform.xlsx").write_bytes(xlsform_bytes)

    with open(job_dir / "features.geojson", "w") as f:
        json.dump(features_geojson, f)

    with open(job_dir / "tasks.geojson", "w") as f:
        json.dump(tasks_geojson, f)


async def _call_qgis_wrapper(
    *,
    job_dir: str,
    title: str,
    language: str,
    extent: str,
) -> None:
    """POST to the QGIS wrapper HTTP service and raise on failure."""
    qgis_url = "http://qfield-qgis:8080"
    payload = {
        "project_dir": job_dir,
        "title": title,
        "language": language,
        "extent": extent,
    }
    log.info("Calling QGIS wrapper at %s for project '%s'", qgis_url, title)

    async with (
        ClientSession(timeout=QGIS_REQUEST_TIMEOUT) as session,
        session.post(f"{qgis_url}/", json=payload) as response,
    ):
        body = await response.text()
        if response.status != 200:
            log.error("QGIS wrapper returned %s: %s", response.status, body)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QGIS project generation failed: {body}",
            )
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QGIS wrapper returned invalid JSON.",
            )
        if result.get("status") != "success":
            msg = result.get("message", "Unknown error")
            log.error("QGIS wrapper reported failure: %s", msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QGIS project generation failed: {msg}",
            )

    log.debug("QGIS wrapper call succeeded")


async def _upload_to_qfieldcloud(
    *,
    project: DbProject,
    qfc_project_name: str,
    final_project_dir: str,
    custom_qfield_creds: QFieldCloud | None,
    db: AsyncConnection,
) -> str:
    """Create a QFieldCloud project and upload files.

    Returns the project dashboard URL.
    """
    loop = get_running_loop()

    log.info("Creating QFieldCloud project: %s", qfc_project_name)
    async with qfield_client(custom_qfield_creds) as client:
        # Determine the owner (the authenticated user, or a configured org)
        qfc_owner = _resolve_qfc_owner(client, custom_qfield_creds)

        # Create project (sync SDK call → run in executor)
        qfield_project = await loop.run_in_executor(
            None,
            partial(
                client.create_project,
                qfc_project_name,
                owner=qfc_owner,
                description="Created by the Field Tasking Manager",
                is_public=True,
            ),
        )
        log.debug("QFieldCloud project created: %s", qfield_project)

        api_project_id = qfield_project.get("id")
        api_project_owner = qfield_project.get("owner")
        api_project_name = qfield_project.get("name")

        try:
            # Upload files (sync SDK call → run in executor)
            log.info("Uploading files to QFieldCloud project %s", api_project_name)
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
                detail=f"Failed to upload files to QFieldCloud: {e}",
            ) from e

    # Build the QFieldCloud project URL
    qfield_url = _build_qfield_url(
        api_project_owner, api_project_name, custom_qfield_creds
    )

    # Store QField project details in the DB
    await DbProject.update(
        db,
        project.id,
        ProjectUpdate(
            external_project_id=api_project_id,
            external_project_instance_url=qfield_url,
        ),
    )
    await db.commit()
    log.info("QFieldCloud project created: %s", qfield_url)

    return qfield_url


def _resolve_qfc_owner(client, custom_creds: QFieldCloud | None) -> str:
    """Resolve the QFieldCloud project owner.

    Uses the authenticated username from the SDK client.  Falls back to the
    configured default (typically the HOTOSM org).
    """
    # The SDK client stores the logged-in username after authentication
    username = getattr(client, "username", None)
    if username:
        return username
    # Fallback to configured username
    if custom_creds and custom_creds.qfield_cloud_user:
        return custom_creds.qfield_cloud_user
    return settings.QFIELDCLOUD_USER or "admin"


def _build_qfield_url(
    owner: str,
    project_name: str,
    custom_creds: QFieldCloud | None,
) -> str:
    """Build the external QFieldCloud project dashboard URL."""
    if custom_creds and custom_creds.qfield_cloud_url:
        # Strip the /api/v1/ suffix and trailing slashes
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
    return f"{base}/a/{owner}/{project_name}"


# ---------------------------------------------------------------------------
# Credential testing
# ---------------------------------------------------------------------------


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
            detail="QFieldCloud credentials are invalid.",
        ) from e


# ---------------------------------------------------------------------------
# Delete QFieldCloud project
# ---------------------------------------------------------------------------


async def delete_qfield_project(db: AsyncConnection, project_id: int) -> str:
    """Delete a project from QFieldCloud using the stored ``external_project_id``."""
    project = await DbProject.one(db, project_id)

    qfield_project_id = project.external_project_id
    if not qfield_project_id:
        return f"No QField project id set for project ID {project_id}"

    loop = get_running_loop()
    async with qfield_client() as client:
        try:
            await loop.run_in_executor(
                None,
                partial(client.delete_project, qfield_project_id),
            )
        except Exception:
            return (
                f"QField project {qfield_project_id} not found "
                f"(may already be deleted)."
            )

    return f"Project {project_id} deleted from QFieldCloud."
