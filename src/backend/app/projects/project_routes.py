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
"""Endpoints for Field-TM projects."""

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Annotated, List, Optional
from uuid import UUID

from area_splitter.splitter import split_by_sql, split_by_square
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
from geojson_pydantic import FeatureCollection
from loguru import logger as log
from osm_fieldwork.json_data_models import data_models_path, get_choices
from pg_nearest_city import AsyncNearestCity
from psycopg import Connection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_schemas import AuthUser, OrgUserDict, ProjectUserDict
from app.auth.providers.osm import init_osm_auth
from app.auth.roles import Mapper, ProjectManager, org_admin
from app.central import central_crud, central_schemas
from app.config import settings
from app.db.database import db_conn
from app.db.enums import DbGeomType, HTTPStatus, ProjectRole, ProjectStatus, XLSFormType
from app.db.languages_and_countries import countries
from app.db.models import (
    DbBackgroundTask,
    DbBasemap,
    DbOdkEntities,
    DbOrganisation,
    DbProject,
    DbProjectTeam,
    DbProjectTeamUser,
    DbTask,
    DbUser,
    DbUserRole,
)
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    merge_polygons,
    parse_geojson_file_to_featcol,
    polygon_to_centroid,
)
from app.organisations import organisation_deps
from app.projects import project_crud, project_deps, project_schemas
from app.projects.project_schemas import ProjectUserContributions
from app.s3 import delete_all_objs_under_prefix
from app.users.user_deps import get_user
from app.users.user_schemas import UserRolesOut

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


@router.get("", response_model=list[project_schemas.ProjectOutNoXml])
async def read_projects(
    current_user: Annotated[AuthUser, Depends(login_required)],
    db: Annotated[Connection, Depends(db_conn)],
    user_sub: str = None,
    skip: int = 0,
    limit: int = 100,
):
    """Return all projects."""
    projects = await DbProject.all(db, skip, limit, current_user, user_sub)
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
    current_user: Annotated[AuthUser, Depends(public_endpoint)],
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    org_id: Optional[int] = None,
    user_sub: Optional[str] = None,
    hashtags: Optional[str] = None,
    search: Optional[str] = None,
    minimal: bool = False,
    status: ProjectStatus = None,
):
    """Get a paginated summary of projects.

    NOTE this is a public endpoint with no auth requirements.
    """
    return await project_crud.get_paginated_projects(
        db,
        page,
        results_per_page,
        current_user,
        org_id,
        user_sub,
        hashtags,
        search,
        minimal,
        status,
    )


@router.get(
    "/{project_id}/entities", response_model=central_schemas.EntityFeatureCollection
)
async def get_odk_entities_geojson(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the ODK entities mapping statuses, i.e. in progress or complete."""
    project = project_user.get("project")
    entities = await central_crud.get_entities_data(
        project.odk_credentials,
        project.odkid,
    )
    await DbOdkEntities.upsert(db, project.id, entities)
    return entities


@router.get(
    "/{project_id}/entities/osm-ids",
    response_model=list[central_schemas.EntityOsmID],
)
async def get_odk_entities_osm_ids(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get the ODK entities linked Field-TM Task IDs."""
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
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    project_user: Annotated[ProjectUserDict, Depends(Mapper(check_completed=True))],
    entity_details: central_schemas.EntityMappingStatusIn,
    db: Annotated[Connection, Depends(db_conn)],
):
    """Set the ODK entities mapping status, i.e. in progress or complete.

    entity_details must be a JSON body with params:
    {
        "entity_id": "string",
        "label": "Feature <FEATURE_ID>",
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
        entity_details.submission_ids,
    )


@router.get(
    "/{project_id}/tiles",
    response_model=list[project_schemas.BasemapOut],
)
async def tiles_list(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
#     project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
        get_choices()
    )  # categories are fetched from osm_fieldwork.data_models.get_choices()
    return categories


@router.get("/features/download")
async def download_features(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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


@router.get("/contributors/{project_id}", response_model=list[ProjectUserContributions])
async def get_contributors(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get contributors of a project."""
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
    # NOTE here we pass the connection string and allow area-splitter to
    # a use psycopg2 connection (not async)
    features = await run_in_threadpool(
        lambda: split_by_sql(
            merged_boundary,
            settings.FMTM_DB_URL,
            num_buildings=no_of_buildings,
            osm_extract=parsed_extract,
        )
    )
    log.debug("COMPLETE task splitting")
    return features


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
        settings.FMTM_DB_URL,
        meters=dimension_meters,
        osm_extract=parsed_extract,
    )


