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
"""Endpoints for Field-TM projects (Litestar)."""

import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Annotated, Optional

from anyio import to_thread
from area_splitter.splitter import split_by_sql, split_by_square
from geojson_pydantic import FeatureCollection
from litestar import Response, Router, delete, get, patch, post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from osm_fieldwork.json_data_models import data_models_path, get_choices
from osm_fieldwork.update_xlsform import append_task_id_choices
from pg_nearest_city import AsyncNearestCity
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper, project_manager, super_admin
from app.central import central_crud
from app.config import settings
from app.db.database import db_conn
from app.db.enums import DbGeomType, ProjectStatus, XLSFormType
from app.db.languages_and_countries import countries
from app.db.models import (
    DbProject,
    DbUser,
    FieldMappingApp,
)
from app.db.postgis_utils import (
    check_crs,
    merge_polygons,
    parse_geojson_file_to_featcol,
    polygon_to_centroid,
)
from app.helpers import helper_schemas
from app.projects import project_crud, project_deps, project_schemas
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_crud import create_qfield_project, delete_qfield_project

log = logging.getLogger(__name__)


@get(
    "/",
    summary="Return all projects.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    return_dto=project_schemas.ProjectOut,
)
async def read_projects(
    db: AsyncConnection,
    user_sub: Optional[str] | None = None,
    skip: Optional[int] = 0,
    limit: Optional[int] = 100,
    hashtags: Optional[list[str]] = None,
) -> list[DbProject]:
    """Return all projects."""
    projects = await DbProject.all(db, skip, limit, user_sub, hashtags)
    return projects or []


