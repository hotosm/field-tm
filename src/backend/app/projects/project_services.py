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
"""Shared service layer for project operations.

These functions contain the core business logic used by both HTMX routes
and REST API routes. They accept typed arguments and raise domain exceptions
(not HTTP exceptions), returning plain data structures.
"""

import json
import logging
from dataclasses import dataclass
from functools import partial
from io import BytesIO
from typing import Optional

import aiohttp
from anyio import to_thread
from area_splitter import SplittingAlgorithm
from area_splitter.splitter import split_by_sql, split_by_square
from geojson_aoi import parse_aoi
from osm_fieldwork.json_data_models import data_models_path
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection

from app.central import central_crud, central_deps
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.enums import ProjectStatus, XLSFormType
from app.db.languages_and_countries import countries
from app.db.models import DbProject
from app.helpers.geometry_utils import (
    AREA_LIMIT_KM2,
    check_crs,
    featcol_keep_single_geom_type,
    geojson_area_km2,
    polygon_to_centroid,
)
from app.projects import project_crud, project_deps, project_schemas

log = logging.getLogger(__name__)


# ============================================================================
# Domain exceptions (no HTTP concepts)
# ============================================================================


class ServiceError(Exception):
    """Base exception for service layer errors."""

    def __init__(self, message: str, code: str = "error"):
        """Initialize with message and error code."""
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(ServiceError):
    """Input validation failed."""

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="validation_error")


class NotFoundError(ServiceError):
    """Resource not found."""

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="not_found")


class ConflictError(ServiceError):
    """Resource conflict (e.g. duplicate name)."""

    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message, code="conflict")


@dataclass(slots=True)
class ODKFinalizeResult:
    """Details returned after ODK finalization."""

    odk_url: str
    manager_username: str
    manager_password: str


def _first_outline_feature(outline: Optional[dict]) -> Optional[dict]:
    """Normalize a project outline to a single GeoJSON Feature."""
    if not outline or not isinstance(outline, dict):
        return None

    outline_type = str(outline.get("type", "")).strip()
    if outline_type == "FeatureCollection":
        features = outline.get("features", [])
        if isinstance(features, list) and features:
            first_feature = features[0]
            if isinstance(first_feature, dict):
                return first_feature
        return None

    if outline_type == "Feature":
        return outline

    # Stored project outlines are typically geometry objects from PostGIS.
    if "coordinates" in outline:
        return {"type": "Feature", "geometry": outline, "properties": {}}

    return None


def _resolve_odk_public_url(custom_odk_creds: Optional[ODKCentral]) -> str:
    """Resolve public ODK base URL used for UI links and persisted instance URL."""
    if custom_odk_creds and custom_odk_creds.external_project_instance_url:
        return custom_odk_creds.external_project_instance_url.rstrip("/")
    return str(
        settings.ODK_CENTRAL_PUBLIC_URL or settings.ODK_CENTRAL_URL or ""
    ).rstrip("/")


# ============================================================================
# Service functions
# ============================================================================


