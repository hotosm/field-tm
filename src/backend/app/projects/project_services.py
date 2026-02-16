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
from io import BytesIO
from typing import Optional

import aiohttp
from anyio import to_thread
from area_splitter import SplittingAlgorithm
from area_splitter.splitter import split_by_sql, split_by_square
from osm_fieldwork.json_data_models import data_models_path
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection

from app.central import central_crud, central_deps
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.enums import ProjectStatus, XLSFormType
from app.db.languages_and_countries import countries
from app.db.models import DbProject
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    parse_geojson_file_to_featcol,
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
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(ServiceError):
    """Input validation failed."""

    def __init__(self, message: str):
        super().__init__(message, code="validation_error")


class NotFoundError(ServiceError):
    """Resource not found."""

    def __init__(self, message: str):
        super().__init__(message, code="not_found")


class ConflictError(ServiceError):
    """Resource conflict (e.g. duplicate name)."""

    def __init__(self, message: str):
        super().__init__(message, code="conflict")


# ============================================================================
# Service functions
# ============================================================================


async def create_project_stub(
    db: AsyncConnection,
    project_name: str,
    field_mapping_app: str,
    description: str,
    outline: dict,
    hashtags: list[str],
    user_sub: str,
) -> DbProject:
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
    if hasattr(project_data, "merge"):
        delattr(project_data, "merge")
    project_data.status = ProjectStatus.DRAFT

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
) -> None:
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


async def download_osm_data(
    db: AsyncConnection,
    project_id: int,
    osm_category: str = "buildings",
    geom_type: str = "POLYGON",
    centroid: bool = False,
) -> dict:
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
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as response:
            if not response.ok:
                raise ServiceError("Failed to download GeoJSON from extract URL.")
            text_content = await response.text()
            try:
                geojson_data = json.loads(text_content)
            except json.JSONDecodeError as e:
                raise ServiceError("Failed to parse GeoJSON data from download.") from e

    # Validate and clean GeoJSON
    featcol = parse_geojson_file_to_featcol(json.dumps(geojson_data))
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
        project_schemas.ProjectUpdate(data_extract_geojson=geojson_data),
    )
    await db.commit()

    feature_count = len(features)
    log.info(
        f"Saved data extract with {feature_count} features for project {project_id}"
    )
    return feature_count


async def split_aoi(
    db: AsyncConnection,
    project_id: int,
    algorithm: str,
    no_of_buildings: int = 50,
    dimension_meters: int = 100,
) -> dict:
    """Split a project AOI into task areas.

    Args:
        db: Database connection.
        project_id: The project ID.
        algorithm: Splitting algorithm name.
        no_of_buildings: Number of buildings per task (for building-based algorithms).
        dimension_meters: Grid dimension in meters (for square splitting).

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
    except ValueError:
        raise ValidationError(f"Invalid algorithm type: {algorithm}")

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
    is_empty_data_extract = parsed_extract == {}

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

        algorithm_params = {}
        for param in algorithm_enum.required_params:
            if param == "num_buildings":
                algorithm_params["num_buildings"] = no_of_buildings

        features = await to_thread.run_sync(
            split_by_sql,
            aoi_featcol,
            settings.FMTM_DB_URL,
            num_buildings=None,
            outfile=None,
            osm_extract=parsed_extract,
            algorithm=algorithm_enum,
            algorithm_params=algorithm_params,
        )
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


async def finalize_odk_project(
    db: AsyncConnection,
    project_id: int,
    custom_odk_creds: Optional[ODKCentral] = None,
) -> str:
    """Create project in ODK Central with all data.

    Args:
        db: Database connection.
        project_id: The project ID.
        custom_odk_creds: Optional custom ODK credentials (None uses env vars).

    Returns:
        URL to the ODK Central project.

    Raises:
        ValidationError: If prerequisites are missing.
        ServiceError: If ODK project creation fails.
    """
    project = await DbProject.one(db, project_id)

    if not project.xlsform_content:
        raise ValidationError("XLSForm is required. Please upload a form first.")
    if not project.data_extract_geojson:
        raise ValidationError(
            "Data extract is required. Please download OSM data or upload GeoJSON first."
        )

    # Validate ODK credentials
    if not custom_odk_creds:
        if not settings.ODK_CENTRAL_URL or not settings.ODK_CENTRAL_USER:
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

    # Persist the ODK base URL
    odk_instance_url = (
        custom_odk_creds.external_project_instance_url
        if custom_odk_creds
        else str(settings.ODK_CENTRAL_URL or "")
    )
    if odk_instance_url and odk_instance_url != (
        project.external_project_instance_url or ""
    ):
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(
                external_project_instance_url=odk_instance_url,
                external_project_id=project_odk_id,
            ),
        )
        await db.commit()

    # Step 2: Create entity list "features" from data extract
    geojson_data = project.data_extract_geojson
    features = geojson_data.get("features", [])
    if not features:
        raise ValidationError("Data extract contains no features.")

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
        log.info("No task areas found, creating single task entity from project outline")
        outline_geojson = project.outline_geojson
        if outline_geojson and outline_geojson.get("features"):
            outline_feature = outline_geojson["features"][0]
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
            properties=["geometry", "task_id", "status", "fill", "stroke", "stroke-width"],
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
    success = await project_crud.generate_project_files(db, project_id)

    if not success:
        raise ServiceError("Failed to generate project files. Please contact support.")

    # Update project status to PUBLISHED
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(status=ProjectStatus.PUBLISHED),
    )
    await db.commit()

    # Build ODK project URL
    if custom_odk_creds:
        base_url = custom_odk_creds.external_project_instance_url.rstrip("/")
    else:
        base_url = settings.ODK_CENTRAL_URL.rstrip("/")
    odk_url = f"{base_url}/#/projects/{project_odk_id}"

    return odk_url


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
    if not project.data_extract_geojson:
        raise ValidationError(
            "Data extract is required. Please download OSM data or upload GeoJSON first."
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