@post(
    "/near_me",
    summary="Get projects near the current user.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def get_tasks_near_me(
    lat: float,
    long: float,
) -> None:
    """Get projects near me.

    TODO to be implemented in future.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@get(
    "/summaries",
    summary="Get a paginated summary of projects.",
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
    return_dto=project_schemas.ProjectSummary,
)
async def read_project_summaries(
    db: AsyncConnection,
    page: int = Parameter(1, ge=1),
    results_per_page: int = Parameter(13, le=100),
    user_sub: str | None = Parameter(default=None),
    hashtags: str | None = Parameter(default=None),
    search: str | None = Parameter(default=None),
    country: str | None = Parameter(default=None),
    status: ProjectStatus | None = Parameter(default=None),
    field_mapping_app: FieldMappingApp | None = Parameter(default=None),
) -> helper_schemas.PaginatedResponse[DbProject]:
    """Get a paginated summary of projects.

    NOTE this is a public endpoint with no auth requirements.
    """
    return await project_crud.get_paginated_projects(
        db,
        page,
        results_per_page,
        user_sub,
        hashtags,
        search,
        status,
        field_mapping_app,
        country=country,
    )


@get(
    "/categories",
    summary="Get all project categories.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def get_categories() -> dict:
    """Get api for fetching all the categories.

    This endpoint fetches all the categories from osm_fieldwork.

    ## Response
    - Returns a JSON object containing a list of categories and their respective forms.

    """
    # FIXME update to use osm-rawdata
    categories = (
        get_choices()
    )  # categories are fetched from osm_fieldwork.data_models.get_choices()
    return categories


@get(
    "/{project_id:int}",
    summary="Get a specific project by ID.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
    return_dto=project_schemas.ProjectOut,
)
async def read_project(
    project_id: int,
    current_user: ProjectUserDict,
) -> DbProject:
    """Get a specific project by ID."""
    return current_user.get("project")


@get(
    "/{project_id:int}/download",
    summary="Download the project boundary as GeoJSON.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def download_project_boundary(
    project_id: int,
    current_user: ProjectUserDict,
    db: AsyncConnection,
) -> Response:
    """Downloads the boundary of a project as a GeoJSON file."""
    project = current_user.get("project")
    geojson_bytes = json.dumps(project.outline).encode("utf-8")
    headers = {
        "Content-Disposition": f"attachment; filename={project.slug}.geojson",
        "Content-Type": "application/media",
    }
    return Response(
        content=geojson_bytes,
        headers=headers,
        status_code=status.HTTP_200_OK,
    )


@post(
    "/task-split",
    summary="Split a task into subtasks.",
    dependencies={
        "auth_user": Provide(login_required),
    },
    status_code=status.HTTP_201_CREATED,
)
async def task_split(
    data: Annotated[
        project_schemas.SplitFormData, Body(media_type=RequestEncodingType.MULTI_PART)
    ],
    no_of_buildings: int = Parameter(default=50),
) -> dict:
    """Split a task into subtasks.

    NOTE we pass a connection

    Args:
        auth_user (AuthUser): the currently logged in user.
        data (SplitFormData): The form data containing the following fields:
            project_geojson (UploadFile): The geojson (AOI) to split.
            extract_geojson (UploadFile, optional): Custom data extract geojson
                containing osm features (should be a FeatureCollection).
                If not included, an extract is generated automatically.
        no_of_buildings (int, optional): The number of buildings per subtask.
            Defaults to 50.

    Returns:
        The result of splitting the task into subtasks.
    """
    boundary_featcol = parse_geojson_file_to_featcol(await data.project_geojson.read())
    merged_boundary = merge_polygons(boundary_featcol, False)
    # Validatiing Coordinate Reference Systems
    await check_crs(merged_boundary)

    # read data extract
    parsed_extract = None
    if data.extract_geojson:
        parsed_extract = parse_geojson_file_to_featcol(
            await data.extract_geojson.read()
        )
        if parsed_extract:
            await check_crs(parsed_extract)
        else:
            log.warning("Parsed geojson file contained no geometries")

    log.debug("STARTED task splitting using provided boundary and data extract")
    # NOTE here we pass the connection string and allow area-splitter to
    # use a psycopg connection (not async)
    features = await to_thread.run_sync(
        split_by_sql,
        merged_boundary,
        settings.FMTM_DB_URL,
        no_of_buildings,
        parsed_extract,
    )
    log.debug("COMPLETE task splitting")
    return features


@post(
    "/preview-split-by-square",
    summary="Preview splitting a project AOI by square.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def preview_split_by_square(
    data: Annotated[
        project_schemas.SplitFormData, Body(media_type=RequestEncodingType.MULTI_PART)
    ],
    dimension_meters: int = Parameter(default=100),
) -> FeatureCollection:
    """Preview splitting by square.

    TODO update to use a response_model
    """
    # Validating for .geojson File.
    file_name = os.path.splitext(data.project_geojson.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Provide a valid .geojson file",
        )

    # read entire file
    boundary_featcol = parse_geojson_file_to_featcol(await data.project_geojson.read())

    # Validatiing Coordinate Reference System
    await check_crs(boundary_featcol)
    parsed_extract = None
    if data.extract_geojson:
        parsed_extract = parse_geojson_file_to_featcol(
            await data.extract_geojson.read()
        )
        if parsed_extract:
            await check_crs(parsed_extract)
        else:
            log.warning("Parsed geojson file contained no geometries")

    if len(boundary_featcol["features"]) > 0:
        boundary_featcol = merge_polygons(boundary_featcol)

    return split_by_square(
        boundary_featcol,
        settings.FMTM_DB_URL,
        meters=dimension_meters,
        osm_extract=parsed_extract,
    )


@post(
    "/generate-data-extract",
    summary="Generate a new data extract for a project AOI.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
)
async def get_data_extract(
    current_user_dict: ProjectUserDict,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
    # FIXME this is currently hardcoded but needs to be user configurable via UI
    osm_category: XLSFormType | None = XLSFormType.buildings,
    centroid: bool = False,
    geom_type: DbGeomType = DbGeomType.POLYGON,
    use_st_within: bool = True,
) -> dict[str, str | None]:
    """Get a new data extract for a given project AOI.

    TODO allow config file (YAML/JSON) upload for data extract generation
    TODO alternatively, direct to raw-data-api to generate first, then upload
    """
    boundary_geojson = parse_geojson_file_to_featcol(await data.read())
    clean_boundary_geojson = merge_polygons(boundary_geojson)
    project = current_user_dict.get("project")

    # Get extract config file from existing data_models
    geom_type = geom_type.name.lower()
    if osm_category:
        config_filename = XLSFormType(osm_category).name
        data_model = f"{data_models_path}/{config_filename}.json"

        with open(data_model, encoding="utf-8") as f:
            config_data = json.load(f)

        data_config = {
            ("polygon", False): ["ways_poly"],
            ("point", True): ["ways_poly", "nodes"],
            ("point", False): ["nodes"],
            ("polyline", False): ["ways_line"],
        }

        config_data["from"] = data_config.get((geom_type, centroid))
        if geom_type == "polyline":
            geom_type = "line"  # line is recognized as a geomtype in raw-data-api

    result = await project_crud.generate_data_extract(
        project.id,
        clean_boundary_geojson,
        geom_type,
        config_data,
        centroid,
        use_st_within,
    )

    return {"url": result.data.get("download_url")}


@get(
    "/data-extract-url",
    summary="Get or set the data extract URL for a project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
)
async def get_or_set_data_extract(
    db: AsyncConnection,
    current_user_dict: ProjectUserDict,
    project_id: int = Parameter(),
    url: str | None = Parameter(default=None),
) -> dict[str, str | None]:
    """Get or set the data extract URL for a project."""
    db_project = current_user_dict.get("project")
    fgb_url = await project_crud.get_or_set_data_extract_url(
        db,
        db_project,
        url,
    )
    return {"url": fgb_url}


@post(
    "/upload-data-extract",
    summary="Upload a data extract GeoJSON for a project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    status_code=status.HTTP_201_CREATED,
)
async def upload_data_extract(
    db: AsyncConnection,
    current_user_dict: ProjectUserDict,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> dict[str, str]:
    """Upload a data extract geojson for a project.

    The frontend has the option to upload flatgeobuf, but this must first
    be deserialised to GeoJSON before upload here.

    Note the following properties are mandatory:
    - "id"
    - "osm_id"
    - "tags"
    - "version"
    - "changeset"
    - "timestamp"

    If a property is missing, a defaults will be assigned.

    Extracts are best generated with https://export.hotosm.org for full compatibility.

    Request Body
    - 'data_extract_file' (file): File with the data extract features.

    Query Params:
    - 'project_id' (int): the project's id. Required.
    """
    project_id = current_user_dict.get("project").id

    # Validating for .geojson File.
    file_name = os.path.splitext(data.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json", ".fgb"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Provide a valid .geojson or .fgb file",
        )

    # read entire file
    extract_data = await data.read()

    fgb_url = await project_crud.upload_geojson_data_extract(
        db, project_id, extract_data
    )
    return {"url": fgb_url}


@post(
    "/{project_id:int}/additional-entity",
    summary="Add an additional Entity list for the project in ODK.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    status_code=status.HTTP_200_OK,
)
async def add_additional_entity_list(
    project_id: int,
    current_user_dict: ProjectUserDict,
    geojson: UploadFile,
) -> None:
    """Add an additional Entity list for the project in ODK.

    Note that the Entity list will be named from the filename
    of the GeoJSON uploaded.
    """
    project = current_user_dict.get("project")
    project_odk_id = project.external_project_id
    # ODK credentials not stored on project, use None to fall back to env vars
    project_odk_creds = None
    # NOTE the Entity name is extracted from the filename (without extension)
    entity_name = Path(geojson.filename).stem

    # Parse geojson
    featcol = parse_geojson_file_to_featcol(await geojson.read())
    properties = list(featcol.get("features")[0].get("properties").keys())
    entities_list = await central_crud.task_geojson_dict_to_entity_values(featcol, True)
    dataset_name = entity_name.replace(" ", "_")

    await central_crud.create_entity_list(
        project_odk_creds,
        project_odk_id,
        properties=properties,
        dataset_name=dataset_name,
        entities_list=entities_list,
    )

    return None


@post(
    "/{project_id:int}/generate-project-data",
    summary="Generate additional project data and files.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    status_code=status.HTTP_200_OK,
)
async def generate_files(
    project_id: int,
    db: AsyncConnection,
    current_user_dict: ProjectUserDict,
    combined_features_count: int = Parameter(0),
) -> None:
    """Generate additional content to initialise the project.

    Boundary, ODK Central forms, QR codes, etc.

    Accepts a project ID and an uploaded file as inputs.
    The generated files are associated with the project ID and stored in the database.
    This api generates odk appuser tokens, forms. This api also creates an app user for
    each task and provides the required roles.
    Some of the other functionality of this api includes converting a xls file
    provided by the user to the xform, generates osm data extracts and uploads
    it to the form.
    """
    project = current_user_dict.get("project")
    project_id = project.id
    log.debug(f"Generating additional files for project: {project.id}")
    warning_message = None

    # Handle QField separately
    if project.field_mapping_app == FieldMappingApp.QFIELD:
        qfield_url = await create_qfield_project(db, project)
        # Provide URL for qfieldcloud project dashboard
        return {"url": qfield_url}

    # Run in background for ODK project with lots of features
    elif combined_features_count > 10000:
        # For many features, we still run this synchronously in Litestar to simplify
        await project_crud.generate_project_files(db, project_id)
        warning_message = "There are lots of features to process. Please be patient."

    else:
        success = await project_crud.generate_project_files(
            db,
            project_id,
        )

        if not success:
            return Response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=(
                    f"Failed project ({project_id}) creation. "
                    "Please contact the server admin."
                ).encode(),
                media_type="application/json",
            )

    # Update the XLSForm if using ODK Collect to add task id choice filter
    if project.field_mapping_app == FieldMappingApp.ODK:
        log.info("Appending task_filter choices to XLSForm for ODK Collect project")
        existing_xlsform = BytesIO(project.xlsform_content)

        # Get task IDs from ODK Central task_boundaries dataset
        task_ids = []
        if project.external_project_id:
            try:
                # ODK credentials not stored on project, use None to fall back to env vars
                project_odk_creds = None
                from app.central import central_deps

                async with central_deps.get_odk_dataset(
                    project_odk_creds
                ) as odk_central:
                    # Fetch task boundaries from ODK
                    entity_data = await odk_central.getEntityData(
                        project.external_project_id,
                        "task_boundaries",
                        include_metadata=False,
                    )

                    if entity_data and isinstance(entity_data, list):
                        # Extract task IDs from entities
                        for entity in entity_data:
                            task_id = entity.get("task_id")
                            if task_id:
                                try:
                                    task_ids.append(int(task_id))
                                except (ValueError, TypeError):
                                    pass
                        # If no task_id in properties, use index
                        if not task_ids:
                            task_ids = list(range(1, len(entity_data) + 1))
            except Exception as e:
                log.warning(
                    f"Could not fetch task boundaries from ODK for project {project.id}: {e}"
                )

        if not task_ids:
            msg = "Project has no task boundaries in ODK Central. Please upload task boundaries first."
            log.error(msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        log.debug(f"Found {len(task_ids)} task boundaries for project ID {project.id}")
        new_xlsform = await append_task_id_choices(existing_xlsform, task_ids)

        # Update in both db + ODK Central
        await central_crud.update_project_xlsform(
            db,
            project,
            new_xlsform,
            project.odk_form_id,
        )

    if warning_message:
        return {"message": warning_message}
    return {}


def _get_local_odk_url() -> str:
    """Return local ODK proxy URL: http://odk.<domain>:<port>."""
    domain = getattr(settings, "FMTM_DOMAIN", "fmtm.localhost")
    port = getattr(settings, "FMTM_DEV_PORT", "7050")
    domain = domain.replace("http://", "").replace("https://", "")
    return f"http://odk.{domain}:{port}".rstrip(":")


