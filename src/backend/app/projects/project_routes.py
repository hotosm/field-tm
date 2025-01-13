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

import requests
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse
from fmtm_splitter.splitter import split_by_sql, split_by_square
from geojson_pydantic import FeatureCollection
from loguru import logger as log
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.make_data_extract import getChoices
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import Connection

from app.auth.auth_deps import login_required, mapper_login_required
from app.auth.auth_schemas import AuthUser, OrgUserDict, ProjectUserDict
from app.auth.providers.osm import check_osm_user, init_osm_auth
from app.auth.roles import check_access, mapper, org_admin, project_manager
from app.central import central_crud, central_deps, central_schemas
from app.config import settings
from app.db.database import db_conn
from app.db.enums import (
    HTTPStatus,
    ProjectRole,
    XLSFormType,
)
from app.db.models import (
    DbBackgroundTask,
    DbBasemap,
    DbGeometryLog,
    DbOdkEntities,
    DbProject,
    DbTask,
    DbUser,
    DbUserRole,
)
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    flatgeobuf_to_featcol,
    merge_polygons,
    parse_geojson_file_to_featcol,
)
from app.organisations import organisation_deps
from app.projects import project_crud, project_deps, project_schemas
from app.s3 import delete_all_objs_under_prefix
from app.users.user_deps import get_user

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/features", response_model=FeatureCollection)
async def read_projects_to_featcol(
    # NOTE here we add not permissions to make this externally accessible
    # to scrapers / other projects
    db: Annotated[Connection, Depends(db_conn)],
    bbox: Optional[str] = None,
):
    """Return all projects as a single FeatureCollection.

    This endpoint is used by disaster.ninja.
    """
    return await project_crud.get_projects_featcol(db, bbox)


