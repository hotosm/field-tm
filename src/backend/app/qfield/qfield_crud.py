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
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from pathlib import Path
from random import getrandbits
from secrets import token_urlsafe
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import geojson
from aiohttp import ClientSession, ClientTimeout
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import AsyncConnection
from qfieldcloud_sdk.sdk import (
    FileTransferType,
    OrganizationMemberRole,
    ProjectCollaboratorRole,
)
from shapely.geometry import shape

from app.config import encrypt_value, settings
from app.db.models import DbProject
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud

log = logging.getLogger(__name__)

# Shared Docker volume mounted in both backend and qfield-qgis containers
SHARED_VOLUME_PATH = "/opt/qfield"

# Timeout for QGIS wrapper HTTP calls (project generation can be slow)
QGIS_REQUEST_TIMEOUT = ClientTimeout(total=300)  # 5 minutes


@dataclass(slots=True)
class QFieldProjectResult:
    """Details returned after QField project creation."""

    qfield_url: str
    manager_username: Optional[str]
    manager_password: Optional[str]
    mapper_username: Optional[str]
    mapper_password: Optional[str]


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


def _can_manage_qfc_users_locally(custom_creds: QFieldCloud | None) -> bool:
    """Whether user provisioning can use the local qfield-user-mgmt sidecar."""
    if not custom_creds or not custom_creds.qfield_cloud_url:
        return True

    host = (urlparse(custom_creds.qfield_cloud_url).hostname or "").lower()
    return host in {
        "",
        "localhost",
        "127.0.0.1",
        "qfield-app",
        "qfield.field.localhost",
    }


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
        # Use project_name if available; slug can be None for freshly-created
        # projects that haven't been named yet.
        qgis_project_title = project.project_name or f"project-{project.id}"
        await _call_qgis_wrapper(
            job_dir=str(job_dir),
            title=qgis_project_title,
            language=form_language or "",
            extent=bbox_str,
            open_in_edit_mode=open_in_edit_mode,
        )

        # Locate the generated .qgz — the converter may sanitise the title
        # when building the filename so we scan rather than predict.
        final_dir = job_dir / "final"
        qgz_files = list(final_dir.glob("*.qgz"))
        if not qgz_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="QGIS wrapper completed but no .qgz file found in output.",
            )
        final_project_file = qgz_files[0]
        log.info("QGIS project generated: %s", final_project_file)

        # ── Step 2: Upload to QFieldCloud ──────────────────────────────
        qfc_project_name = f"FieldTM-{qgis_project_title}-{getrandbits(32)}"
        result = await _upload_to_qfieldcloud(
            project=project,
            qfc_project_name=qfc_project_name,
            final_project_dir=str(final_project_file.parent),
            custom_qfield_creds=custom_qfield_creds,
            db=db,
        )

        return result

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
    open_in_edit_mode: bool,
) -> None:
    """POST to the QGIS wrapper HTTP service and raise on failure."""
    qgis_url = "http://qfield-qgis:8080"
    payload = {
        "project_dir": job_dir,
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

    log.debug("QGIS wrapper call succeeded")


async def _create_qfc_user(
    username: str,
    password: str,
) -> bool:
    """Create a QFieldCloud user via the qfield-user-mgmt sidecar service.

    The sidecar runs inside the qfield-app container (same Django environment)
    and creates users directly via the ORM.  Returns True on success or if the
    user already exists, False on failure.
    """
    url = "http://qfield-user-mgmt:8001/create-user"
    payload = {"username": username, "password": password}

    async with ClientSession() as session:
        try:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    body = await resp.json()
                    log.info("QFC user '%s': %s", username, body.get("status", "ok"))
                    return True
                body = await resp.text()
                log.warning(
                    "qfield-user-mgmt returned %s for '%s': %s",
                    resp.status,
                    username,
                    body,
                )
        except Exception as exc:
            log.warning("qfield-user-mgmt call failed for '%s': %s", username, exc)

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
        api_project_owner = qfield_project.get("owner") or qfc_owner

        try:
            # Upload files (sync SDK call → run in executor)
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

        manager_username = manager_password = None
        mapper_username = mapper_password = None
        if _can_manage_qfc_users_locally(custom_qfield_creds):
            # Create manager user and add to project
            manager_username, manager_password = await _provision_project_user(
                loop=loop,
                client=client,
                api_project_id=api_project_id,
                api_project_owner=api_project_owner,
                username=f"ftm_manager_{project.id}",
                role=ProjectCollaboratorRole.MANAGER,
                role_label="manager",
            )

            # Create mapper service account and add to project
            mapper_username, mapper_password = await _provision_project_user(
                loop=loop,
                client=client,
                api_project_id=api_project_id,
                api_project_owner=api_project_owner,
                username=f"ftm_mapper_{project.id}",
                role=ProjectCollaboratorRole.EDITOR,
                role_label="mapper",
            )
        else:
            log.info(
                "Skipping QField service-account provisioning for remote instance %s",
                custom_qfield_creds.qfield_cloud_url,
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
    created = await _create_qfc_user(username, password)
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