async def _store_odk_project_url(db: AsyncConnection, project: DbProject) -> None:
    """Store the external ODK project URL.

    Uses local proxy URL if credentials indicate local Docker setup (central:8383),
    otherwise uses the custom ODK Central URL from project/org credentials.
    """
    if project.field_mapping_app != FieldMappingApp.ODK:
        return

    try:
        enriched = await DbProject.one(db, project.id, minimal=False)
    except Exception:
        enriched = project

    creds = getattr(enriched, "odk_credentials", None)
    odk_url = getattr(creds, "external_project_instance_url", None) if creds else None

    if not odk_url:
        return

    if "central:8383" in odk_url:
        odk_url = _get_local_odk_url()

    # Append project ID to URL
    odk_url = odk_url.rstrip("/")
    external_project_id = getattr(enriched, "external_project_id", None)
    if external_project_id and "/projects/" not in odk_url:
        odk_url = f"{odk_url}/projects/{external_project_id}"

    try:
        await DbProject.update(
            db,
            project.id,
            ProjectUpdate(
                external_project_instance_url=odk_url,
                external_project_id=external_project_id,
            ),
        )
        log.debug(
            "Stored ODK project external reference for project "
            f"{project.id}: id={external_project_id}, url={odk_url}"
        )
    except Exception as exc:
        log.warning(
            "Failed to store ODK project external reference for project "
            f"{project.id}: {exc}"
        )