@router.post("/generate-data-extract")
async def get_data_extract(
    # config_file: Optional[str] = Form(None),
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
    geojson_file: UploadFile = File(...),
    # FIXME this is currently hardcoded but needs to be user configurable via UI
    osm_category: Annotated[Optional[XLSFormType], Form()] = XLSFormType.buildings,
    centroid: Annotated[bool, Form()] = False,
    geom_type: Annotated[DbGeomType, Form()] = DbGeomType.POLYGON,
    use_st_within: Annotated[bool, Form()] = True,
):
    """Get a new data extract for a given project AOI.

    TODO allow config file (YAML/JSON) upload for data extract generation
    TODO alternatively, direct to raw-data-api to generate first, then upload
    """
    boundary_geojson = parse_geojson_file_to_featcol(await geojson_file.read())
    clean_boundary_geojson = merge_polygons(boundary_geojson)
    project = project_user_dict.get("project")

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

    return JSONResponse(
        status_code=HTTPStatus.OK, content={"url": result.data.get("download_url")}
    )


@router.get("/data-extract-url")
async def get_or_set_data_extract(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
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


@router.post("/upload-data-extract")
async def upload_data_extract(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
    data_extract_file: UploadFile = File(...),
):
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
    project_id = project_user_dict.get("project").id

    # Validating for .geojson File.
    file_name = os.path.splitext(data_extract_file.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json", ".fgb"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST, detail="Provide a valid .geojson or .fgb file"
        )

    # read entire file
    extract_data = await data_extract_file.read()

    fgb_url = await project_crud.upload_geojson_data_extract(
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
        new_manager.sub,
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


@router.get("/{project_id}/users", response_model=list[UserRolesOut])
async def get_project_users(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[DbUser, Depends(ProjectManager())],
    role: Optional[str] = None,
):
    """Get project users and their project role."""
    project = project_user_dict.get("project")
    users = await DbUserRole.all(db, project.id, role=role)
    if not users:
        return []
    return users


@router.post("/{project_id}/additional-entity")
async def add_additional_entity_list(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
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
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
    background_tasks: BackgroundTasks,
    combined_features_count: Annotated[int, Form()] = 0,
):
    """Generate additional content to initialise the project.

    Boundary, ODK Central forms, QR codes, etc.

    Accepts a project ID and an uploaded file as inputs.
    The generated files are associated with the project ID and stored in the database.
    This api generates odk appuser tokens, forms. This api also creates an app user for
    each task and provides the required roles.
    Some of the other functionality of this api includes converting a xls file
    provided by the user to the xform, generates osm data extracts and uploads
    it to the form.

    Args:
        combined_features_count (int): Total count of features to be mapped, plus
            additional dataset features, determined by frontend.
        db (Connection): The database connection.
        project_user_dict (ProjectUserDict): Project admin role.
        background_tasks (BackgroundTasks): FastAPI background tasks.

    Returns:
        json (JSONResponse): A success message containing the project ID.
    """
    project = project_user_dict.get("project")
    project_id = project.id
    log.debug(f"Generating additional files for project: {project.id}")
    warning_message = None

    if combined_features_count > 10000:
        # Return immediately and run in background if many features
        background_tasks.add_task(
            project_crud.generate_project_files,
            db,
            project_id,
        )
        warning_message = "There are lots of features to process. Please be patient 🙏"

    else:
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

    if warning_message:
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": warning_message},
        )
    return Response(status_code=HTTPStatus.OK)


@router.post("/{project_id}/tiles-generate")
async def generate_project_basemap(
    project_user: Annotated[ProjectUserDict, Depends(ProjectManager())],
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
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Partial update an existing project."""
    # NOTE this does not including updating the ODK project name
    return await DbProject.update(db, project_user_dict.get("project").id, new_data)


@router.post("/{project_id}/upload-task-boundaries")
async def upload_project_task_boundaries(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
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
    project_id = project_user_dict.get("project").id
    tasks_featcol = parse_geojson_file_to_featcol(await task_geojson.read())
    await check_crs(tasks_featcol)
    # We only want to allow polygon geometries
    featcol_single_geom_type = featcol_keep_single_geom_type(
        tasks_featcol,
        geom_type="Polygon",
    )
    success = await DbTask.create(db, project_id, featcol_single_geom_type)
    if success:
        return JSONResponse(content={"message": "success"})

    log.error(f"Failed to create task areas for project {project_id}")
    return JSONResponse(content={"message": "failure"})


####################
# ORG ADMIN ROUTES #
####################


@router.post("/stub", response_model=project_schemas.ProjectOut)
async def create_stub_project(
    project_info: project_schemas.StubProjectIn,
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Create a project in the local database.

    The org_id and project_id params are inherited from the org_admin permission.
    Either param can be passed to determine if the user has admin permission
    to the organisation (or organisation associated with a project).
    """
    delattr(project_info, "merge")  # Remove merge field as it is not in database
    db_user = org_user_dict["user"]
    db_org = org_user_dict["org"]
    project_info.organisation_id = db_org.id
    project_info.status = ProjectStatus.DRAFT

    log.info(
        f"User {db_user.username} attempting creation of project "
        f"{project_info.name} in organisation ({db_org.id})"
    )
    await project_deps.check_project_dup_name(db, project_info.name)

    # Get the location_str via reverse geocode
    async with AsyncNearestCity(db) as geocoder:
        centroid = await polygon_to_centroid(project_info.outline.model_dump())
        latitude, longitude = centroid.y, centroid.x
        location = await geocoder.query(latitude, longitude)
        # Convert to two letter country code --> full name
        country_full_name = countries.get(location.country, location.country)
        project_info.location_str = f"{location.city},{country_full_name}"

    # Create the project in the Field-TM DB
    project_info.author_sub = db_user.sub
    try:
        log.debug(f"Project details: {project_info}")
        project = await DbProject.create(db, project_info)
    except Exception as e:
        log.error(f"Error posting to /stub: {e}")
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Project creation failed.",
        ) from e
    if not project:
        log.error("Project creation passed at /stub, but the project is empty")
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
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
    # Delete Field-TM project
    await DbProject.delete(db, project.id)

    log.info(f"Deletion of project {project.id} successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.patch("", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.ProjectIn,
    project_user: Annotated[ProjectUserDict, Depends(ProjectManager())],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Create a project in ODK Central and update the local stub project.

    The org_id and project_id params are inherited from the org_admin permission.
    Either param can be passed to determine if the user has admin permission
    to the organisation (or organisation associated with a project).
    """
    project_id = project_user.get("project").id
    org_id = project_user.get("project").organisation_id
    db_org = await DbOrganisation.one(db, org_id)
    project = await DbProject.one(db, project_id)

    if project_info.name:
        await project_deps.check_project_dup_name(db, project_info.name)
    if project_info.odk_credentials:
        odk_creds_decrypted = project_info.odk_credentials
    else:
        log.debug(
            "No ODK credentials passed during project creation. "
            "Defaulting to organisation credentials."
        )
        odk_creds_decrypted = await organisation_deps.get_org_odk_creds(db_org)

    # Create project in ODK Central
    # NOTE runs in separate thread using run_in_threadpool
    odkproject = await run_in_threadpool(
        lambda: central_crud.create_odk_project(project.name, odk_creds_decrypted)
    )
    project_info.odkid = odkproject["id"]

    try:
        project = await DbProject.update(db, project.id, project_info)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Project update failed.",
        ) from e

    return project


###############################
# ENDPOINTS THAT MUST BE LAST #
###############################
# NOTE this is due to the /{project_id} which will capture any text
# NOTE in place of the project_id integer


@router.get("/{project_id}", response_model=project_schemas.ProjectOut)
async def read_project(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get a specific project by ID."""
    return project_user.get("project")


@router.get("/{project_id}/minimal", response_model=project_schemas.ProjectOut)
async def read_project_minimal(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    return await project_deps.get_project_by_id(db, project_id, minimal=True)


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    task_geojson = await project_crud.get_task_geometry(db, project_id)

    headers = {
        "Content-Disposition": "attachment; filename=task_boundary.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=task_geojson, headers=headers)


@router.get("/{project_id}/teams", response_model=List[project_schemas.ProjectTeam])
async def get_project_teams(
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Get the teams associated with a project."""
    project_id = project_user.get("project").id
    teams = await DbProjectTeam.all(db, project_id)
    return teams


@router.post("/{project_id}/teams", response_model=project_schemas.ProjectTeamOne)
async def create_project_team(
    team: project_schemas.ProjectTeamIn,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Create a new team for a project."""
    return await DbProjectTeam.create(db, team)


@router.get("/{project_id}/teams/{team_id}", response_model=project_schemas.ProjectTeam)
async def get_team(
    team: Annotated[DbProjectTeam, Depends(project_deps.get_project_team)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(ProjectManager())],
):
    """Get the teams associated with a project."""
    team = await DbProjectTeam.one(db, team.team_id)
    return team


@router.patch(
    "/{project_id}/teams/{team_id}", response_model=project_schemas.ProjectTeamOne
)
async def update_project_team(
    team: Annotated[DbProjectTeam, Depends(project_deps.get_project_team)],
    team_update: project_schemas.ProjectTeamIn,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Get the teams associated with a project."""
    team = await DbProjectTeam.update(db, team.team_id, team_update)
    return team


@router.delete("/{project_id}/teams/{team_id}")
async def delete_project_team(
    team: Annotated[DbProjectTeam, Depends(project_deps.get_project_team)],
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Get the teams associated with a project."""
    team = await DbProjectTeam.delete(db, team.team_id)
    return team


@router.post("/{project_id}/teams/{team_id}/users")
async def add_team_users(
    team: Annotated[DbProjectTeam, Depends(project_deps.get_project_team)],
    user_subs: List[str],
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Add users to a team."""
    # Assign mapper user roles to the project
    for user_sub in user_subs:
        await DbUserRole.create(
            db,
            project_user.get("project").id,
            user_sub,
            ProjectRole.MAPPER,
        )
    await DbProjectTeamUser.create(db, team.team_id, user_subs)
    return Response(status_code=HTTPStatus.OK)


@router.delete("/{project_id}/teams/{team_id}/users")
async def remove_team_users(
    team: Annotated[DbProjectTeam, Depends(project_deps.get_project_team)],
    user_subs: List[str],
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Add users to a team."""
    await DbProjectTeamUser.delete(db, team.team_id, user_subs)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete("/entity/{entity_uuid}")
async def delete_entity(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(Mapper())],
    entity_uuid: UUID,
    dataset_name: str = "features",
):
    """Delete an Entity from ODK and local database."""
    try:
        project = project_user_dict.get("project")
        project_odk_id = project.odkid
        project_odk_creds = project.odk_credentials

        log.debug(
            f"Deleting ODK Entity in dataset '{dataset_name}'(ODK ID: {project_odk_id})"
        )
        await central_crud.delete_entity(
            odk_creds=project_odk_creds,
            odk_id=project_odk_id,
            entity_uuid=entity_uuid,
            dataset_name=dataset_name,
        )
        await DbOdkEntities.delete(db, entity_uuid)
        return {"detail": "Entity deleted successfully"}

    except HTTPException as http_err:
        log.error(f"HTTP error during deletion: {http_err.detail}")
        raise
    except Exception as e:
        log.exception("Unexpected error during entity deletion")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Entity deletion failed",
        ) from e


@router.delete("/{project_id}/users/{user_sub}")
async def unassign_user_from_project(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[DbUser, Depends(ProjectManager())],
    user_sub: str,
):
    """Unassign a user from a project (remove their role)."""
    project = project_user_dict.get("project")
    await project_crud.unassign_user_from_project(db, project.id, user_sub)
    return {"message": f"User {user_sub} unassigned from project {project.id}."}
