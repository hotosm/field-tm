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

import base64
import json
import logging
import re
import shutil
import tempfile
from asyncio import get_running_loop
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from pathlib import Path
from random import getrandbits
from secrets import token_urlsafe
from typing import Optional
from urllib.parse import urlsplit
from uuid import uuid4

from aiohttp import ClientSession, ClientTimeout
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import AsyncConnection
from qfieldcloud_sdk.interfaces import QfcRequestException
from qfieldcloud_sdk.sdk import (
    FileTransferType,
    OrganizationMemberRole,
    ProjectCollaboratorRole,
)

from app.config import encrypt_value, settings
from app.db.models import DbProject
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud

log = logging.getLogger(__name__)

# Timeout for QGIS wrapper HTTP calls (project generation can be slow)
QGIS_REQUEST_TIMEOUT = ClientTimeout(total=300)  # 5 minutes
QFC_NAME_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(slots=True)
class QFieldProjectResult:
    """Details returned after QField project creation."""

    qfield_url: str
    manager_username: Optional[str]
    manager_password: Optional[str]
    mapper_username: Optional[str]
    mapper_password: Optional[str]


def strip_qfc_api_suffix(url: str) -> str:
    """Return the canonical QFieldCloud origin without API path segments."""
    value = (url or "").strip()
    if not value:
        return ""

    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    return value.split("/api/v1")[0].rstrip("/")


def normalise_qfc_url(url: str) -> str:
    """Return the canonical QFieldCloud API root with trailing slash."""
    base = strip_qfc_api_suffix(url)
    if not base:
        return ""
    return f"{base}/api/v1/"


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _flatten_geom_coords(geom: dict) -> list:
    """Flatten all coordinates in a GeoJSON geometry to a list of [lon, lat] pairs."""
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])
    if geom_type == "Point":
        return [coords]
    if geom_type in ("LineString", "MultiPoint"):
        return list(coords)
    if geom_type in ("Polygon", "MultiLineString"):
        return [c for ring in coords for c in ring]
    if geom_type == "MultiPolygon":
        return [c for poly in coords for ring in poly for c in ring]
    if geom_type == "GeometryCollection":
        result = []
        for sub_geom in geom.get("geometries", []):
            result.extend(_flatten_geom_coords(sub_geom))
        return result
    return []


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
    coords = _flatten_geom_coords(geometry)
    if not coords:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project outline geometry has no coordinates.",
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