@post(
    "/{project_id:int}/upload-task-boundaries",
    summary="Upload project task boundaries as GeoJSON.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_task_boundaries(
    project_id: int,
    db: AsyncConnection,
    current_user_dict: ProjectUserDict,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
) -> dict[str, str]:
    """Set project task boundaries using split GeoJSON from frontend.

    Each polygon in the uploaded geojson are made into single task.

    Required Parameters:
        project_id (id): ID for associated project.
        task_geojson (UploadFile): Multi-polygon GeoJSON file.

    Returns:
        JSONResponse: JSON containing success message.
    """
    project = current_user_dict.get("project")
    project_id = project.id
    tasks_featcol = parse_geojson_file_to_featcol(await data.read())
    await check_crs(tasks_featcol)

    # Send task boundaries directly to ODK/QField, not stored in database
    if project.field_mapping_app == FieldMappingApp.ODK:
        # Convert task boundaries to entities and upload to ODK Central
        project_odk_id = project.external_project_id
        if not project_odk_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project must have an ODK Central project ID. Please create the project in ODK Central first.",
            )

        # Convert task boundaries to entity format
        # Each task boundary becomes an entity in ODK
        task_entities = []
        for idx, feature in enumerate(tasks_featcol.get("features", [])):
            if feature.get("geometry"):
                entity_dict = await central_crud.feature_geojson_to_entity_dict(
                    feature, additional_features=True
                )
                # Update label to indicate it's a task boundary
                entity_dict["label"] = f"Task {idx + 1}"
                # Add task_id to properties
                if "data" in entity_dict:
                    entity_dict["data"]["task_id"] = str(idx + 1)
                task_entities.append(entity_dict)

        # Create entity list for task boundaries in ODK
        # ODK credentials not stored on project, use None to fall back to env vars
        project_odk_creds = None
        try:
            # Check if dataset already exists, if so delete and recreate
            from app.central import central_deps

            async with central_deps.get_odk_dataset(project_odk_creds) as odk_central:
                datasets = await odk_central.listDatasets(project_odk_id)
                if any(ds.get("name") == "task_boundaries" for ds in datasets):
                    log.info("Task boundaries dataset already exists, will be replaced")
        except Exception as e:
            log.warning(f"Could not check existing datasets: {e}")

        await central_crud.create_entity_list(
            project_odk_creds,
            project_odk_id,
            properties=["geometry", "task_id"],
            dataset_name="task_boundaries",
            entities_list=task_entities,
        )
        log.info(
            f"Uploaded {len(task_entities)} task boundaries to ODK Central for project {project_id}"
        )
    elif project.field_mapping_app == FieldMappingApp.QFIELD:
        # For QField, boundaries are written to tasks.geojson during project generation
        # Store temporarily in a temp table for use during generation
        # They will be written to tasks.geojson file and not stored permanently
        log.info("Storing task boundaries temporarily for QField project generation")

        # Create temporary table for task boundaries (cleaned up after project generation)
        async with db.cursor() as cur:
            # Drop existing temp table if it exists
            await cur.execute(f"""
                DROP TABLE IF EXISTS temp_task_boundaries_{project_id} CASCADE;
            """)

            # Create temp table
            await cur.execute(f"""
                CREATE TEMP TABLE temp_task_boundaries_{project_id} (
                    task_index INTEGER,
                    outline GEOMETRY(POLYGON, 4326)
                );
            """)

            # Insert task boundaries
            for idx, feature in enumerate(tasks_featcol.get("features", [])):
                if feature.get("geometry"):
                    geom_json = json.dumps(feature["geometry"])
                    await cur.execute(
                        f"""
                        INSERT INTO temp_task_boundaries_{project_id} (task_index, outline)
                        VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                        """,
                        (idx + 1, geom_json),
                    )

            await db.commit()
            log.info(
                f"Stored {len(tasks_featcol.get('features', []))} task boundaries in temp table for QField project {project_id}"
            )

    return {"message": "success"}