async def create_project_stub(  # noqa: C901, PLR0912, PLR0913, PLR0915
    db: AsyncConnection,
    project_name: str,
    field_mapping_app: str,
    description: str,
    outline: dict,
    hashtags: list[str],
    user_sub: str,
) -> DbProject:  # noqa: C901, PLR0912, PLR0913, PLR0915
    """Create a new project stub in the database.

    Args:
        db: Database connection.
        project_name: Name for the project.
        field_mapping_app: The field mapping app (ODK or QField).
        description: Project description.
        outline: GeoJSON geometry for the project area.
        hashtags: List of hashtag strings.
        user_sub: The authenticated user's sub identifier.

    Returns:
        The created DbProject.

    Raises:
        ValidationError: If required fields are missing.
        ConflictError: If project name already exists.
    """
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

    # Check for duplicate project name
    exists = await project_deps.project_name_does_not_already_exist(db, project_name)
    if exists:
        raise ConflictError(
            f"Project with name '{project_name}' already exists. "
            "Please choose a different name."
        )

    # Create StubProjectIn object
    project_data = project_schemas.StubProjectIn(
        project_name=project_name,
        field_mapping_app=field_mapping_app,
        description=description.strip(),
        outline=outline,
        hashtags=hashtags,
        merge=True,
    )

    # Remove merge field as it is not in database
    # TODO check this is still needed?
    if hasattr(project_data, "merge"):
        delattr(project_data, "merge")
    project_data.status = ProjectStatus.DRAFT

    # Check project area size (outline is already parsed by geojson-aoi-parser)
    try:
        outline_dict = project_data.outline.model_dump()
        area_km2 = geojson_area_km2(outline_dict)
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

    # Get the location_str via reverse geocode
    try:
        outline_dict = project_data.outline.model_dump()
        async with AsyncNearestCity(db) as geocoder:
            centroid = await polygon_to_centroid(outline_dict)
            latitude, longitude = centroid.y, centroid.x
            location = await geocoder.query(latitude, longitude)
            if location:
                country_full_name = (
                    countries.get(location.country, location.country)
                    if location.country
                    else None
                )
                if location.city and country_full_name:
                    project_data.location_str = f"{location.city}, {country_full_name}"
                elif location.city:
                    project_data.location_str = location.city
                elif country_full_name:
                    project_data.location_str = country_full_name
                else:
                    project_data.location_str = None
            else:
                project_data.location_str = None
    except Exception as e:
        log.error(
            f"Error getting location for project {project_name}: {e}",
            exc_info=True,
        )
        project_data.location_str = None

    # Create the project in the Field-TM DB
    project_data.created_by_sub = user_sub
    try:
        project = await DbProject.create(db, project_data)
    except Exception as e:
        log.error(f"Error creating project: {e}")
        raise ServiceError("Project creation failed.") from e

    return project


