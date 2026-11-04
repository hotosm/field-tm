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
"""Shared project operations for HTMX and backend workflows."""

import logging
from asyncio import get_running_loop
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from typing import Optional

from anyio import to_thread
from area_splitter import SplittingAlgorithm
from area_splitter.splitter import split_by_sql
from geojson_aoi import parse_aoi
from osm_fieldwork.enums import NewPointCapture
from osm_fieldwork.update_xlsform import get_processed_form_options
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection
from qfieldcloud_sdk.interfaces import QfcRequestException

from app.central import central_crud, central_deps
from app.config import settings
from app.db.enums import FieldMappingApp, ProjectStatus
from app.db.languages_and_countries import countries
from app.db.models import DbProject
from app.errors import (
    ConflictError,
    DownstreamDeleteError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from app.helpers.geometry_utils import (
    AREA_LIMIT_KM2,
    check_crs,
    geojson_area_km2,
    merge_featcol_polygons_sync,
    polygon_to_centroid,
    stamp_missing_task_ids,
)
from app.i18n import _
from app.projects import project_deps, project_schemas
from app.projects.task_sync import tasks_geometry_hash
from app.qfield.qfield_crud import create_qfield_project
from app.qfield.qfield_deps import qfield_client

log = logging.getLogger(__name__)

HTTP_STATUS_OK_MIN = 200
HTTP_STATUS_OK_MAX_EXCLUSIVE = 300
HTTP_STATUS_NOT_FOUND = 404
SIMPLE_PROJECT_TAGS = ["osm", "buildings", "simple"]


def _simple_project_description() -> str:
    """Return the translated description for simple workflow projects."""
    return _(
        "This project was created with a simplified workflow in FieldTM and is made "
        "to collect building data to enhance OpenStreetMap."
    )


def _simple_project_fallback_city() -> str:
    """Return the translated fallback location label for simple workflow projects."""
    return _("Unnamed Area")


def _format_simple_fallback_city(centroid) -> str:
    """Build a deterministic fallback city-like label from centroid coordinates."""
    if centroid is None:
        return _simple_project_fallback_city()

    lon = getattr(centroid, "x", None)
    lat = getattr(centroid, "y", None)
    if lon is None or lat is None:
        return _simple_project_fallback_city()

    return _("Area {latitude:.4f}_{longitude:.4f}").format(latitude=lat, longitude=lon)


@dataclass(slots=True)
class QFieldFinalizeResult:
    """Details returned after QField finalization."""

    qfield_url: str


@dataclass(slots=True)
class DeleteProjectResult:
    """Result from deleting project in downstream app + Field-TM."""

    downstream_status: str


def _validate_project_stub_inputs(
    project_name: str,
    field_mapping_app: str,
    description: str,
    outline: dict,
) -> None:
    """Validate the required inputs for stub project creation."""
    if not project_name:
        raise ValidationError("Project name is required.")
    if not description or not description.strip():
        raise ValidationError("Description is required.")
    if not field_mapping_app:
        raise ValidationError("Field Mapping App is required.")
    if not outline:
        raise ValidationError(
            "You must draw or upload an Area of Interest (AOI) on the map."
        )


async def _ensure_project_name_available(
    db: AsyncConnection,
    project_name: str,
) -> None:
    """Reject duplicate project names."""
    exists = await project_deps.project_name_does_not_already_exist(db, project_name)
    if exists:
        raise ConflictError(
            f"Project with name '{project_name}' already exists. "
            "Please choose a different name."
        )


async def _delete_odk_downstream_project(project: DbProject) -> str:
    """Delete an ODK project, tolerating already-deleted remote state."""
    if not project.external_project_id:
        return "No ODK project id configured; skipped downstream deletion."

    try:
        async with central_deps.pyodk_client(project.get_odk_credentials()) as client:
            response = client.session.delete(f"projects/{project.external_project_id}")
    except Exception as exc:
        raise DownstreamDeleteError(
            "Failed to connect to ODK Central for project "
            f"{project.external_project_id}: {exc}"
        ) from exc

    if HTTP_STATUS_OK_MIN <= response.status_code < HTTP_STATUS_OK_MAX_EXCLUSIVE:
        return f"Deleted ODK project {project.external_project_id}."
    if response.status_code == HTTP_STATUS_NOT_FOUND:
        return (
            f"ODK project {project.external_project_id} was already deleted; "
            "proceeding with Field-TM deletion."
        )

    detail = (response.text or "").strip() or response.reason_phrase
    raise DownstreamDeleteError(
        "Failed to delete ODK project "
        f"{project.external_project_id} (HTTP {response.status_code}): {detail}"
    )


async def _delete_qfield_downstream_project(project: DbProject) -> str:
    """Delete a QFieldCloud project, tolerating already-deleted remote state."""
    if not project.external_project_id:
        return "No QFieldCloud project id configured; skipped downstream deletion."

    loop = get_running_loop()
    async with qfield_client() as client:
        try:
            await loop.run_in_executor(
                None,
                partial(client.delete_project, project.external_project_id),
            )
            return f"Deleted QFieldCloud project {project.external_project_id}."
        except QfcRequestException as exc:
            status_code = exc.response.status_code
            if status_code == HTTP_STATUS_NOT_FOUND:
                return (
                    f"QFieldCloud project {project.external_project_id} was already "
                    "deleted; proceeding with Field-TM deletion."
                )
            raise DownstreamDeleteError(
                "Failed to delete QFieldCloud project "
                f"{project.external_project_id} (HTTP {status_code}): {exc}"
            ) from exc
        except Exception as exc:
            raise DownstreamDeleteError(
                "Failed to delete QFieldCloud project "
                f"{project.external_project_id}: {exc}"
            ) from exc


async def delete_project_with_downstream(
    db: AsyncConnection,
    project_id: int,
) -> DeleteProjectResult:
    """Delete downstream project first, then Field-TM project.

    If downstream deletion fails for any reason except "already deleted", the
    Field-TM project is preserved and a ``DownstreamDeleteError`` is raised.
    """
    try:
        project = await DbProject.one(db, project_id)
    except KeyError as exc:
        raise NotFoundError(f"Project ({project_id}) not found.") from exc

    if project.field_mapping_app == FieldMappingApp.ODK:
        downstream_status = await _delete_odk_downstream_project(project)
    elif project.field_mapping_app == FieldMappingApp.QFIELD:
        downstream_status = await _delete_qfield_downstream_project(project)
    else:
        downstream_status = (
            f"Unsupported field mapping app '{project.field_mapping_app}'; "
            "skipped downstream deletion."
        )

    await DbProject.delete(db, project_id)
    log.info("Deleted FieldTM project %s", project_id)
    return DeleteProjectResult(downstream_status=downstream_status)


def _build_stub_project_data(
    project_name: str,
    field_mapping_app: str,
    description: str,
    outline: dict,
    hashtags: list[str],
) -> project_schemas.StubProjectIn:
    """Build the DB payload for a draft project."""
    project_data = project_schemas.StubProjectIn(
        project_name=project_name,
        field_mapping_app=field_mapping_app,
        description=description.strip(),
        outline=outline,
        hashtags=hashtags,
        merge=True,
    )

    if hasattr(project_data, "merge"):
        delattr(project_data, "merge")
    project_data.status = ProjectStatus.DRAFT
    return project_data


async def _validate_outline_area_limit(
    db: AsyncConnection, project_data: project_schemas.StubProjectIn
) -> None:
    """Reject AOIs larger than the configured maximum area."""
    try:
        area_km2 = await geojson_area_km2(db, project_data.outline.model_dump())
        if area_km2 > AREA_LIMIT_KM2:
            raise ValidationError(
                f"Project area is too large ({area_km2:,.0f} km²). "
                f"The maximum allowed size is {AREA_LIMIT_KM2:,} km². "
                "Please select a smaller area."
            )
    except ValidationError:
        raise
    except Exception as e:
        log.warning(f"Could not calculate area for size check: {e}")


def _format_location_str(location) -> str | None:
    """Format reverse-geocoder output as a readable location string."""
    if not location:
        return None

    country_full_name = (
        countries.get(location.country, location.country) if location.country else None
    )
    if location.city and country_full_name:
        return f"{location.city}, {country_full_name}"
    if location.city:
        return location.city
    if country_full_name:
        return country_full_name
    return None


def _normalize_city_name(city_name: str | None) -> str | None:
    """Normalize nearest-city text before using it in generated names."""
    if not city_name:
        return None
    normalized = " ".join(str(city_name).split())
    return normalized or None


def _derive_simple_project_name(location, centroid=None) -> str:
    """Build the simplified project title from nearest city with fallback."""
    city_name = _normalize_city_name(getattr(location, "city", None))
    fallback_city = _format_simple_fallback_city(centroid)
    return _("{location} OSM Buildings").format(location=city_name or fallback_city)


def _derive_simple_project_metadata(
    location, centroid=None
) -> tuple[str, str, list[str]]:
    """Build name/description/tags for the simplified AOI-only workflow."""
    return (
        _derive_simple_project_name(location, centroid=centroid),
        _simple_project_description(),
        SIMPLE_PROJECT_TAGS.copy(),
    )


def _build_simple_outline_payload(outline: dict) -> dict:
    """Normalize simplified-flow outlines to GeoJSON geometry for storage."""
    featcol = parse_aoi(settings.FTM_DB_URL, outline, merge=True)
    featcol = merge_featcol_polygons_sync(settings.FTM_DB_URL, featcol)
    features = featcol.get("features", [])
    if not features:
        raise ValidationError(
            "You must draw or upload an Area of Interest (AOI) on the map."
        )
    geometry = features[0].get("geometry")
    if not geometry:
        raise ValidationError(
            "You must draw or upload an Area of Interest (AOI) on the map."
        )
    return geometry


async def derive_simple_project_metadata(
    db: AsyncConnection,
    outline: dict,
) -> tuple[str, str, list[str], str | None]:
    """Derive simplified-flow project metadata from AOI centroid lookup."""
    if not outline:
        raise ValidationError(
            "You must draw or upload an Area of Interest (AOI) on the map."
        )

    normalized_outline = _build_simple_outline_payload(outline)
    centroid = await polygon_to_centroid(normalized_outline)

    try:
        async with AsyncNearestCity(db) as geocoder:
            location = await geocoder.query(centroid.x, centroid.y)
    except Exception as e:
        log.warning(
            "Nearest-city lookup failed for simple workflow at lat=%s lon=%s; "
            "falling back to default naming. Error: %s",
            centroid.y,
            centroid.x,
            e,
            exc_info=True,
        )
        location = None

    project_name, description, hashtags = _derive_simple_project_metadata(
        location,
        centroid=centroid,
    )
    location_str = _format_location_str(location)
    return project_name, description, hashtags, location_str


async def _populate_project_location(
    db: AsyncConnection,
    project_name: str,
    project_data: project_schemas.StubProjectIn,
) -> None:
    """Best-effort reverse geocode for the project centroid."""
    try:
        outline_dict = project_data.outline.model_dump()
        async with AsyncNearestCity(db) as geocoder:
            centroid = await polygon_to_centroid(outline_dict)
            location = await geocoder.query(centroid.x, centroid.y)
            project_data.location_str = _format_location_str(location)
    except Exception as e:
        log.error(
            f"Error getting location for project {project_name}: {e}",
            exc_info=True,
        )
        project_data.location_str = None


async def create_project_stub(
    db: AsyncConnection,
    project_name: str,
    field_mapping_app: str,
    description: str,
    outline: dict,
    hashtags: list[str],
    user_sub: str,
) -> DbProject:
    """Create a project stub.

    Raises ValidationError for invalid inputs or ConflictError for duplicate names.
    """
    _validate_project_stub_inputs(project_name, field_mapping_app, description, outline)
    await _ensure_project_name_available(db, project_name)
    project_data = _build_stub_project_data(
        project_name,
        field_mapping_app,
        description,
        outline,
        hashtags,
    )
    await _validate_outline_area_limit(db, project_data)
    await _populate_project_location(db, project_name, project_data)
    project_data.created_by_sub = user_sub

    try:
        project = await DbProject.create(db, project_data)
    except Exception as e:
        log.error(f"Error creating project: {e}")
        raise ServiceError("Project creation failed.") from e

    return project


async def _build_project_xlsform(
    project_id: int,
    xlsform_bytes: BytesIO,
    **form_options,
) -> bytes:
    """Validate an uploaded XLSForm and add the Field-TM fields to it."""
    form_name = f"FTM_Project_{project_id}"

    await central_crud.validate_and_update_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        **form_options,
    )

    xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        **form_options,
    )

    project_xlsform.seek(0)
    xlsform_db_bytes = project_xlsform.getvalue()
    if len(xlsform_db_bytes) == 0 or not xform_id:
        raise ValidationError("There was an error modifying the XLSForm!")

    log.debug(
        f"Built XLSForm for xFormId: {xform_id}, bytes length: {len(xlsform_db_bytes)}"
    )
    return xlsform_db_bytes