@patch(
    "/{project_id:int}",
    summary="Partially update an existing project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    return_dto=project_schemas.ProjectOut,
)
async def update_project(
    data: project_schemas.ProjectUpdate,
    project_id: int,
    current_user_dict: ProjectUserDict,
    db: AsyncConnection,
) -> DbProject:
    """Partial update an existing project."""
    # NOTE this does not including updating the ODK project name
    # If password is None but URL/username are provided, preserve existing encrypted password
    project = current_user_dict.get("project")
    if (
        (data.external_project_instance_url or data.external_project_username)
        and not data.external_project_password
        and project.external_project_password_encrypted
    ):
        # Password is None, so set password_encrypted to preserve existing encrypted password
        # This allows the validation to pass and the password to be preserved
        data.password_encrypted = project.external_project_password_encrypted

    return await DbProject.update(db, project.id, data)


@post(
    "/stub",
    summary="Create a project stub in the local database.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    return_dto=project_schemas.ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_stub_project(
    db: AsyncConnection,
    auth_user: AuthUser,
    data: project_schemas.StubProjectIn,
) -> DbProject:
    """Create a project in the local database."""
    if hasattr(data, "merge"):
        delattr(data, "merge")  # Remove merge field as it is not in database
    data.status = ProjectStatus.DRAFT

    log.info(
        f"User {auth_user.username} attempting creation of project {data.project_name}"
    )

    # Check for duplicate project name before creating
    exists = await project_deps.project_name_does_not_already_exist(
        db, data.project_name
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with name '{data.project_name}' already exists.",
        )

    # Get the location_str via reverse geocode
    async with AsyncNearestCity(db) as geocoder:
        centroid = await polygon_to_centroid(data.outline.model_dump())
        latitude, longitude = centroid.y, centroid.x
        location = await geocoder.query(latitude, longitude)
        # Convert to two letter country code --> full name
        country_full_name = (
            countries.get(location.country, location.country) if location else None
        )
        data.location_str = f"{location.city},{country_full_name}" if location else None

    # Create the project in the Field-TM DB
    data.created_by_sub = auth_user.sub
    try:
        project = await DbProject.create(db, data)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error posting to /stub: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project creation failed.",
        ) from e

    return project