def _sanitize_qfc_project_name(name: str) -> str:
    """Normalize a QFieldCloud project name to API-accepted characters."""
    cleaned = QFC_NAME_SANITIZE_PATTERN.sub("-", (name or "").strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-.")
    return cleaned or f"FieldTM-project-{getrandbits(32)}"


def _build_qfc_service_account_email(username: str) -> str:
    """Build a non-empty email for QFieldCloud service-account provisioning."""
    local_part = re.sub(r"[^A-Za-z0-9._+-]+", "-", (username or "").strip()).strip(".-")
    if not local_part:
        local_part = "ftm-qfield-user"

    domain = (settings.FTM_DOMAIN or "field.localhost").strip().lower()
    domain = re.sub(r"[^a-z0-9.-]+", "-", domain).strip(".-")
    if not domain or "." not in domain:
        domain = "noreply.local"

    return f"{local_part}@{domain}"


# ---------------------------------------------------------------------------
# Data preparation helpers
# ---------------------------------------------------------------------------


def clean_tags_for_qgis(
    geojson_data: dict,
) -> dict:
    """Clean GeoJSON properties to be compatible with QGIS.

    QGIS cannot write nested JSON/list property values back out to GeoJSON.
    Flatten ``tags`` to ``key=value;...`` and stringify any other non-scalar
    property values before the wrapper touches the file.
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


def _qgis_safe_tags_value(tags) -> str:
    """Normalize the ``tags`` property to a QGIS-safe string."""
    result = ""
    if not tags:
        return result
    if isinstance(tags, dict):
        result = ";".join(f"{k}={v}" for k, v in tags.items())
    elif isinstance(tags, list):
        result = json.dumps(tags, ensure_ascii=False, separators=(",", ":"))
    elif not (isinstance(tags, str) and tags.startswith("{") and tags.endswith("}")):
        result = str(tags)
    else:
        try:
            tags_dict = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            result = str(tags)
        else:
            if isinstance(tags_dict, dict):
                result = ";".join(f"{k}={v}" for k, v in tags_dict.items())
            else:
                result = str(tags)
    return result


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


# ---------------------------------------------------------------------------
# Core: create QField project
# ---------------------------------------------------------------------------


async def create_qfield_project(
    db: AsyncConnection,
    project: DbProject,
    custom_qfield_creds: QFieldCloud | None = None,
) -> QFieldProjectResult:
    """Create QField project in QFieldCloud via the QGIS wrapper service.

    Steps:
        1. Prepare local files (XLSForm, features, tasks).
        2. Call the QGIS wrapper HTTP service to generate a ``.qgz`` project.
        3. Create a project on QFieldCloud and upload the generated files.
        4. Provision manager and mapper service accounts.

    Returns:
        QFieldProjectResult with URL and credentials.

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
    open_in_edit_mode = _should_open_in_edit_mode(project.data_extract_geojson)
    features_geojson = _build_features_geojson(project)
    features_geojson = _strip_feature_properties_for_qfield(features_geojson)
    features_geojson = clean_tags_for_qgis(features_geojson)

    tasks_geojson = _build_tasks_geojson(project)
    tasks_geojson = clean_tags_for_qgis(tasks_geojson)

    # Persist the QField-modified XLSForm back to DB
    log.debug("Saving QField XLSForm to DB for project %s", project.id)
    await DbProject.update(
        db,
        project.id,
        ProjectUpdate(xlsform_content=xlsform_bytes),
    )
    await db.commit()

    # ── Step 1: Write job inputs to DB and call QGIS wrapper ─────────
    qgis_project_title = project.project_name or f"project-{project.id}"
    job_id = uuid4()
    await _insert_qgis_job(db, job_id, xlsform_bytes, features_geojson, tasks_geojson)
    await db.commit()

    try:
        await _call_qgis_wrapper(
            job_id=str(job_id),
            title=qgis_project_title,
            language=form_language or "",
            extent=bbox_str,
            open_in_edit_mode=open_in_edit_mode,
        )

        # ── Step 2: Read outputs from DB, upload to QFieldCloud ──────
        output_files = await _read_qgis_job_outputs(db, job_id)
        if not output_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QGIS wrapper completed but wrote no output files.",
            )

        tmp_dir = tempfile.mkdtemp(prefix="qfield_upload_")
        try:
            for filename, b64_content in output_files.items():
                (Path(tmp_dir) / filename).write_bytes(base64.b64decode(b64_content))

            qgz_files = list(Path(tmp_dir).glob("*.qgz"))
            if not qgz_files:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="QGIS wrapper completed but no .qgz file in output.",
                )
            log.info("QGIS project generated: %s", qgz_files[0].name)

            raw_qfc_project_name = f"FieldTM-{qgis_project_title}-{getrandbits(32)}"
            qfc_project_name = _sanitize_qfc_project_name(raw_qfc_project_name)
            result = await _upload_to_qfieldcloud(
                project=project,
                qfc_project_name=qfc_project_name,
                final_project_dir=tmp_dir,
                custom_qfield_creds=custom_qfield_creds,
                db=db,
            )
            return result
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    finally:
        await _delete_qgis_job(db, job_id)
        await db.commit()


async def _insert_qgis_job(
    db: AsyncConnection,
    job_id,
    xlsform: bytes,
    features: dict,
    tasks: dict,
) -> None:
    """Insert a new QGIS job with input files into the database."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO qgis_jobs (job_id, xlsform, features, tasks)
            VALUES (%(job_id)s, %(xlsform)s, %(features)s, %(tasks)s)
            """,
            {
                "job_id": job_id,
                "xlsform": xlsform,
                "features": json.dumps(features),
                "tasks": json.dumps(tasks),
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


async def _call_qgis_wrapper(
    *,
    job_id: str,
    title: str,
    language: str,
    extent: str,
    open_in_edit_mode: bool,
) -> None:
    """POST to the QGIS wrapper to trigger project generation.

    The wrapper reads input files from and writes output files to the
    ``qgis_jobs`` table in the shared database.  Only the job_id and
    processing parameters are sent via HTTP.
    """
    qgis_url = settings.QFIELDCLOUD_QGIS_URL
    payload = {
        "job_id": job_id,
        "title": title,
        "language": language,
        "extent": extent,
        "open_in_edit_mode": open_in_edit_mode,
    }
    log.info("Calling QGIS wrapper at %s for project '%s'", qgis_url, title)

    async with (
        ClientSession(timeout=QGIS_REQUEST_TIMEOUT) as session,
        session.post(f"{qgis_url}/", json=payload) as response,
    ):
        body = await response.text()
        if response.status != status.HTTP_200_OK:
            log.error("QGIS wrapper returned %s: %s", response.status, body)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QGIS project generation failed: {body}",
            )
        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QGIS wrapper returned invalid JSON.",
            ) from exc
        if result.get("status") != "success":
            msg = result.get("message", "Unknown error")
            log.error("QGIS wrapper reported failure: %s", msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"QGIS project generation failed: {msg}",
            )

    log.debug("QGIS wrapper call succeeded for job %s", job_id)