async def process_xlsform(  # noqa: PLR0913
    db: AsyncConnection,
    project_id: int,
    xlsform_bytes: BytesIO,
    need_verification_fields: bool = True,
    include_photo_upload: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
    default_language: str | None = None,
    *,
    new_point_capture: NewPointCapture = NewPointCapture.MAP,
) -> None:
    """Validate, process, and store an XLSForm.

    Raises ValidationError if validation or processing fails.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    xlsform_db_bytes = await _build_project_xlsform(
        project.id,
        xlsform_bytes,
        need_verification_fields=need_verification_fields,
        include_photo_upload=include_photo_upload,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
        new_point_capture=new_point_capture,
    )

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(xlsform_content=xlsform_db_bytes),
    )
    await db.commit()
    log.debug(f"Successfully saved XLSForm to database for project {project_id}")


async def update_odk_project_form(
    db: AsyncConnection,
    project: DbProject,
    xlsform_bytes: BytesIO,
) -> None:
    """Publish a new form version to ODK Central, then store it.

    The new version keeps the form ID and Field-TM options of the current form.
    """
    form_options = get_processed_form_options(project.xlsform_content)
    xlsform_db_bytes = await _build_project_xlsform(
        project.id,
        xlsform_bytes,
        use_odk_collect=True,
        **form_options,
    )

    await central_crud.update_odk_xform(
        int(project.external_project_id),
        form_options["form_id"],
        await central_crud.read_and_test_xform(BytesIO(xlsform_db_bytes)),
        project.get_odk_credentials(),
    )

    await DbProject.update(
        db,
        project.id,
        project_schemas.ProjectUpdate(xlsform_content=xlsform_db_bytes),
    )
    await db.commit()


def _as_aoi_feature_collection(outline: dict) -> dict:
    """Wrap a project outline geometry in a single-feature collection."""
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": outline, "properties": {}}],
    }


async def split_aoi(
    db: AsyncConnection,
    project_id: int,
    algorithm: SplittingAlgorithm,
    num_buildings: int,
    statement_timeout_ms: Optional[int] = None,
) -> dict:
    """Split a project AOI by building count (used by the simple flow).

    Custom projects split in the browser-based task planner instead.
    """
    project = await DbProject.one(db, project_id)
    if not project.outline:
        raise NotFoundError("Project outline not found. Cannot split AOI.")
    extract = project.data_extract_geojson
    if not isinstance(extract, dict) or extract.get("type") != "FeatureCollection":
        raise ValidationError("Data extract required for task splitting.")

    # Don't hold the outer transaction open during the threaded split.
    await db.commit()
    split = partial(
        split_by_sql,
        _as_aoi_feature_collection(project.outline),
        settings.FTM_DB_URL,
        num_buildings=None,
        outfile=None,
        osm_extract=extract,
        algorithm=algorithm,
        algorithm_params={
            "num_buildings": num_buildings,
            "include_roads": "TRUE",
            "include_rivers": "TRUE",
            "include_railways": "TRUE",
            "include_aeroways": "TRUE",
        },
        statement_timeout_ms=statement_timeout_ms,
    )
    features = await to_thread.run_sync(split)
    if not features or not features.get("features"):
        raise ValidationError("No task areas generated.")
    await check_crs(features)
    return features


async def save_task_areas(
    db: AsyncConnection,
    project_id: int,
    tasks_geojson: dict,
) -> int:
    """Store task areas and return their count; {} means no splitting.

    Raises ValidationError for invalid GeoJSON.
    """
    if not isinstance(tasks_geojson, dict):
        raise ValidationError("Invalid task areas data format.")

    if tasks_geojson and tasks_geojson.get("features"):
        await check_crs(tasks_geojson)
        # Persist stable task IDs for all export paths.
        stamp_missing_task_ids(tasks_geojson)

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(task_areas_geojson=tasks_geojson),
    )
    await db.commit()

    is_empty = tasks_geojson == {}
    task_count = len(tasks_geojson.get("features", [])) if not is_empty else 0

    log.info(
        f"Saved task areas for project {project_id} "
        f"(empty: {is_empty}, count: {task_count})"
    )
    return task_count


async def publish_project(db: AsyncConnection, project_id: int) -> None:
    """Publish a files-only (Type B) project: there is nothing to sync."""
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(status=ProjectStatus.PUBLISHED),
    )
    await db.commit()


async def finalize_qfield_project(
    db: AsyncConnection,
    project_id: int,
    custom_qfield_creds=None,
    default_language: str | None = None,
) -> QFieldFinalizeResult:
    """Publish to QFieldCloud and return its URL.

    Raises ValidationError for missing prerequisites or ServiceError if creation fails.
    """
    project = await DbProject.one(db, project_id)

    if not project.xlsform_content:
        raise ValidationError("XLSForm is required. Please upload a form first.")
    if project.data_extract_geojson is None:
        raise ValidationError(
            "Data extract is required. "
            "Please download OSM data or upload GeoJSON first."
        )

    log.info(f"Creating QField project for Field-TM project {project_id}")
    qfield_url = await create_qfield_project(
        db,
        project,
        custom_qfield_creds,
        default_language=default_language,
    )

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            status=ProjectStatus.PUBLISHED,
            tasks_synced_hash=tasks_geometry_hash(project),
        ),
    )
    await db.commit()

    return QFieldFinalizeResult(qfield_url=qfield_url)