@router.get("", response_model=list[project_schemas.ProjectOut])
async def read_projects(
    current_user: Annotated[AuthUser, Depends(login_required)],
    db: Annotated[Connection, Depends(db_conn)],
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    """Return all projects."""
    projects = await DbProject.all(db, skip, limit, user_id)
    return projects


@router.post("/me", response_model=list[DbProject])
async def get_projects_for_user(
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get all projects the user is author of.

    TODO to be implemented in future.
    """
    raise HTTPException(status_code=HTTPStatus.NOT_IMPLEMENTED)


@router.post("/near_me", response_model=list[project_schemas.ProjectSummary])
async def get_tasks_near_me(
    lat: float,
    long: float,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
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
    search: Optional[str] = None,
):
    """Get a paginated summary of projects."""
    return await project_crud.get_paginated_projects(
        db, page, results_per_page, user_id, hashtags, search
    )


@router.get(
    "/search",
    response_model=project_schemas.PaginatedProjectSummaries,
)
async def search_project(
    current_user: Annotated[AuthUser, Depends(login_required)],
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
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    minimal: bool = False,
):
    """Get the ODK entities for a project in GeoJSON format.

    NOTE This endpoint should not not be used to display the feature geometries.
    Rendering multiple GeoJSONs if inefficient.
    This is done by the flatgeobuf by filtering the task area bbox.
    """
    project = project_user.get("project")
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
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entities mapping statuses, i.e. in progress or complete."""
    project = project_user.get("project")
    entities = await central_crud.get_entities_data(
        project.odk_credentials,
        project.odkid,
    )
    # First update the Entity statuses in the db
    # FIXME this is a hack and in the long run should be replaced
    # https://github.com/hotosm/fmtm/issues/1841
    await DbOdkEntities.upsert(db, project.id, entities)
    return entities


@router.get(
    "/{project_id}/entities/osm-ids",
    response_model=list[central_schemas.EntityOsmID],
)
async def get_odk_entities_osm_ids(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get the ODK entities linked OSM IDs.

    This endpoint is required as we cannot modify the data extract fields
    when generated via raw-data-api.
    We need to link Entity UUIDs to OSM/Feature IDs.
    """
    project = project_user.get("project")
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
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get the ODK entities linked FMTM Task IDs."""
    project = project_user.get("project")
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
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entity mapping status, i.e. in progress or complete."""
    project = project_user.get("project")
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
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    entity_details: central_schemas.EntityMappingStatusIn,
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
    project = project_user.get("project")
    return await central_crud.update_entity_mapping_status(
        project.odk_credentials,
        project.odkid,
        entity_details.entity_id,
        entity_details.label,
        entity_details.status,
    )


@router.get(
    "/{project_id}/tiles",
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


# NOTE we no longer need this as tiles are uploaded to S3
# However, it could be useful if requiring private buckets in
# the future, with pre-signed URL generation
# @router.get(
#     "/{project_id}/tiles/{tile_id}",
#     response_model=project_schemas.BasemapOut,
# )
# async def download_tiles(
#     tile_id: UUID,
#     db: Annotated[Connection, Depends(db_conn)],
#     project_user: Annotated[ProjectUserDict, Depends(mapper)],
# ):
#     """Download the basemap tile archive for a project."""
#     log.debug("Getting basemap path from DB")
#     try:
#         db_basemap = await DbBasemap.one(db, tile_id)
#     except KeyError as e:
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

#     log.info(f"User requested download for tiles: {db_basemap.url}")

#     project = project_user.get("project")
#     filename = Path(db_basemap.url).name.replace(f"{project.id}_", f"{project.slug}_")
#     log.debug(f"Sending tile archive to user: {filename}")

#     if db_basemap.format == "mbtiles":
#         mimetype = "application/vnd.mapbox-vector-tile"
#     elif db_basemap.format == "pmtiles":
#         mimetype = "application/vnd.pmtiles"
#     else:
#         mimetype = "application/vnd.sqlite3"

#     return FileResponse(
#         db_basemap.url,
#         headers={
#             "Content-Disposition": f"attachment; filename={filename}",
#             "Content-Type": mimetype,
#         },
#     )


@router.get("/categories")
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


@router.get("/download-form/{project_id}")
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


@router.get("/features/download")
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


@router.get("/convert-fgb-to-geojson")
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


@router.get(
    "/task-status/{bg_task_id}",
    response_model=project_schemas.BackgroundTaskStatus,
)
async def get_task_status(
    bg_task_id: str,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get the background task status by passing the task ID."""
    try:
        return await DbBackgroundTask.one(db, bg_task_id)
    except KeyError as e:
        log.warning(str(e))
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


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


##################
# MANAGER ROUTES #
##################


@router.post("/task-split")
async def task_split(
    # NOTE we do not set any roles on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    current_user: Annotated[AuthUser, Depends(login_required)],
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    no_of_buildings: int = Form(50),
):
    """Split a task into subtasks.

    NOTE we pass a connection

    Args:
        current_user (AuthUser): the currently logged in user.
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
    # NOTE we do not set any roles on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    current_user: Annotated[AuthUser, Depends(login_required)],
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    debug: bool = False,
):
    """Basic validity check for uploaded XLSForm.

    Parses the form using ODK pyxform to check that it is valid.

    If the `debug` param is used, the form is returned for inspection.
    NOTE that this debug form has additional fields appended and should
        not be used for FMTM project creation.

    NOTE this provides a basic sanity check, some fields are omitted
    so the form is not usable in production:
        - form_category
        - additional_entities
        - new_geom_type
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


@router.post("/preview-split-by-square", response_model=FeatureCollection)
async def preview_split_by_square(
    # NOTE we do not set any roles on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    current_user: Annotated[AuthUser, Depends(login_required)],
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

    if len(boundary_featcol["features"]) > 0:
        boundary_featcol = merge_polygons(boundary_featcol)

    return split_by_square(
        boundary_featcol,
        settings.FMTM_DB_URL.unicode_string(),
        meters=dimension_meters,
        osm_extract=parsed_extract,
    )


@router.post("/generate-data-extract")
async def get_data_extract(
    # config_file: Optional[str] = Form(None),
    # NOTE we do not set any roles on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    current_user: Annotated[AuthUser, Depends(login_required)],
    geojson_file: UploadFile = File(...),
    form_category: Optional[XLSFormType] = Form(None),
):
    """Get a new data extract for a given project AOI.

    TODO allow config file (YAML/JSON) upload for data extract generation
    TODO alternatively, direct to raw-data-api to generate first, then upload
    """
    boundary_geojson = parse_geojson_file_to_featcol(await geojson_file.read())
    clean_boundary_geojson = merge_polygons(boundary_geojson)

    # Get extract config file from existing data_models
    if form_category:
        config_filename = XLSFormType(form_category).name
        data_model = f"{data_models_path}/{config_filename}.yaml"
        with open(data_model, "rb") as data_model_yaml:
            extract_config = BytesIO(data_model_yaml.read())
    else:
        extract_config = None

    fgb_url = await project_crud.generate_data_extract(
        clean_boundary_geojson,
        extract_config,
    )

    return JSONResponse(status_code=HTTPStatus.OK, content={"url": fgb_url})


@router.get("/data-extract-url")
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


@router.post("/upload-custom-extract")
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


@router.post("/add-manager")
async def add_new_project_manager(
    request: Request,
    db: Annotated[Connection, Depends(db_conn)],
    background_tasks: BackgroundTasks,
    new_manager: Annotated[DbUser, Depends(get_user)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    osm_auth=Depends(init_osm_auth),
):
    """Add a new project manager.

    The logged in user must be the admin of the organisation.
    """
    await DbUserRole.create(
        db,
        org_user_dict["project"].id,
        new_manager.id,
        ProjectRole.PROJECT_MANAGER,
    )

    background_tasks.add_task(
        project_crud.send_project_manager_message,
        request=request,
        project=org_user_dict["project"],
        new_manager=new_manager,
        osm_auth=osm_auth,
    )
    return Response(status_code=HTTPStatus.OK)


@router.post("/invite-new-user")
async def invite_new_user(
    request: Request,
    background_tasks: BackgroundTasks,
    project: Annotated[DbProject, Depends(project_deps.get_project)],
    invitee_username: str,
    osm_auth=Depends(init_osm_auth),
):
    """Invite a new user to a project."""
    user_exists = await check_osm_user(invitee_username)

    if not user_exists:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User does not exist on Open Street Map",
        )
    background_tasks.add_task(
        project_crud.send_invitation_message,
        request=request,
        project=project,
        invitee_username=invitee_username,
        osm_auth=osm_auth,
    )
    return Response(status_code=HTTPStatus.OK)


@router.post("/update-form")
async def update_project_form(
    xlsform: Annotated[BytesIO, Depends(central_deps.read_xlsform)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    xform_id: str = Form(...),
    category: XLSFormType = Form(...),
):
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
        UPDATE projects
        SET
            xlsform_content = %(xls_data)s
        WHERE
            id = %(project_id)s
        RETURNING id, hashtags;
    """
    async with db.cursor() as cur:
        await cur.execute(
            sql,
            {
                "xls_data": xlsform.getvalue(),
                "project_id": project.id,
            },
        )
        db.commit()

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": f"Successfully updated the form for project {project.id}"},
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
    project_odk_id = project.odkid
    project_odk_creds = project.odk_credentials
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

    return Response(status_code=HTTPStatus.OK)


@router.post("/{project_id}/generate-project-data")
async def generate_files(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    background_tasks: BackgroundTasks,
    xlsform_upload: Annotated[
        Optional[BytesIO], Depends(central_deps.read_optional_xlsform)
    ],
    additional_entities: Optional[list[str]] = None,
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

    Args:
        xlsform_upload (UploadFile, optional): A custom XLSForm to use in the project.
            A file should be provided if user wants to upload a custom xls form.
        additional_entities (list[str]): If additional Entity lists need to be
            created (i.e. the project form references multiple geometries).
        db (Connection): The database connection.
        project_user_dict (ProjectUserDict): Project admin role.
        background_tasks (BackgroundTasks): FastAPI background tasks.

    Returns:
        json (JSONResponse): A success message containing the project ID.
    """
    project = project_user_dict.get("project")
    project_id = project.id
    form_category = project.xform_category
    new_geom_type = project.new_geom_type

    log.debug(f"Generating additional files for project: {project.id}")

    if xlsform_upload:
        log.debug("User provided custom XLSForm")

        # Validate uploaded form
        await central_crud.validate_and_update_user_xlsform(
            xlsform=xlsform_upload,
            form_category=form_category,
            additional_entities=additional_entities,
            new_geom_type=new_geom_type,
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
        new_geom_type=new_geom_type,
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

    success = await project_crud.generate_project_files(
        db,
        project_id,
    )

    if not success:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "message": (
                    f"Failed project ({project_id}) creation. "
                    "Please contact the server admin."
                )
            },
        )

    if project.custom_tms_url:
        basemap_in = project_schemas.BasemapGenerate(
            tile_source="custom", file_format="pmtiles", tms_url=project.custom_tms_url
        )
        org_id = project.organisation_id
        await generate_basemap(project_id, org_id, basemap_in, db, background_tasks)

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": "success"},
    )


@router.post("/{project_id}/tiles-generate")
async def generate_project_basemap(
    # NOTE we do not set the correct role on this endpoint yet
    # FIXME once sub project creation implemented, this should be manager only
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    background_tasks: BackgroundTasks,
    db: Annotated[Connection, Depends(db_conn)],
    basemap_in: project_schemas.BasemapGenerate,
):
    """Returns basemap tiles for a project."""
    project_id = project_user.get("project").id
    org_id = project_user.get("project").organisation_id

    await generate_basemap(project_id, org_id, basemap_in, db, background_tasks)
    # Create task in db and return uuid
    return {"Message": "Tile generation started"}


async def generate_basemap(
    project_id: int,
    org_id: int,
    basemap_in: project_schemas.BasemapGenerate,
    db: Connection,
    background_tasks: BackgroundTasks,
):
    """Generate basemap tiles for a project."""
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

    background_tasks.add_task(
        project_crud.generate_project_basemap,
        db,
        project_id,
        org_id,
        background_task_id,
        basemap_in.tile_source,
        basemap_in.file_format,
        basemap_in.tms_url,
    )


@router.patch("/{project_id}", response_model=project_schemas.ProjectOut)
async def update_project(
    new_data: project_schemas.ProjectUpdate,
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Partial update an existing project."""
    # NOTE this does not including updating the ODK project name
    return await DbProject.update(db, project_user_dict.get("project").id, new_data)


@router.post("/{project_id}/upload-task-boundaries")
async def upload_project_task_boundaries(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(project_manager)],
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


####################
# ORG ADMIN ROUTES #
####################


@router.post("", response_model=project_schemas.ProjectOut)
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

    await project_deps.check_project_dup_name(db, project_info.name)

    # Create project in ODK Central
    # NOTE runs in separate thread using run_in_threadpool
    odkproject = await run_in_threadpool(
        lambda: central_crud.create_odk_project(project_info.name, odk_creds_decrypted)
    )

    # Create the project in the FMTM DB
    project_info.odkid = odkproject["id"]
    project_info.author_id = db_user.id
    project = await DbProject.create(db, project_info)
    if not project:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Project creation failed.",
        )

    return project


@router.delete("/{project_id}")
async def delete_project(
    db: Annotated[Connection, Depends(db_conn)],
    project: Annotated[DbProject, Depends(project_deps.get_project)],
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
        settings.S3_BUCKET_NAME, f"/{project.organisation_id}/{project.id}"
    )
    # Delete FMTM project
    await DbProject.delete(db, project.id)

    log.info(f"Deletion of project {project.id} successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)


###############################
# ENDPOINTS THAT MUST BE LAST #
###############################
# NOTE this is due to the /{project_id} which will capture any text
# NOTE in place of the project_id integer


@router.get("/{project_id}", response_model=project_schemas.ProjectOut)
async def read_project(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get a specific project by ID."""
    return project_user.get("project")


@router.get("/{project_id}/minimal", response_model=project_schemas.ProjectOut)
async def read_project_minimal(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(mapper_login_required)],
):
    """Get a specific project by ID, with minimal metadata.

    This endpoint is used for a quick return on the mapper frontend,
    without all additional calculated fields.

    It can also be accessed via temporary authentication, regardless of
    project visibility, hence has very minimal metadata included
    (no sensitive fields).

    NOTE this does mean the odk_token can be retrieved from this endpoint
    and is a small leak that could be addressed in future if needed.
    (any user could theoretically submit a contribution via the ODK
    token, even if this is a private project).
    """
    return await DbProject.one(db, project_id, minimal=True)


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
) -> StreamingResponse:
    """Downloads the boundary of a project as a GeoJSON file."""
    project = project_user.get("project")
    geojson = json.dumps(project.outline).encode("utf-8")
    return StreamingResponse(
        BytesIO(geojson),
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


@router.post("/{project_id}/geometries")
async def create_geom_log(
    geom_log: project_schemas.GeometryLogIn,
    current_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Creates a new entry in the geometries log table.

    It allows mappers to create new geom.
    But needs a validator to invalidate (BAD status) the geom.

    Returns:
    geometries (DbGeometryLog): The created geometries log entry.

    Raises:
    HTTPException: If user do not have permission.
    Or if the geometries log creation fails.
    """
    db_user = current_user.get("user")
    db_project = current_user.get("project")

    if geom_log.status == "BAD":
        access = await check_access(
            db_user,
            db,
            project_id=db_project.id,
            role=ProjectRole.PROJECT_MANAGER,  # later change this to validator
        )
        if not access:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You don't have permission to do this operation.",
            )

    geometries = await DbGeometryLog.create(db, geom_log)
    if not geometries:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="geometries log creation failed.",
        )

    return geometries


@router.delete("/{project_id}/geometries")
async def delete_geom_log(
    geom_id: str,
    project_user: Annotated[
        ProjectUserDict, Depends(project_manager)
    ],  # later change this to validator
    db: Annotated[Connection, Depends(db_conn)],
):
    """Delete geometry from geometry log table.

    Returns: HTTP 204 response.

    Raises:
    HTTPException: If the geometries log deletion fails.
    """
    project_id = project_user.get("project").id
    await DbGeometryLog.delete(db, project_id, geom_id)
    log.info(f"Deletion of geom {geom_id} from project {project_id} is successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)