async def process_xlsform(
    db: AsyncConnection,
    project_id: int,
    xlsform_bytes: BytesIO,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
    default_language: str = "english",
) -> None:  # noqa: PLR0913
    """Validate, process, and store an XLSForm for a project.

    Args:
        db: Database connection.
        project_id: The project ID.
        xlsform_bytes: BytesIO of the XLSForm file.
        need_verification_fields: Whether to add verification fields.
        mandatory_photo_upload: Whether photo upload is mandatory.
        use_odk_collect: Whether to use ODK Collect.
        default_language: Default language for the form.

    Raises:
        ValidationError: If the form is invalid or processing fails.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    form_name = f"FMTM_Project_{project.id}"

    # Validate and process the form
    await central_crud.validate_and_update_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform_bytes,
        form_name=form_name,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        default_language=default_language,
        use_odk_collect=use_odk_collect,
    )

    # Write XLS form content to db
    project_xlsform.seek(0)
    xlsform_db_bytes = project_xlsform.getvalue()
    if len(xlsform_db_bytes) == 0 or not xform_id:
        raise ValidationError("There was an error modifying the XLSForm!")

    log.debug(
        f"Setting project XLSForm db data for xFormId: {xform_id}, "
        f"bytes length: {len(xlsform_db_bytes)}"
    )
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(xlsform_content=xlsform_db_bytes),
    )
    await db.commit()
    log.debug(f"Successfully saved XLSForm to database for project {project_id}")


async def download_osm_data(  # noqa: C901
    db: AsyncConnection,
    project_id: int,
    osm_category: str = "buildings",
    geom_type: str = "POLYGON",
    centroid: bool = False,
) -> dict:  # noqa: C901
    """Download OSM data extract for a project and return the GeoJSON.

    Args:
        db: Database connection.
        project_id: The project ID.
        osm_category: OSM category (e.g. buildings, highways).
        geom_type: Geometry type (POLYGON, POINT, POLYLINE).
        centroid: Whether to generate centroids.

    Returns:
        A validated GeoJSON FeatureCollection dict.

    Raises:
        NotFoundError: If project outline is missing.
        ServiceError: If data extraction fails.
    """
    project = await project_deps.get_project_by_id(db, project_id)

    outline = project.outline
    if not outline:
        raise NotFoundError("Project outline not found.")

    # Convert outline to FeatureCollection format
    aoi_featcol = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": outline, "properties": {}}],
    }

    # Get extract config
    try:
        osm_category_enum = XLSFormType[osm_category.lower()]
    except (KeyError, AttributeError):
        osm_category_enum = XLSFormType.buildings

    config_filename = osm_category_enum.name
    data_model = f"{data_models_path}/{config_filename}.json"

    with open(data_model, encoding="utf-8") as f:
        config_data = json.load(f)

    geom_type_lower = geom_type.lower()
    data_config = {
        ("polygon", False): ["ways_poly"],
        ("point", True): ["ways_poly", "nodes"],
        ("point", False): ["nodes"],
        ("polyline", False): ["ways_line"],
    }

    config_data["from"] = data_config.get((geom_type_lower, centroid))
    if geom_type_lower == "polyline":
        geom_type_lower = "line"

    # Generate data extract
    result = await project_crud.generate_data_extract(
        project.id,
        aoi_featcol,
        geom_type_lower,
        config_data,
        centroid,
        True,
    )

    # Download GeoJSON from URL
    download_url = result.data.get("download_url")
    if not download_url:
        raise ServiceError("Failed to get download URL from data extract.")

    # Download and parse GeoJSON
    async with (
        aiohttp.ClientSession() as session,
        session.get(download_url) as response,
    ):
        if not response.ok:
            raise ServiceError("Failed to download GeoJSON from extract URL.")
        text_content = await response.text()
        try:
            geojson_data = json.loads(text_content)
        except json.JSONDecodeError as e:
            raise ServiceError("Failed to parse GeoJSON data from download.") from e

    if not isinstance(geojson_data, dict):
        raise ServiceError("Downloaded extract is not valid GeoJSON data.")

    # Some extract responses may return `"features": null` for empty results.
    features = geojson_data.get("features")
    if features is None:
        features = []
        geojson_data["features"] = features
    if not isinstance(features, list):
        raise ServiceError("Downloaded GeoJSON has invalid feature structure.")
    if len(features) == 0:
        raise ValidationError(
            "No matching OSM features were found for this area and selection. "
            "Try different extract options, upload custom GeoJSON, "
            "or choose Collect New Data Only."
        )

    # Validate and clean GeoJSON
    featcol = parse_aoi(settings.FMTM_DB_URL, geojson_data)
    featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

    if not featcol_single_geom_type:
        raise ServiceError("Could not process GeoJSON data.")

    await check_crs(featcol_single_geom_type)

    return featcol_single_geom_type


async def save_data_extract(
    db: AsyncConnection,
    project_id: int,
    geojson_data: dict,
) -> int:
    """Save a GeoJSON data extract to the database.

    Args:
        db: Database connection.
        project_id: The project ID.
        geojson_data: The GeoJSON FeatureCollection dict to save.

    Returns:
        Number of features saved.

    Raises:
        ValidationError: If the GeoJSON is empty or invalid.
    """
    if not geojson_data:
        raise ValidationError("No GeoJSON data provided.")

    features = geojson_data.get("features", [])
    if not features:
        raise ValidationError("GeoJSON data contains no features.")

    # Validate CRS
    await check_crs(geojson_data)

    # Save to database
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_geojson=geojson_data,
            # Reset split status when a new extract is accepted.
            task_areas_geojson=None,
        ),
    )
    await db.commit()

    feature_count = len(features)
    log.info(
        f"Saved data extract with {feature_count} features for project {project_id}"
    )
    return feature_count


async def split_aoi(  # noqa: C901, PLR0913
    db: AsyncConnection,
    project_id: int,
    algorithm: str,
    no_of_buildings: int = 10,
    dimension_meters: int = 100,
    include_roads: bool = True,
    include_rivers: bool = True,
    include_railways: bool = True,
    include_aeroways: bool = True,
) -> dict:  # noqa: C901, PLR0913
    """Split a project AOI into task areas.

    Args:
        db: Database connection.
        project_id: The project ID.
        algorithm: Splitting algorithm name.
        no_of_buildings: Number of buildings per task (for building-based algorithms).
        dimension_meters: Grid dimension in meters (for square splitting).
        include_roads: Include road lines for building-based split guidance.
        include_rivers: Include river lines for building-based split guidance.
        include_railways: Include railway lines for building-based split guidance.
        include_aeroways: Include aeroway lines for building-based split guidance.

    Returns:
        A GeoJSON FeatureCollection of task areas, or empty dict for NO_SPLITTING.

    Raises:
        ValidationError: If algorithm is invalid or required data is missing.
        NotFoundError: If project outline is missing.
    """
    project = await DbProject.one(db, project_id)

    if not project.outline:
        raise NotFoundError("Project outline not found. Cannot split AOI.")

    if not algorithm:
        raise ValidationError("Please select a splitting option.")

    try:
        algorithm_enum = SplittingAlgorithm(algorithm)
    except ValueError as err:
        raise ValidationError(f"Invalid algorithm type: {algorithm}") from err

    # Handle NO_SPLITTING case
    if algorithm_enum == SplittingAlgorithm.NO_SPLITTING:
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(task_areas_geojson={}),
        )
        await db.commit()
        log.info(
            f"No splitting selected for project {project_id}. "
            "Will use whole AOI as single task."
        )
        return {}

    # Convert outline to FeatureCollection
    aoi_featcol = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": project.outline, "properties": {}}
        ],
    }

    # Get data extract from database
    parsed_extract = project.data_extract_geojson
    is_empty_data_extract = parsed_extract == {} or (
        isinstance(parsed_extract, dict)
        and parsed_extract.get("type") == "FeatureCollection"
        and len(parsed_extract.get("features", [])) == 0
    )

    # If data extract is empty, skip splitting
    if is_empty_data_extract:
        log.info(
            f"Empty data extract for project {project_id}. "
            "Skipping split and saving empty task areas."
        )
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(task_areas_geojson={}),
        )
        await db.commit()
        return {}

    # Perform splitting based on algorithm
    log.info(f"Splitting AOI for project {project_id} using algorithm: {algorithm}")

    if algorithm_enum in (
        SplittingAlgorithm.AVG_BUILDING_VORONOI,
        SplittingAlgorithm.AVG_BUILDING_SKELETON,
    ):
        if (
            not parsed_extract
            or not isinstance(parsed_extract, dict)
            or parsed_extract.get("type") != "FeatureCollection"
        ):
            raise ValidationError(
                "Data extract required for task splitting algorithm. "
                "Please download OSM data or upload GeoJSON first and accept it."
            )

        algorithm_params = {
            "num_buildings": no_of_buildings,
            "include_roads": "TRUE" if include_roads else "FALSE",
            "include_rivers": "TRUE" if include_rivers else "FALSE",
            "include_railways": "TRUE" if include_railways else "FALSE",
            "include_aeroways": "TRUE" if include_aeroways else "FALSE",
        }

        split_sql_call = partial(
            split_by_sql,
            aoi_featcol,
            settings.FMTM_DB_URL,
            num_buildings=None,
            outfile=None,
            osm_extract=parsed_extract,
            algorithm=algorithm_enum,
            algorithm_params=algorithm_params,
        )
        features = await to_thread.run_sync(split_sql_call)
    elif algorithm_enum == SplittingAlgorithm.DIVIDE_BY_SQUARE:
        features = await to_thread.run_sync(
            split_by_square,
            aoi_featcol,
            settings.FMTM_DB_URL,
            dimension_meters,
            parsed_extract
            if (
                parsed_extract
                and isinstance(parsed_extract, dict)
                and parsed_extract.get("type") == "FeatureCollection"
            )
            else None,
            None,
        )
    elif algorithm_enum == SplittingAlgorithm.TOTAL_TASKS:
        raise ValidationError(
            "Split by Specific Number of Tasks is not yet implemented."
        )
    else:
        raise ValidationError(f"Algorithm {algorithm} not yet implemented.")

    if not features or not features.get("features"):
        raise ValidationError(
            "No task areas generated. Please try different parameters."
        )

    await check_crs(features)
    return features


async def save_task_areas(
    db: AsyncConnection,
    project_id: int,
    tasks_geojson: dict,
) -> int:
    """Save task split results to the database.

    Args:
        db: Database connection.
        project_id: The project ID.
        tasks_geojson: GeoJSON FeatureCollection of task areas (or {} for no splitting).

    Returns:
        Number of tasks saved (0 for no splitting).

    Raises:
        ValidationError: If the GeoJSON is invalid.
    """
    if not isinstance(tasks_geojson, dict):
        raise ValidationError("Invalid task areas data format.")

    # Validate CRS if not empty
    if tasks_geojson and tasks_geojson.get("features"):
        await check_crs(tasks_geojson)

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


async def finalize_odk_project(  # noqa: C901, PLR0912, PLR0915
    db: AsyncConnection,
    project_id: int,
    custom_odk_creds: Optional[ODKCentral] = None,
) -> ODKFinalizeResult:  # noqa: C901, PLR0912, PLR0915
    """Create project in ODK Central with all data.

    Args:
        db: Database connection.
        project_id: The project ID.
        custom_odk_creds: Optional custom ODK credentials (None uses env vars).

    Returns:
        Finalization details including Central URL and manager credentials.

    Raises:
        ValidationError: If prerequisites are missing.
        ServiceError: If ODK project creation fails.
    """
    project = await DbProject.one(db, project_id)

    if not project.xlsform_content:
        raise ValidationError("XLSForm is required. Please upload a form first.")
    if project.data_extract_geojson is None:
        raise ValidationError(
            "Data extract is required. "
            "Please download OSM data or upload GeoJSON first."
        )

    # Validate ODK credentials
    if not custom_odk_creds and (
        not settings.ODK_CENTRAL_URL or not settings.ODK_CENTRAL_USER
    ):
        raise ValidationError(
            "ODK Central credentials are not configured on the server. "
            "Please provide custom ODK credentials."
        )

    # Step 1: Create ODK project if it doesn't exist
    project_odk_id = project.external_project_id
    if not project_odk_id:
        log.info(f"Creating ODK project for Field-TM project {project_id}")
        odk_project = await central_crud.create_odk_project(
            project.project_name,
            custom_odk_creds,
        )
        project_odk_id = odk_project["id"]
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(external_project_id=project_odk_id),
        )
        await db.commit()
        log.info(
            f"Created ODK project {project_odk_id} for Field-TM project {project_id}"
        )

    # Persist ODK connection details used for this project.
    # Custom advanced config should remain available for future QR/token refresh.
    odk_instance_url = _resolve_odk_public_url(custom_odk_creds)
    should_update_odk_details = False
    update_payload = project_schemas.ProjectUpdate(external_project_id=project_odk_id)

    if odk_instance_url and odk_instance_url != (
        project.external_project_instance_url or ""
    ):
        update_payload.external_project_instance_url = odk_instance_url
        should_update_odk_details = True

    if custom_odk_creds:
        if custom_odk_creds.external_project_username:
            update_payload.external_project_username = (
                custom_odk_creds.external_project_username
            )
            should_update_odk_details = True
        if custom_odk_creds.external_project_password:
            update_payload.external_project_password = (
                custom_odk_creds.external_project_password
            )
            should_update_odk_details = True

    if should_update_odk_details:
        await DbProject.update(
            db,
            project_id,
            update_payload,
        )
        await db.commit()

    # Step 2: Create entity list "features" from data extract
    geojson_data = project.data_extract_geojson or {}
    features = (
        geojson_data.get("features", []) if isinstance(geojson_data, dict) else []
    )
    entity_properties: list[str] = []
    entities_list: list[dict] = []

    if features:
        first_feature = features[0]
        entity_properties = list(first_feature.get("properties", {}).keys())

        for field in ["created_by", "fill", "marker-color", "stroke", "stroke-width"]:
            if field not in entity_properties:
                entity_properties.append(field)

        entities_list = await central_crud.task_geojson_dict_to_entity_values(
            geojson_data, additional_features=True
        )

        default_style = {
            "fill": "#1a1a1a",
            "marker-color": "#1a1a1a",
            "stroke": "#000000",
            "stroke-width": "6",
        }

        for entity in entities_list:
            data = entity["data"]
            for key, value in default_style.items():
                data.setdefault(key, value)
    else:
        log.info(
            "No existing features supplied for project %s. "
            "Creating empty 'features' dataset for collect-new-data workflow.",
            project_id,
        )

    log.info(f"Creating entity list 'features' for ODK project {project_odk_id}")
    await central_crud.create_entity_list(
        custom_odk_creds,
        project_odk_id,
        properties=entity_properties,
        dataset_name="features",
        entities_list=entities_list,
    )

    # Step 3: Upload task entities (always needed for entity-based task selection)
    task_areas = project.task_areas_geojson
    task_entities = []
    if task_areas and task_areas.get("features"):
        log.info(
            f"Uploading {len(task_areas.get('features', []))} task boundaries to ODK"
        )
        for idx, feature in enumerate(task_areas.get("features", [])):
            if feature.get("geometry"):
                entity_dict = await central_crud.feature_geojson_to_entity_dict(
                    feature, additional_features=True
                )
                entity_dict["label"] = f"Task {idx + 1}"
                entity_dict["data"] = {
                    "geometry": entity_dict["data"]["geometry"],
                    "task_id": str(idx + 1),
                    "status": "ready",
                    "fill": "#3388ff33",
                    "stroke": "#3388ff",
                    "stroke-width": "3",
                }
                task_entities.append(entity_dict)

    if not task_entities:
        # Create a single task from the project outline so tasks.csv always has data
        log.info(
            "No task areas found, creating single task entity from project outline"
        )
        outline_feature = _first_outline_feature(project.outline)
        if outline_feature and outline_feature.get("geometry"):
            entity_dict = await central_crud.feature_geojson_to_entity_dict(
                outline_feature, additional_features=True
            )
            entity_dict["label"] = "Task 1"
            entity_dict["data"] = {
                "geometry": entity_dict["data"]["geometry"],
                "task_id": "1",
                "status": "ready",
                "fill": "#3388ff33",
                "stroke": "#3388ff",
                "stroke-width": "3",
            }
            task_entities.append(entity_dict)
        else:
            raise ValidationError(
                "Project outline is missing or invalid. "
                "Cannot create fallback task for ODK finalization."
            )

    if task_entities:
        try:
            async with central_deps.get_odk_dataset(custom_odk_creds) as odk_central:
                datasets = await odk_central.listDatasets(project_odk_id)
                if any(ds.get("name") == "tasks" for ds in datasets):
                    log.info("Tasks dataset already exists, will be replaced")
        except Exception as e:
            log.warning(f"Could not check existing datasets: {e}")

        await central_crud.create_entity_list(
            custom_odk_creds,
            project_odk_id,
            properties=[
                "geometry",
                "task_id",
                "status",
                "fill",
                "stroke",
                "stroke-width",
            ],
            dataset_name="tasks",
            entities_list=task_entities,
        )

    # Step 4: Upload XLSForm
    xlsform_bytes = BytesIO(project.xlsform_content)
    xform = await central_crud.read_and_test_xform(xlsform_bytes)
    log.info(f"Uploading XLSForm to ODK project {project_odk_id}")
    await central_crud.create_odk_xform(
        project_odk_id,
        xform,
        custom_odk_creds,
    )

    # Step 5: Generate project files (appusers, QR codes, etc.)
    log.info(f"Generating project files for project {project_id}")
    success = await project_crud.generate_project_files(
        db, project_id, odk_credentials=custom_odk_creds
    )

    if not success:
        raise ServiceError("Failed to generate project files. Please contact support.")

    # Build ODK project URL
    odk_url = f"{_resolve_odk_public_url(custom_odk_creds)}/#/projects/{project_odk_id}"

    try:
        (
            manager_username,
            manager_password,
        ) = await central_crud.create_project_manager_user(
            project_odk_id=project_odk_id,
            project_name=project.project_name or f"Project {project_id}",
            odk_credentials=custom_odk_creds,
        )
    except Exception as e:
        manager_error = getattr(e, "detail", str(e))
        raise ServiceError(
            f"Failed to create ODK Central manager user. {manager_error}"
        ) from e

    # Update project status to PUBLISHED only after manager account exists.
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(status=ProjectStatus.PUBLISHED),
    )
    await db.commit()

    return ODKFinalizeResult(
        odk_url=odk_url,
        manager_username=manager_username,
        manager_password=manager_password,
    )


async def finalize_qfield_project(
    db: AsyncConnection,
    project_id: int,
    custom_qfield_creds=None,
) -> str:
    """Create project in QField with all data.

    Args:
        db: Database connection.
        project_id: The project ID.
        custom_qfield_creds: Optional custom QField credentials.

    Returns:
        URL to the QField project.

    Raises:
        ValidationError: If prerequisites are missing.
        ServiceError: If QField project creation fails.
    """
    from app.qfield.qfield_crud import create_qfield_project

    project = await DbProject.one(db, project_id)

    if not project.xlsform_content:
        raise ValidationError("XLSForm is required. Please upload a form first.")
    if project.data_extract_geojson is None:
        raise ValidationError(
            "Data extract is required. "
            "Please download OSM data or upload GeoJSON first."
        )

    log.info(f"Creating QField project for Field-TM project {project_id}")
    qfield_url = await create_qfield_project(db, project, custom_qfield_creds)

    # Update project status to PUBLISHED
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(status=ProjectStatus.PUBLISHED),
    )
    await db.commit()

    return qfield_url