async def _create_qfc_user(username: str, password: str, client) -> bool:
    """Create a QFieldCloud user via the SDK (POST /api/v1/users/).

    Returns True when the user is created (201) or already exists (409).
    Returns False and logs a warning when the endpoint is unavailable (404/405)
    or the service account lacks staff permission (403).  Both cases are soft
    failures: caller skips collaborator provisioning but continues.
    """
    loop = get_running_loop()
    email = _build_qfc_service_account_email(username)
    try:
        await loop.run_in_executor(
            None,
            partial(client.create_user, username, password, email, exist_ok=True),
        )
        log.info("QFC user '%s' created or already exists", username)
        return True
    except QfcRequestException as exc:
        status_code = exc.response.status_code
        if status_code in (
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ):
            log.warning(
                "QFC user creation API not available "
                "(upgrade QFieldCloud to enable automated account provisioning)"
            )
            return False
        if status_code == status.HTTP_403_FORBIDDEN:
            log.warning(
                "QFC service account lacks staff permission for user creation; "
                "ensure the account has is_staff=True in QFieldCloud"
            )
            return False
        log.warning(
            "Unexpected QFC user creation response %s for '%s': %s",
            status_code,
            username,
            exc,
        )
        return False
    except Exception as exc:
        log.warning("QFC user creation call failed for '%s': %s", username, exc)
        return False


async def _upload_to_qfieldcloud(
    *,
    project: DbProject,
    qfc_project_name: str,
    final_project_dir: str,
    custom_qfield_creds: QFieldCloud | None,
    db: AsyncConnection,
) -> QFieldProjectResult:
    """Create a QFieldCloud project, upload files, and provision manager/mapper users.

    Returns a QFieldProjectResult with the project URL and credentials.
    """
    loop = get_running_loop()

    log.info("Creating QFieldCloud project: %s", qfc_project_name)
    async with qfield_client(custom_qfield_creds) as client:
        # Determine the owner (the authenticated user, or a configured org)
        qfc_owner = _resolve_qfc_owner(client, custom_qfield_creds)

        # Create project (sync SDK call --> run in executor)
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
        api_project_owner = qfield_project.get("owner") or qfc_owner

        try:
            # Upload files (sync SDK call --> run in executor)
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

        # Provision per-project service accounts via the QFC admin API.
        # _create_qfc_user returns False (and logs a warning) when the API is
        # unavailable or the service account lacks staff permission, so these
        # calls degrade gracefully on older QFieldCloud instances.
        manager_username, manager_password = await _provision_project_user(
            loop=loop,
            client=client,
            api_project_id=api_project_id,
            api_project_owner=api_project_owner,
            username=f"ftm_manager_{project.id}",
            role=ProjectCollaboratorRole.MANAGER,
            role_label="manager",
        )
        mapper_username, mapper_password = await _provision_project_user(
            loop=loop,
            client=client,
            api_project_id=api_project_id,
            api_project_owner=api_project_owner,
            username=f"ftm_mapper_{project.id}",
            role=ProjectCollaboratorRole.EDITOR,
            role_label="mapper",
        )
        if not manager_username:
            log.info(
                "QField service-account provisioning skipped for %s",
                (
                    custom_qfield_creds.qfield_cloud_url
                    if custom_qfield_creds
                    else "default instance"
                ),
            )

    # Prefer a canonical URL returned by QFieldCloud, otherwise fall back to
    # the instance root instead of guessing an internal route.
    qfield_url = _resolve_qfield_project_url(qfield_project, custom_qfield_creds)

    # Store QField project details and mapper credentials in the DB
    update_payload = ProjectUpdate(
        external_project_id=api_project_id,
        external_project_instance_url=qfield_url,
    )
    if mapper_username and mapper_password:
        update_payload.external_project_username = mapper_username
        update_payload.external_project_password_encrypted = encrypt_value(
            mapper_password
        )
    await DbProject.update(db, project.id, update_payload)
    await db.commit()
    log.info("QFieldCloud project created: %s", qfield_url)

    return QFieldProjectResult(
        qfield_url=qfield_url,
        manager_username=manager_username,
        manager_password=manager_password,
        mapper_username=mapper_username,
        mapper_password=mapper_password,
    )


