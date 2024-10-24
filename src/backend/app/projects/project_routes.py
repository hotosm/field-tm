# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Endpoints for FMTM projects."""

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID

import requests
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fmtm_splitter.splitter import split_by_sql, split_by_square
from geojson_pydantic import Feature, FeatureCollection
from loguru import logger as log
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.make_data_extract import getChoices
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import Connection

from app.auth.auth_schemas import AuthUser, OrgUserDict, ProjectUserDict
from app.auth.osm import login_required
from app.auth.roles import mapper, org_admin, project_manager
from app.central import central_crud, central_deps, central_schemas
from app.config import settings
from app.db import db_models
from app.db.database import db_conn
from app.db.enums import (
    TILES_FORMATS,
    TILES_SOURCE,
    HTTPStatus,
    ProjectRole,
    XLSFormType,
)
from app.db.models import DbBackgroundTask, DbBasemap, DbProject, DbTask, DbUserRole
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    flatgeobuf_to_featcol,
    merge_polygons,
    parse_geojson_file_to_featcol,
    split_geojson_by_task_areas,
    wkb_geom_to_feature,
)
from app.organisations import organisation_deps
from app.projects import project_crud, project_deps, project_schemas
from app.s3 import delete_all_objs_under_prefix

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/features", response_model=FeatureCollection)
async def read_projects_to_featcol(
    db: Annotated[Connection, Depends(db_conn)],
    bbox: Optional[str] = None,
):
    """Return all projects as a single FeatureCollection."""
    return await project_crud.get_projects_featcol(db, bbox)


@router.get("/", response_model=list[project_schemas.ProjectOut])
async def read_projects(
    db: Annotated[Connection, Depends(db_conn)],
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    """Return all projects."""
    projects = await DbProject.all(db, skip, limit, user_id)
    return projects


@router.post("/me", response_model=list[DbProject])
async def get_projects_for_user(user_id: int):
    """Get all projects the user is author of.

    TODO to be implemented in future.
    """
    raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)


@router.post("/near_me", response_model=list[project_schemas.ProjectSummary])
async def get_tasks_near_me(lat: float, long: float, user_id: int = None):
    """Get projects near me.

    TODO to be implemented in future.
    """
    raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)


@router.get("/summaries", response_model=project_schemas.PaginatedProjectSummaries)
async def read_project_summaries(
    db: Annotated[Connection, Depends(db_conn)],
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    user_id: Optional[int] = None,
    hashtags: Optional[str] = None,
):
    """Get a paginated summary of projects."""
    return await project_crud.get_paginated_projects(
        db, page, results_per_page, user_id, hashtags
    )


@router.get(
    "/search",
    response_model=project_schemas.PaginatedProjectSummaries,
)
async def search_project(
    db: Annotated[Connection, Depends(db_conn)],
    search: str,
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    user_id: Optional[int] = None,
    hashtags: Optional[str] = None,
):
    """Search projects by string, hashtag, or other criteria."""
    return await project_crud.get_paginated_projects(
        db, page, results_per_page, user_id, hashtags, search
    )


@router.get(
    "/{project_id}/entities", response_model=central_schemas.EntityFeatureCollection
)
async def get_odk_entities_geojson(
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
    minimal: bool = False,
):
    """Get the ODK entities for a project in GeoJSON format.

    NOTE This endpoint should not not be used to display the feature geometries.
    Rendering multiple GeoJSONs if inefficient.
    This is done by the flatgeobuf by filtering the task area bbox.
    """
    return await central_crud.get_entities_geojson(
        project.odk_credentials,
        project.odkid,
        minimal=minimal,
    )