@delete(
    "/{project_id:int}",
    summary="Delete a project from ODK Central and the local database.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    db: AsyncConnection,
    current_user: DbUser,
) -> None:
    """Delete a project from both ODK Central and the local database."""
    project = await project_deps.get_project_by_id(db, project_id)

    log.info(
        f"User {current_user.username} attempting deletion of project {project.id}"
    )

    # Handle QField projects separately
    if project.field_mapping_app == FieldMappingApp.QFIELD:
        log.info(f"Deleting QFieldCloud project for FieldTM project ({project.id})")
        await delete_qfield_project(db, project.id)
    else:
        # Delete ODK Central project
        log.info(f"Deleting ODK Central project for FieldTM project ({project.id})")
        # Use None for credentials to fall back to environment variables
        await central_crud.delete_odk_project(project.external_project_id, None)

    # Delete Field-TM project
    await DbProject.delete(db, project.id)

    log.info(f"Deletion of project {project.id} successful")
    return None


@patch(
    "",
    summary="Create project in ODK Central and update the local stub project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
    return_dto=project_schemas.ProjectOut,
)
async def create_project(
    db: AsyncConnection,
    current_user: ProjectUserDict,
    data: project_schemas.ProjectIn,
    project_id: int = Parameter(),
) -> DbProject:
    """Create a project in ODK Central and update the local stub project."""
    project_id = current_user.get("project").id
    project = await DbProject.one(db, project_id)

    if data.project_name:
        # Check for duplicate project name before creating
        exists = await project_deps.project_name_does_not_already_exist(
            db, data.project_name
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with name '{data.project_name}' already exists.",
            )

    odk_creds_decrypted = data.odk_credentials

    # Create project in ODK Central using a background thread
    odkproject = await to_thread.run_sync(
        central_crud.create_odk_project,
        project.project_name,
        odk_creds_decrypted,
    )
    data.external_project_id = odkproject["id"]

    try:
        project = await DbProject.update(db, project.id, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project update failed.",
        ) from e

    await _store_odk_project_url(db, project)

    return project


project_router = Router(
    path="/projects",
    tags=["projects"],
    route_handlers=[
        read_projects,
        get_tasks_near_me,
        read_project_summaries,
        get_categories,
        read_project,
        download_project_boundary,
        task_split,
        preview_split_by_square,
        get_data_extract,
        get_or_set_data_extract,
        upload_data_extract,
        add_additional_entity_list,
        generate_files,
        upload_project_task_boundaries,
        update_project,
        create_stub_project,
        delete_project,
        create_project,
    ],
)