async def _provision_project_user(
    *,
    loop,
    client,
    api_project_id: str,
    api_project_owner: str,
    username: str,
    role: ProjectCollaboratorRole,
    role_label: str,
) -> tuple[Optional[str], Optional[str]]:
    """Create a QFieldCloud user and add them to the project.

    Returns (username, password) on success, (None, None) if creation failed.
    """
    password = token_urlsafe(16)
    created = await _create_qfc_user(username, password, client)
    if not created:
        log.warning(
            "Could not create QFC %s user '%s'; skipping collaborator assignment.",
            role_label,
            username,
        )
        return None, None

    try:
        if _is_org_owned_project(api_project_owner, getattr(client, "username", None)):
            await _ensure_org_membership(
                loop=loop,
                client=client,
                organization=api_project_owner,
                username=username,
            )

        await loop.run_in_executor(
            None,
            partial(
                client.add_project_collaborator,
                api_project_id,
                username,
                role,
            ),
        )
        log.info(
            "Added QFC %s '%s' to project %s", role_label, username, api_project_id
        )
    except Exception as exc:
        log.warning(
            "Could not add '%s' as %s to project %s: %s",
            username,
            role_label,
            api_project_id,
            exc,
        )
        return None, None

    if not await _project_has_collaborator(
        loop=loop,
        client=client,
        api_project_id=api_project_id,
        username=username,
    ):
        log.warning(
            "QField project %s does not list '%s' as a collaborator after add; "
            "withholding %s credentials.",
            api_project_id,
            username,
            role_label,
        )
        return None, None

    return username, password


def _is_org_owned_project(project_owner: str, client_username: str | None) -> bool:
    """Whether the project owner is an organization rather than the auth user."""
    return bool(project_owner and client_username and project_owner != client_username)


async def _ensure_org_membership(
    *,
    loop,
    client,
    organization: str,
    username: str,
) -> None:
    """Ensure a user is a member of the owning organization."""
    members = await loop.run_in_executor(
        None,
        partial(client.get_organization_members, organization),
    )
    if any(member.get("member") == username for member in members):
        return

    await loop.run_in_executor(
        None,
        partial(
            client.add_organization_member,
            organization,
            username,
            OrganizationMemberRole.MEMBER,
            False,
        ),
    )
    log.info("Added QFC user '%s' to organization '%s'", username, organization)


async def _project_has_collaborator(
    *,
    loop,
    client,
    api_project_id: str,
    username: str,
) -> bool:
    """Confirm the project collaborator was persisted by QFieldCloud."""
    collaborators = await loop.run_in_executor(
        None,
        partial(client.get_project_collaborators, api_project_id),
    )
    return any(collab.get("collaborator") == username for collab in collaborators)


def _resolve_qfc_owner(client, custom_creds: QFieldCloud | None) -> str:
    """Resolve the QFieldCloud project owner.

    Prefers the explicit QFIELDCLOUD_PROJECT_OWNER setting (which may be an
    organisation name rather than the authenticated user).  Falls back to the
    authenticated username, then the configured login user.
    """
    # Explicit owner override takes highest priority (e.g. an org like "hotosm")
    if settings.QFIELDCLOUD_PROJECT_OWNER:
        return settings.QFIELDCLOUD_PROJECT_OWNER
    # The SDK client stores the logged-in username after authentication
    username = getattr(client, "username", None)
    if username:
        return username
    # Fallback to configured login username
    if custom_creds and custom_creds.qfield_cloud_user:
        return custom_creds.qfield_cloud_user
    return settings.QFIELDCLOUD_USER or "admin"


def _qfield_base_url(custom_creds: QFieldCloud | None) -> str:
    """Build the external QFieldCloud base UI URL."""
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


# ---------------------------------------------------------------------------
# Collaborator management
# ---------------------------------------------------------------------------


async def add_qfc_project_collaborator(
    client,
    qfc_project_id: str,
    username: str,
    role: ProjectCollaboratorRole,
) -> None:
    """Add a user as a collaborator to a QFieldCloud project.

    Handles org-owned projects by ensuring org membership first.
    Raises HTTPException on failure.
    """
    loop = get_running_loop()

    try:
        project = await loop.run_in_executor(
            None, partial(client.get_project, qfc_project_id)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QFieldCloud project '{qfc_project_id}' not found.",
        ) from exc

    owner = project.get("owner", "")
    client_username = getattr(client, "username", None)

    if _is_org_owned_project(owner, client_username):
        try:
            await _ensure_org_membership(
                loop=loop,
                client=client,
                organization=owner,
                username=username,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Project belongs to organization '{owner}'. "
                    f"Could not add '{username}' to the organization: {exc}"
                ),
            ) from exc

    try:
        await loop.run_in_executor(
            None,
            partial(client.add_project_collaborator, qfc_project_id, username, role),
        )
    except QfcRequestException as exc:
        status_code = exc.response.status_code
        if status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' does not exist on QFieldCloud.",
            ) from exc
        if status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User '{username}' is already a collaborator on this project.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to add collaborator: {exc}",
        ) from exc

    log.info(
        "Added QFC user '%s' to project '%s' with role '%s'",
        username,
        qfc_project_id,
        role,
    )


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