@router.get(
    "/{project_id}/entities/statuses",
    response_model=list[central_schemas.EntityMappingStatus],
)
async def get_odk_entities_mapping_statuses(
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entities mapping statuses, i.e. in progress or complete."""
    return await central_crud.get_entities_data(
        project.odk_credentials,
        project.odkid,
    )


@router.get(
    "/{project_id}/entities/osm-ids",
    response_model=list[central_schemas.EntityOsmID],
)
async def get_odk_entities_osm_ids(
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entities linked OSM IDs.

    This endpoint is required as we cannot modify the data extract fields
    when generated via raw-data-api.
    We need to link Entity UUIDs to OSM/Feature IDs.
    """
    return await central_crud.get_entities_data(
        project.odk_credentials,
        project.odkid,
        fields="osm_id",
    )


@router.get(
    "/{project_id}/entities/task-ids",
    response_model=list[central_schemas.EntityTaskID],
)
async def get_odk_entities_task_ids(
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entities linked FMTM Task IDs."""
    return await central_crud.get_entities_data(
        project.odk_credentials,
        project.odkid,
        fields="task_id",
    )


@router.get(
    "/{project_id}/entity/status",
    response_model=central_schemas.EntityMappingStatus,
)
async def get_odk_entity_mapping_status(
    entity_id: str,
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entity mapping status, i.e. in progress or complete."""
    return await central_crud.get_entity_mapping_status(
        project.odk_credentials,
        project.odkid,
        entity_id,
    )


@router.post(
    "/{project_id}/entity/status",
    response_model=central_schemas.EntityMappingStatus,
)
async def set_odk_entities_mapping_status(
    entity_details: central_schemas.EntityMappingStatusIn,
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Set the ODK entities mapping status, i.e. in progress or complete.

    entity_details must be a JSON body with params:
    {
        "entity_id": "string",
        "label": "Task <TASK_ID> Feature <FEATURE_ID>",
        "status": 0
    }
    """
    return await central_crud.update_entity_mapping_status(
        project.odk_credentials,
        project.odkid,
        entity_details.entity_id,
        entity_details.label,
        entity_details.status,
    )


@router.get(
    "/{project_id}/tiles/",
    response_model=list[project_schemas.BasemapOut],
)
async def tiles_list(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Returns the list of tiles for a project.

    Parameters:
        project_id: int
        db (Connection): The database connection.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: List of generated tiles for a project.
    """
    return await DbBasemap.all(db, project_user.get("project").id)


@router.get(
    "/{project_id}/tiles/{tile_id}/",
    response_model=project_schemas.BasemapOut,
)
async def download_tiles(
    tile_id: UUID,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Download the basemap tile archive for a project."""
    log.debug("Getting basemap path from DB")
    try:
        db_basemap = await DbBasemap.one(db, tile_id)
    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    log.info(f"User requested download for tiles: {db_basemap.url}")

    project = project_user.get("project")
    filename = Path(db_basemap.url).name.replace(f"{project.id}_", f"{project.slug}_")
    log.debug(f"Sending tile archive to user: {filename}")

    if db_basemap.format == "mbtiles":
        mimetype = "application/vnd.mapbox-vector-tile"
    elif db_basemap.format == "pmtiles":
        mimetype = "application/vnd.pmtiles"
    else:
        mimetype = "application/vnd.sqlite3"

    return FileResponse(
        db_basemap.url,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": mimetype,
        },
    )


@router.get("/{project_id}/tiles-generate")
async def generate_project_basemap(
    background_tasks: BackgroundTasks,
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    source: str = Query(
        ..., description="Select a source for tiles", enum=TILES_SOURCE
    ),
    format: str = Query(
        "mbtiles", description="Select an output format", enum=TILES_FORMATS
    ),
    tms: str = Query(
        None,
        description="Provide a custom TMS URL, optional",
    ),
):
    """Returns basemap tiles for a project."""
    # Create task in db and return uuid
    log.debug(
        "Creating generate_project_basemap background task "
        f"for project ID: {project_id}"
    )
    background_task_id = await DbBackgroundTask.create(
        db,
        project_schemas.BackgroundTaskIn(
            project_id=project_id,
            name="generate_basemap",
        ),
    )

    # # FIXME delete this
    # project_crud.generate_project_basemap(
    #     db,
    #     project_id,
    #     background_task_id,
    #     source,
    #     format,
    #     tms
    # )

    background_tasks.add_task(
        project_crud.generate_project_basemap,
        db,
        project_id,
        background_task_id,
        source,
        format,
        tms,
    )

    return {"Message": "Tile generation started"}


@router.get("/{id}", response_model=project_schemas.ProjectOut)
async def read_project(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get a specific project by ID."""
    return project_user.get("project")


@router.delete("/{project_id}")
async def delete_project(
    db: Annotated[Connection, Depends(db_conn)],
    project: Annotated[db_models.DbProject, Depends(project_deps.get_project)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
):
    """Delete a project from both ODK Central and the local database."""
    log.info(
        f"User {org_user_dict.get('user').username} attempting "
        f"deletion of project {project.id}"
    )
    # Delete ODK Central project
    await central_crud.delete_odk_project(project.odkid, project.odk_credentials)
    # Delete S3 resources
    await delete_all_objs_under_prefix(
        settings.S3_BUCKET_NAME, f"/{project.organisation_id}/{project.id}/"
    )
    await project_crud.delete_fmtm_s3_objects(project)
    # Delete FMTM project
    await DbProject.delete(db, project.id)

    log.info(f"Deletion of project {project.id} successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/{project_id}/upload-task-boundaries")
async def upload_project_task_boundaries(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    task_geojson: UploadFile = File(...),
):
    """Set project task boundaries using split GeoJSON from frontend.

    Each polygon in the uploaded geojson are made into single task.

    Required Parameters:
        project_id (id): ID for associated project.
        task_geojson (UploadFile): Multi-polygon GeoJSON file.

    Returns:
        JSONResponse: JSON containing success message.
    """
    tasks_featcol = parse_geojson_file_to_featcol(await task_geojson.read())
    await check_crs(tasks_featcol)
    # We only want to allow polygon geometries
    featcol_single_geom_type = featcol_keep_single_geom_type(
        tasks_featcol,
        geom_type="Polygon",
    )
    success = await DbTask.create(db, project_id, featcol_single_geom_type)
    if not success:
        return JSONResponse(content={"message": "failure"})
    return JSONResponse(content={"message": "success"})


@router.post("/task-split")
async def task_split(
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    no_of_buildings: int = Form(50),
):
    """Split a task into subtasks.

    NOTE we pass a connection

    Args:
        project_geojson (UploadFile): The geojson (AOI) to split.
        extract_geojson (UploadFile, optional): Custom data extract geojson
            containing osm features (should be a FeatureCollection).
            If not included, an extract is generated automatically.
        no_of_buildings (int, optional): The number of buildings per subtask.
            Defaults to 50.

    Returns:
        The result of splitting the task into subtasks.
    """
    boundary_featcol = parse_geojson_file_to_featcol(await project_geojson.read())
    merged_boundary = merge_polygons(boundary_featcol, False)
    # Validatiing Coordinate Reference Systems
    await check_crs(merged_boundary)

    # read data extract
    parsed_extract = None
    if extract_geojson:
        parsed_extract = parse_geojson_file_to_featcol(await extract_geojson.read())
        if parsed_extract:
            await check_crs(parsed_extract)
        else:
            log.warning("Parsed geojson file contained no geometries")

    log.debug("STARTED task splitting using provided boundary and data extract")
    # NOTE here we pass the connection string and allow fmtm-splitter to
    # a use psycopg2 connection (not async)
    features = await run_in_threadpool(
        lambda: split_by_sql(
            merged_boundary,
            settings.FMTM_DB_URL.unicode_string(),
            num_buildings=no_of_buildings,
            osm_extract=parsed_extract,
        )
    )
    log.debug("COMPLETE task splitting")
    return features


@router.post("/validate-form")
async def validate_form(
    xlsform: BytesIO = Depends(central_deps.read_xlsform),
    debug: bool = False,
):
    """Basic validity check for uploaded XLSForm.

    Parses the form using ODK pyxform to check that it is valid.

    If the `debug` param is used, the form is returned for inspection.
    NOTE that this debug form has additional fields appended and should
        not be used for FMTM project creation.
    """
    if debug:
        xform_id, updated_form = await central_crud.append_fields_to_user_xlsform(
            xlsform,
        )
        return StreamingResponse(
            updated_form,
            media_type=(
                "application/vnd.openxmlformats-" "officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f"attachment; filename={xform_id}.xlsx"},
        )
    else:
        await central_crud.validate_and_update_user_xlsform(
            xlsform,
        )
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": "Your form is valid"},
        )


@router.post("/{project_id}/generate-project-data")
async def generate_files(
    background_tasks: BackgroundTasks,
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    xlsform_upload: Annotated[
        Optional[BytesIO], Depends(central_deps.read_optional_xlsform)
    ],
    additional_entities: list[str] = None,
):
    """Generate additional content to initialise the project.

    Boundary, ODK Central forms, QR codes, etc.

    Accepts a project ID, category, custom form flag, and an uploaded file as inputs.
    The generated files are associated with the project ID and stored in the database.
    This api generates odk appuser tokens, forms. This api also creates an app user for
    each task and provides the required roles.
    Some of the other functionality of this api includes converting a xls file
    provided by the user to the xform, generates osm data extracts and uploads
    it to the form.

    TODO this requires org_admin permission.
    We should refactor to create a project as a stub.
    Then move most logic to another endpoint to edit an existing project.
    The edit project endpoint can have project manager permissions.

    Args:
        background_tasks (BackgroundTasks): FastAPI bg tasks, provided automatically.
        xlsform_upload (UploadFile, optional): A custom XLSForm to use in the project.
            A file should be provided if user wants to upload a custom xls form.
        additional_entities (list[str]): If additional Entity lists need to be
            created (i.e. the project form references multiple geometries).
        db (Connection): The database connection.
        project_user_dict (ProjectUserDict): Project admin role.

    Returns:
        json (JSONResponse): A success message containing the project ID.
    """
    project = project_user_dict.get("project")
    project_id = project.id
    form_category = project.xform_category

    log.debug(f"Generating additional files for project: {project.id}")

    if xlsform_upload:
        log.debug("User provided custom XLSForm")

        # Validate uploaded form
        await central_crud.validate_and_update_user_xlsform(
            xlsform=xlsform_upload,
            form_category=form_category,
            additional_entities=additional_entities,
        )
        xlsform = xlsform_upload

    else:
        log.debug(f"Using default XLSForm for category: '{form_category}'")

        form_filename = XLSFormType(form_category).name
        xlsform_path = f"{xlsforms_path}/{form_filename}.xls"
        with open(xlsform_path, "rb") as f:
            xlsform = BytesIO(f.read())

    xform_id, project_xlsform = await central_crud.append_fields_to_user_xlsform(
        xlsform=xlsform,
        form_category=form_category,
        additional_entities=additional_entities,
    )
    # Write XLS form content to db
    xlsform_bytes = project_xlsform.getvalue()
    if len(xlsform_bytes) == 0 or not xform_id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="There was an error modifying the XLSForm!",
        )
    log.debug(f"Setting project XLSForm db data for xFormId: {xform_id}")
    sql = """
        UPDATE public.projects
        SET
            odk_form_id = %(odk_form_id)s,
            xlsform_content = %(xlsform_content)s
        WHERE id = %(project_id)s;
    """
    async with db.cursor() as cur:
        await cur.execute(
            sql,
            {
                "project_id": project_id,
                "odk_form_id": xform_id,
                "xlsform_content": xlsform_bytes,
            },
        )

    # Create task in db and return uuid
    log.debug(f"Creating export background task for project ID: {project_id}")
    background_task_id = await DbBackgroundTask.create(
        db,
        project_schemas.BackgroundTaskIn(
            project_id=project_id,
            name="generate_project",
        ),
    )

    log.debug(f"Submitting {background_task_id} to background tasks stack")
    background_tasks.add_task(
        project_crud.generate_project_files,
        db,
        project_id,
        background_task_id,
    )

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"Message": f"{project.id}", "task_id": f"{background_task_id}"},
    )


@router.post("/{project_id}/additional-entity")
async def add_additional_entity_list(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    geojson: UploadFile = File(...),
):
    """Add an additional Entity list for the project in ODK.

    Note that the Entity list will be named from the filename
    of the GeoJSON uploaded.
    """
    project = project_user_dict.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    project_odk_creds = project.odk_credentials
    # NOTE the Entity name is extracted from the filename (without extension)
    entity_name = Path(geojson.filename).stem

    # Parse geojson + divide by task
    # (not technically required, but also appends properties in correct format)
    featcol = parse_geojson_file_to_featcol(await geojson.read())
    feature_split_by_task = await split_geojson_by_task_areas(db, featcol, project_id)
    entities_list = await central_crud.task_geojson_dict_to_entity_values(
        feature_split_by_task
    )

    await central_crud.create_entity_list(
        project_odk_creds,
        project_odk_id,
        dataset_name=entity_name,
        entities_list=entities_list,
    )

    return Response(status_code=HTTPStatus.OK)


@router.get("/categories/")
async def get_categories(current_user: Annotated[AuthUser, Depends(login_required)]):
    """Get api for fetching all the categories.

    This endpoint fetches all the categories from osm_fieldwork.

    ## Response
    - Returns a JSON object containing a list of categories and their respoective forms.

    """
    # FIXME update to use osm-rawdata
    categories = (
        getChoices()
    )  # categories are fetched from osm_fieldwork.make_data_extracts.getChoices()
    return categories


@router.post("/preview-split-by-square/", response_model=FeatureCollection)
async def preview_split_by_square(
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    dimension_meters: int = Form(100),
):
    """Preview splitting by square.

    TODO update to use a response_model
    """
    # Validating for .geojson File.
    file_name = os.path.splitext(project_geojson.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="Provide a valid .geojson file",
        )

    # read entire file
    boundary_featcol = parse_geojson_file_to_featcol(await project_geojson.read())

    # Validatiing Coordinate Reference System
    await check_crs(boundary_featcol)
    parsed_extract = None
    if extract_geojson:
        parsed_extract = parse_geojson_file_to_featcol(await extract_geojson.read())
        if parsed_extract:
            await check_crs(parsed_extract)
        else:
            log.warning("Parsed geojson file contained no geometries")

    if len(boundary_featcol["features"]) == 0:
        boundary_featcol = merge_polygons(boundary_featcol)

    return split_by_square(
        boundary_featcol,
        osm_extract=parsed_extract,
        meters=dimension_meters,
    )


@router.post("/generate-data-extract/")
async def get_data_extract(
    # config_file: Optional[str] = Form(None),
    current_user: Annotated[AuthUser, Depends(login_required)],
    geojson_file: UploadFile = File(...),
    form_category: Optional[XLSFormType] = Form(None),
):
    """Get a new data extract for a given project AOI.

    TODO allow config file (YAML/JSON) upload for data extract generation
    TODO alternatively, direct to raw-data-api to generate first, then upload
    """
    boundary_geojson = json.loads(await geojson_file.read())

    # Get extract config file from existing data_models
    if form_category:
        config_filename = XLSFormType(form_category).name
        data_model = f"{data_models_path}/{config_filename}.yaml"
        with open(data_model, "rb") as data_model_yaml:
            extract_config = BytesIO(data_model_yaml.read())
    else:
        extract_config = None

    fgb_url = await project_crud.generate_data_extract(
        boundary_geojson,
        extract_config,
    )

    return JSONResponse(status_code=HTTPStatus.OK, content={"url": fgb_url})


@router.get("/data-extract-url/")
async def get_or_set_data_extract(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    url: Optional[str] = None,
):
    """Get or set the data extract URL for a project."""
    db_project = project_user_dict.get("project")
    fgb_url = await project_crud.get_or_set_data_extract_url(
        db,
        db_project,
        url,
    )
    return JSONResponse(status_code=HTTPStatus.OK, content={"url": fgb_url})


@router.post("/upload-custom-extract/")
async def upload_custom_extract(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    custom_extract_file: UploadFile = File(...),
):
    """Upload a custom data extract geojson for a project.

    Extract can be in geojson for flatgeobuf format.

    Note the following properties are mandatory:
    - "id"
    - "osm_id"
    - "tags"
    - "version"
    - "changeset"
    - "timestamp"

    Extracts are best generated with https://export.hotosm.org for full compatibility.

    Request Body
    - 'custom_extract_file' (file): File with the data extract features.

    Query Params:
    - 'project_id' (int): the project's id. Required.
    """
    project_id = project_user_dict.get("project").id

    # Validating for .geojson File.
    file_name = os.path.splitext(custom_extract_file.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json", ".fgb"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST, detail="Provide a valid .geojson or .fgb file"
        )

    # read entire file
    extract_data = await custom_extract_file.read()

    if file_ext == ".fgb":
        fgb_url = await project_crud.upload_custom_fgb_extract(
            db, project_id, extract_data
        )
    else:
        fgb_url = await project_crud.upload_custom_geojson_extract(
            db, project_id, extract_data
        )
    return JSONResponse(status_code=HTTPStatus.OK, content={"url": fgb_url})


@router.get("/download-form/{project_id}/")
async def download_form(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Download the XLSForm for a project."""
    project = project_user.get("project")

    headers = {
        "Content-Disposition": f"attachment; filename={project.id}_xlsform.xlsx",
        "Content-Type": "application/media",
    }
    return Response(content=project.xlsform_content, headers=headers)


@router.post("/update-form")
async def update_project_form(
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    xform_id: str = Form(...),
    category: XLSFormType = Form(...),
) -> DbProject:
    """Update the XForm data in ODK Central.

    Also updates the category and custom XLSForm data in the database.
    """
    project = project_user_dict["project"]

    # TODO we currently do nothing with the provided category
    # TODO allowing for category updates is disabled due to complexity
    # TODO as it would mean also updating data extracts,
    # TODO so perhaps we just remove this?
    # form_filename = XLSFormType(project.xform_category).name
    # xlsform_path = Path(f"{xlsforms_path}/{form_filename}.xls")
    # file_ext = xlsform_path.suffix.lower()
    # with open(xlsform_path, "rb") as f:
    #     new_xform_data = BytesIO(f.read())

    # Update ODK Central form data
    await central_crud.update_project_xform(
        xform_id,
        project.odkid,
        xlsform,
        category,
        project.odk_credentials,
    )

    sql = """
        INSERT INTO projects
            (xlsform_content)
        VALUES
            (%(xls_data)s)
        RETURNING id, hashtags;
    """
    async with db.cursor() as cur:
        await cur.execute(sql, {"xls_data": xlsform.getvalue()})

    return project


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
) -> StreamingResponse:
    """Downloads the boundary of a project as a GeoJSON file."""
    project = project_user.get("project")
    geojson = wkb_geom_to_feature(project.outline, id=project.id)
    return StreamingResponse(
        BytesIO(json.dumps(geojson).encode("utf-8")),
        headers={
            "Content-Disposition": (f"attachment; filename={project.slug}.geojson"),
            "Content-Type": "application/media",
        },
    )


@router.get("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Downloads the boundary of the tasks for a project as a GeoJSON file.

    Args:
        project_id (int): Project ID path param.
        db (Connection): The database connection.
        project_user (ProjectUserDict): Check if user has MAPPER permission.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    project_id = project_user.get("project").id
    out = await project_crud.get_task_geometry(db, project_id)

    headers = {
        "Content-Disposition": "attachment; filename=project_outline.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=out, headers=headers)


@router.get("/features/download/")
async def download_features(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    task_id: Optional[int] = None,
):
    """Downloads the features of a project as a GeoJSON file.

    Can generate a geojson for the entire project, or specific task areas.
    """
    project = project_user.get("project")
    feature_collection = await project_crud.get_project_features_geojson(
        db, project, task_id
    )

    headers = {
        "Content-Disposition": (
            f"attachment; filename=fmtm_project_{project.id}_features.geojson"
        ),
        "Content-Type": "application/media",
    }

    return Response(content=json.dumps(feature_collection), headers=headers)


@router.get("/convert-fgb-to-geojson/")
async def convert_fgb_to_geojson(
    url: str,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Convert flatgeobuf to GeoJSON format, extracting GeometryCollection.

    Helper endpoint to test data extracts during project creation.
    Required as the flatgeobuf files wrapped in GeometryCollection
    cannot be read in QGIS or other tools.

    Args:
        url (str): URL to the flatgeobuf file.
        db (Connection): The database connection.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    with requests.get(url) as response:
        if not response.ok:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Download failed for data extract",
            )
        data_extract_geojson = await flatgeobuf_to_featcol(db, response.content)

    if not data_extract_geojson:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=("Failed to convert flatgeobuf --> geojson"),
        )

    headers = {
        "Content-Disposition": ("attachment; filename=fmtm_data_extract.geojson"),
        "Content-Type": "application/media",
    }

    return Response(content=json.dumps(data_extract_geojson), headers=headers)


@router.get("/centroid/")
async def project_centroid(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
) -> Feature:
    """Get a centroid of each projects.

    Parameters:
        project_id (int): The ID of the project.
        db (Connection): The database connection.

    Returns:
        list[tuple[int, str]]: A list of tuples containing the task ID and
            the centroid as a string.
    """
    project = project_user.get("project")
    centroid = project.centroid
    return wkb_geom_to_feature(centroid)


@router.get(
    "/task-status/{task_id}",
    response_model=project_schemas.BackgroundTaskStatus,
)
async def get_task_status(
    task_id: str,
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the background task status by passing the task ID."""
    try:
        return await DbBackgroundTask.one(db, task_id)
    except KeyError as e:
        log.warning(str(e))
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


@router.get(
    "/project_dashboard/{project_id}", response_model=project_schemas.ProjectDashboard
)
async def project_dashboard(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the project dashboard details."""
    project = project_user.get("project")
    details = await project_crud.get_dashboard_detail(db, project)
    details["slug"] = project.slug
    details["organisation_name"] = project.organisation_name
    details["created_at"] = project.created_at
    details["organisation_logo"] = project.organisation_logo
    details["last_active"] = project.last_active
    return details


@router.get("/contributors/{project_id}")
async def get_contributors(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get contributors of a project.

    TODO use a pydantic model for return type
    """
    project = project_user.get("project")
    return await project_crud.get_project_users_plus_contributions(db, project.id)


@router.post("/add-manager/")
async def add_new_project_manager(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
):
    """Add a new project manager.

    The logged in user must be either the admin of the organisation or a super admin.
    """
    await DbUserRole.create(
        db,
        project_user_dict["project"].id,
        project_user_dict["user"].id,
        ProjectRole.PROJECT_MANAGER,
    )
    return Response(status_code=HTTPStatus.OK)


@router.post("/", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.ProjectIn,
    org_user_dict: Annotated[AuthUser, Depends(org_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Create a project in ODK Central and the local database.

    The org_id and project_id params are inherited from the org_admin permission.
    Either param can be passed to determine if the user has admin permission
    to the organisation (or organisation associated with a project).
    """
    db_user = org_user_dict["user"]
    db_org = org_user_dict["org"]
    project_info.organisation_id = db_org.id

    log.info(
        f"User {db_user.username} attempting creation of project "
        f"{project_info.name} in organisation ({db_org.id})"
    )

    # Must decrypt ODK password & connect to ODK Central before proj created
    # cannot use project.odk_credentials helper as no project set yet
    # FIXME this can be updated once we have incremental project creation
    if project_info.odk_central_url:
        odk_creds_decrypted = central_schemas.ODKCentralDecrypted(
            odk_central_url=project_info.odk_central_url,
            odk_central_user=project_info.odk_central_user,
            odk_central_password=project_info.odk_central_password,
        )
    else:
        # Else use default org credentials if none passed
        log.debug(
            "No ODK credentials passed during project creation. "
            "Defaulting to organisation credentials."
        )
        odk_creds_decrypted = await organisation_deps.get_org_odk_creds(db_org)

    await project_deps.check_project_dup_name(db, project_info.name.lower())

    # Create project in ODK Central
    # NOTE runs in separate thread using run_in_threadpool
    odkproject = await run_in_threadpool(
        lambda: central_crud.create_odk_project(project_info.name, odk_creds_decrypted)
    )

    # Create the project in the local DB
    project_info.odkid = odkproject["id"]
    project_info.author_id = db_user.id
    project = await DbProject.create(db, project_info)
    if not project:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Project creation failed.",
        )

    return project


@router.patch("/{project_id}", response_model=project_schemas.ProjectOut)
async def update_project(
    new_data: project_schemas.ProjectUpdate,
    org_user_dict: Annotated[AuthUser, Depends(org_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Partial update an existing project."""
    # NOTE this does not including updating the ODK project name
    return await DbProject.update(db, org_user_dict.get("project").id, new_data)
