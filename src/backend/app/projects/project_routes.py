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
from typing import Optional

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
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from geojson_pydantic import Feature, FeatureCollection
from loguru import logger as log
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.make_data_extract import getChoices
from osm_fieldwork.xlsforms import xlsforms_path
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth.auth_schemas import AuthUser, OrgUserDict, ProjectUserDict
from app.auth.osm import login_required
from app.auth.roles import mapper, org_admin, project_manager
from app.central import central_crud, central_deps, central_schemas
from app.db import database, db_models
from app.db.postgis_utils import (
    check_crs,
    flatgeobuf_to_featcol,
    merge_polygons,
    parse_geojson_file_to_featcol,
    split_geojson_by_task_areas,
    wkb_geom_to_feature,
)
from app.models.enums import (
    TILES_FORMATS,
    TILES_SOURCE,
    HTTPStatus,
    ProjectVisibility,
    XLSFormType,
)
from app.organisations import organisation_deps
from app.projects import project_crud, project_deps, project_schemas
from app.tasks import tasks_crud

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/features", response_model=FeatureCollection)
async def read_projects_to_featcol(
    db: Session = Depends(database.get_db),
    bbox: Optional[str] = None,
):
    """Return all projects as a single FeatureCollection."""
    return await project_crud.get_projects_featcol(db, bbox)


@router.get("/", response_model=list[project_schemas.ProjectOut])
async def read_projects(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    """Return all projects."""
    project_count, projects = await project_crud.get_projects(
        db, user_id=user_id, skip=skip, limit=limit
    )
    return projects


@router.post("/near_me", response_model=list[project_schemas.ProjectSummary])
async def get_tasks_near_me(lat: float, long: float, user_id: int = None):
    """Get projects near me.

    TODO to be implemented in future.
    """
    return [project_schemas.ProjectSummary()]


@router.get("/summaries", response_model=project_schemas.PaginatedProjectSummaries)
async def read_project_summaries(
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    user_id: Optional[int] = None,
    hashtags: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    """Get a paginated summary of projects."""
    if hashtags:
        hashtags = hashtags.split(",")  # create list of hashtags
        hashtags = list(
            filter(lambda hashtag: hashtag.startswith("#"), hashtags)
        )  # filter hashtags that do start with #

    total_project_count = (
        db.query(db_models.DbProject)
        .filter(
            db_models.DbProject.visibility  # type: ignore
            == ProjectVisibility.PUBLIC  # type: ignore
        )
        .count()
    )
    skip = (page - 1) * results_per_page
    limit = results_per_page

    project_count, projects = await project_crud.get_project_summaries(
        db, skip, limit, user_id, hashtags, None
    )

    pagination = await project_crud.get_pagination(
        page, project_count, results_per_page, total_project_count
    )

    project_summaries = [
        project_schemas.ProjectSummary(**project.__dict__) for project in projects
    ]

    response = project_schemas.PaginatedProjectSummaries(
        results=project_summaries,
        pagination=pagination,
    )
    return response


@router.get(
    "/search-projects", response_model=project_schemas.PaginatedProjectSummaries
)
async def search_project(
    search: str,
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    user_id: Optional[int] = None,
    hashtags: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    """Search projects by string, hashtag, or other criteria."""
    if hashtags:
        hashtags = hashtags.split(",")  # create list of hashtags
        hashtags = list(
            filter(lambda hashtag: hashtag.startswith("#"), hashtags)
        )  # filter hashtags that do start with #

    total_projects = db.query(db_models.DbProject).count()
    skip = (page - 1) * results_per_page
    limit = results_per_page

    project_count, projects = await project_crud.get_project_summaries(
        db, skip, limit, user_id, hashtags, search
    )

    pagination = await project_crud.get_pagination(
        page, project_count, results_per_page, total_projects
    )
    project_summaries = [
        project_schemas.ProjectSummary(**project.__dict__) for project in projects
    ]

    response = project_schemas.PaginatedProjectSummaries(
        results=project_summaries,
        pagination=pagination,
    )
    return response


@router.get(
    "/{project_id}/entities", response_model=central_schemas.EntityFeatureCollection
)
async def get_odk_entities_geojson(
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    minimal: bool = False,
    db: Session = Depends(database.get_db),
):
    """Get the ODK entities for a project in GeoJSON format.

    NOTE This endpoint should not not be used to display the feature geometries.
    Rendering multiple GeoJSONs if inefficient.
    This is done by the flatgeobuf by filtering the task area bbox.
    """
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.get_entities_geojson(
        odk_credentials,
        project.odkid,
        minimal=minimal,
    )


@router.get(
    "/{project_id}/entities/statuses",
    response_model=list[central_schemas.EntityMappingStatus],
)
async def get_odk_entities_mapping_statuses(
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(database.get_db),
):
    """Get the ODK entities mapping statuses, i.e. in progress or complete."""
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.get_entities_data(
        odk_credentials,
        project.odkid,
    )


@router.get(
    "/{project_id}/entities/osm-ids",
    response_model=list[central_schemas.EntityOsmID],
)
async def get_odk_entities_osm_ids(
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(database.get_db),
):
    """Get the ODK entities linked OSM IDs.

    This endpoint is required as we cannot modify the data extract fields
    when generated via raw-data-api.
    We need to link Entity UUIDs to OSM/Feature IDs.
    """
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.get_entities_data(
        odk_credentials,
        project.odkid,
        fields="osm_id",
    )


@router.get(
    "/{project_id}/entities/task-ids",
    response_model=list[central_schemas.EntityTaskID],
)
async def get_odk_entities_task_ids(
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(database.get_db),
):
    """Get the ODK entities linked FMTM Task IDs."""
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.get_entities_data(
        odk_credentials,
        project.odkid,
        fields="task_id",
    )


@router.get(
    "/{project_id}/entity/status",
    response_model=central_schemas.EntityMappingStatus,
)
async def get_odk_entity_mapping_status(
    entity_id: str,
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(database.get_db),
):
    """Get the ODK entity mapping status, i.e. in progress or complete."""
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.get_entity_mapping_status(
        odk_credentials,
        project.odkid,
        entity_id,
    )


@router.post(
    "/{project_id}/entity/status",
    response_model=central_schemas.EntityMappingStatus,
)
async def set_odk_entities_mapping_status(
    entity_details: central_schemas.EntityMappingStatusIn,
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(database.get_db),
):
    """Set the ODK entities mapping status, i.e. in progress or complete.

    entity_details must be a JSON body with params:
    {
        "entity_id": "string",
        "label": "Task <TASK_ID> Feature <FEATURE_ID>",
        "status": 0
    }
    """
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    return await central_crud.update_entity_mapping_status(
        odk_credentials,
        project.odkid,
        entity_details.entity_id,
        entity_details.label,
        entity_details.status,
    )


@router.get("/{project_id}/tiles-list/")
async def tiles_list(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Returns the list of tiles for a project.

    Parameters:
        project_id: int
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: List of generated tiles for a project.
    """
    return await project_crud.get_mbtiles_list(db, project_user.get("project").id)


@router.get("/{project_id}/download-tiles/")
async def download_tiles(
    tile_id: int,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Download the basemap tile archive for a project."""
    log.debug("Getting tile archive path from DB")
    dbtile_obj = (
        db.query(db_models.DbTilesPath)
        .filter(db_models.DbTilesPath.id == str(tile_id))
        .first()
    )
    if not dbtile_obj:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Basemap ID does not exist!"
        )
    log.info(f"User requested download for tiles: {dbtile_obj.path}")

    project = project_user.get("project")
    filename = Path(dbtile_obj.path).name.replace(
        f"{project.id}_", f"{project.project_name_prefix}_"
    )
    log.debug(f"Sending tile archive to user: {filename}")

    if (tiles_path := Path(filename).suffix) == ".mbtiles":
        tiles_mime_type = "application/vnd.mapbox-vector-tile"
    elif tiles_path == ".pmtiles":
        tiles_mime_type = "application/vnd.pmtiles"
    else:
        tiles_mime_type = "application/vnd.sqlite3"

    return FileResponse(
        dbtile_obj.path,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": tiles_mime_type,
        },
    )


@router.get("/{project_id}/tiles")
async def generate_project_tiles(
    background_tasks: BackgroundTasks,
    project_id: int,
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
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Returns basemap tiles for a project."""
    # Create task in db and return uuid
    log.debug(
        "Creating generate_project_tiles background task "
        f"for project ID: {project_id}"
    )
    background_task_id = await project_crud.insert_background_task_into_database(
        db, project_id=project_id
    )

    background_tasks.add_task(
        project_crud.get_project_tiles,
        db,
        project_id,
        background_task_id,
        source,
        format,
        tms,
    )

    return {"Message": "Tile generation started"}


@router.get("/{project_id}", response_model=project_schemas.ReadProject)
async def read_project(
    project_user: ProjectUserDict = Depends(mapper),
):
    """Get a specific project by ID."""
    return project_user.get("project")


@router.delete("/{project_id}")
async def delete_project(
    db: Session = Depends(database.get_db),
    project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    org_user_dict: OrgUserDict = Depends(org_admin),
):
    """Delete a project from both ODK Central and the local database."""
    log.info(
        f"User {org_user_dict.get('user').username} attempting "
        f"deletion of project {project.id}"
    )
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    # Delete ODK Central project
    await central_crud.delete_odk_project(project.odkid, odk_credentials)
    # Delete S3 resources
    await project_crud.delete_fmtm_s3_objects(project)
    # Delete FMTM project
    await project_crud.delete_fmtm_project(db, project)

    log.info(f"Deletion of project {project.id} successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/create-project", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.ProjectUpload,
    org_user_dict: OrgUserDict = Depends(org_admin),
    db: Session = Depends(database.get_db),
):
    """Create a project in ODK Central and the local database.

    The org_id and project_id params are inherited from the org_admin permission.
    Either param can be passed to determine if the user has admin permission
    to the organisation (or organisation associated with a project).

    TODO refactor to standard REST POST to /projects
    TODO but first check doesn't break other endpoints
    """
    db_user = org_user_dict.get("user")

    db_org = org_user_dict.get("org")
    project_info.organisation_id = db_org.id

    log.info(
        f"User {db_user.username} attempting creation of project "
        f"{project_info.project_info.name} in organisation ({db_org.id})"
    )

    # Must decrypt ODK password & connect to ODK Central before proj created
    # cannot use get_odk_credentials helper as no project id yet
    if project_info.odk_central_url:
        odk_creds_decrypted = project_schemas.ODKCentralDecrypted(
            odk_central_url=project_info.odk_central_url,
            odk_central_user=project_info.odk_central_user,
            odk_central_password=project_info.odk_central_password,
        )
    else:
        # Use default org credentials if none passed
        log.debug(
            "No odk credentials passed during project creation. "
            "Defaulting to organisation credentials."
        )
        odk_creds_decrypted = await organisation_deps.get_org_odk_creds(db_org)

    sql = text("""
        SELECT EXISTS (
            SELECT 1
            FROM project_info
            WHERE LOWER(name) = :project_name
        )
    """)
    result = db.execute(sql, {"project_name": project_info.project_info.name.lower()})
    project_exists = result.scalar()
    if project_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Project already exists with the name "
            f"{project_info.project_info.name}",
        )

    odkproject = central_crud.create_odk_project(
        project_info.project_info.name,
        odk_creds_decrypted,
    )

    project = await project_crud.create_project_with_project_info(
        db,
        project_info,
        odkproject["id"],
        db_user,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project creation failed")

    return project


@router.put("/{project_id}", response_model=project_schemas.ProjectOut)
async def update_project(
    project_info: project_schemas.ProjectUpdate,
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
):
    """Update an existing project by ID.

    Note: the entire project JSON must be uploaded.
    If a partial update is required, use the PATCH method instead.

    Parameters:
    - id: ID of the project to update
    - project_info: Updated project information
    - current_user (DbUser): Check if user is project_manager

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    project = await project_crud.update_project_with_project_info(
        db, project_info, project_user_dict["project"], project_user_dict["user"]
    )
    if not project:
        raise HTTPException(status_code=422, detail="Project could not be updated")
    return project


@router.patch("/{project_id}", response_model=project_schemas.ProjectOut)
async def project_partial_update(
    project_info: project_schemas.ProjectPartialUpdate,
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
):
    """Partial Update an existing project by ID.

    Parameters:
    - id
    - name
    - short_description
    - description

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    # Update project information
    project = await project_crud.partial_update_project_info(
        db, project_info, project_user_dict["project"]
    )

    if not project:
        raise HTTPException(status_code=422, detail="Project could not be updated")
    return project


@router.post("/{project_id}/upload-task-boundaries")
async def upload_project_task_boundaries(
    project_id: int,
    task_geojson: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    org_user_dict: OrgUserDict = Depends(org_admin),
):
    """Set project task boundaries using split GeoJSON from frontend.

    Each polygon in the uploaded geojson are made into single task.

    Required Parameters:
        project_id (id): ID for associated project.
        task_geojson (UploadFile): Multi-polygon GeoJSON file.

    Returns:
        dict: JSON containing success message, project ID, and number of tasks.
    """
    log.debug(f"Uploading project boundary multipolygon for project ID: {project_id}")
    tasks_featcol = parse_geojson_file_to_featcol(await task_geojson.read())
    # Validatiing Coordinate Reference System
    await check_crs(tasks_featcol)

    log.debug("Creating tasks for each polygon in project")
    await project_crud.create_tasks_from_geojson(db, project_id, tasks_featcol)

    # Get the number of tasks in a project
    task_count = await tasks_crud.get_task_count_in_project(db, project_id)

    return {
        "message": "Project Boundary Uploaded",
        "project_id": f"{project_id}",
        "task_count": task_count,
    }


@router.post("/task-split")
async def task_split(
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    no_of_buildings: int = Form(50),
    db: Session = Depends(database.get_db),
):
    """Split a task into subtasks.

    Args:
        project_geojson (UploadFile): The geojson (AOI) to split.
        extract_geojson (UploadFile, optional): Custom data extract geojson
            containing osm features (should be a FeatureCollection).
            If not included, an extract is generated automatically.
        no_of_buildings (int, optional): The number of buildings per subtask.
            Defaults to 50.
        db (Session, optional): The database session. Injected by FastAPI.

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

    return await project_crud.split_geojson_into_tasks(
        db,
        merged_boundary,
        no_of_buildings,
        parsed_extract,
    )


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
    xlsform_upload: Optional[BytesIO] = Depends(central_deps.read_optional_xlsform),
    additional_entities: list[str] = None,
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
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
        db (Session): Database session, provided automatically.
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
    if not xlsform_bytes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="There was an error with the XLSForm!",
        )
    project.odk_form_id = xform_id
    project.xlsform_content = xlsform_bytes
    db.commit()

    # Create task in db and return uuid
    log.debug(f"Creating export background task for project ID: {project_id}")
    background_task_id = await project_crud.insert_background_task_into_database(
        db, project_id=project_id
    )

    log.debug(f"Submitting {background_task_id} to background tasks stack")
    background_tasks.add_task(
        project_crud.generate_project_files,
        db,
        project_id,
        background_task_id,
    )

    return JSONResponse(
        status_code=200,
        content={"Message": f"{project.id}", "task_id": f"{background_task_id}"},
    )


@router.post("/{project_id}/additional-entity")
async def add_additional_entity_list(
    geojson: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
):
    """Add an additional Entity list for the project in ODK.

    Note that the Entity list will be named from the filename
    of the GeoJSON uploaded.
    """
    project = project_user_dict.get("project")
    project_id = project.id
    project_odk_id = project.odkid
    odk_credentials = await project_deps.get_odk_credentials(db, project_id)
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
        odk_credentials,
        project_odk_id,
        dataset_name=entity_name,
        entities_list=entities_list,
    )

    return Response(status_code=HTTPStatus.OK)


@router.get("/categories/")
async def get_categories(current_user: AuthUser = Depends(login_required)):
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


@router.post("/preview-split-by-square/")
async def preview_split_by_square(
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    dimension: int = Form(100),
):
    """Preview splitting by square.

    TODO update to use a response_model
    """
    # Validating for .geojson File.
    file_name = os.path.splitext(project_geojson.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

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

    return await project_crud.preview_split_by_square(
        boundary_featcol, dimension, parsed_extract
    )


@router.post("/generate-data-extract/")
async def get_data_extract(
    geojson_file: UploadFile = File(...),
    form_category: Optional[XLSFormType] = Form(None),
    # config_file: Optional[str] = Form(None),
    current_user: AuthUser = Depends(login_required),
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

    return JSONResponse(status_code=200, content={"url": fgb_url})


@router.get("/data-extract-url/")
async def get_or_set_data_extract(
    url: Optional[str] = None,
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
):
    """Get or set the data extract URL for a project."""
    fgb_url = await project_crud.get_or_set_data_extract_url(
        db,
        project_id,
        url,
    )

    return JSONResponse(status_code=200, content={"url": fgb_url})


@router.post("/upload-custom-extract/")
async def upload_custom_extract(
    custom_extract_file: UploadFile = File(...),
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
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
    # Validating for .geojson File.
    file_name = os.path.splitext(custom_extract_file.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json", ".fgb"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Provide a valid .geojson or .fgb file"
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
    return JSONResponse(status_code=200, content={"url": fgb_url})


@router.get("/download-form/{project_id}/")
async def download_form(
    project_user: ProjectUserDict = Depends(mapper),
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
    xform_id: str = Form(...),
    category: XLSFormType = Form(...),
    xlsform: BytesIO = Depends(central_deps.read_xlsform),
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
) -> project_schemas.ProjectBase:
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

    # Get ODK Central credentials for project
    odk_creds = await project_deps.get_odk_credentials(db, project.id)
    # Update ODK Central form data
    await central_crud.update_project_xform(
        xform_id,
        project.odkid,
        xlsform,
        category,
        len(project.tasks),
        odk_creds,
    )

    # Commit changes to db
    project.xlsform_content = xlsform.getvalue()
    db.commit()

    return project


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_user: ProjectUserDict = Depends(mapper),
) -> StreamingResponse:
    """Downloads the boundary of a project as a GeoJSON file."""
    project = project_user.get("project")
    geojson = wkb_geom_to_feature(project.outline, id=project.id)
    return StreamingResponse(
        BytesIO(json.dumps(geojson).encode("utf-8")),
        headers={
            "Content-Disposition": (
                f"attachment; filename={project.project_name_prefix}.geojson"
            ),
            "Content-Type": "application/media",
        },
    )


@router.get("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: Session = Depends(mapper),
):
    """Downloads the boundary of the tasks for a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user has MAPPER permission.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    out = await project_crud.get_task_geometry(db, project_id)

    headers = {
        "Content-Disposition": "attachment; filename=project_outline.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=out, headers=headers)


@router.get("/features/download/")
async def download_features(
    task_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
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
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Convert flatgeobuf to GeoJSON format, extracting GeometryCollection.

    Helper endpoint to test data extracts during project creation.
    Required as the flatgeobuf files wrapped in GeometryCollection
    cannot be read in QGIS or other tools.

    Args:
        url (str): URL to the flatgeobuf file.
        db (Session): The database session, provided automatically.
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


# @router.get("/boundary_in_osm/{project_id}/")
# async def download_task_boundary_osm(
#     project_id: int,
#     db: Session = Depends(database.get_db),
#     project_user: ProjectUserDict = Depends(mapper),
# ):
#     """Downloads the boundary of a task as a OSM file.

#     Args:
#         project_id (int): The id of the project.
#         db (Session): The database session, provided automatically.
#         current_user (AuthUser): Check if user has MAPPER permission.

#     Returns:
#         Response: The HTTP response object containing the downloaded file.
#     """
#     out = await project_crud.get_task_geometry(db, project_id)
#     file_path = f"/tmp/{project_id}_task_boundary.geojson"

#     # Write the response content to the file
#     with open(file_path, "w") as f:
#         f.write(out)
#     result = await project_crud.convert_geojson_to_osm(file_path)

#     with open(result, "r") as f:
#         content = f.read()

#     response = Response(content=content, media_type="application/xml")
#     return response


@router.get("/centroid/")
async def project_centroid(
    project_user: ProjectUserDict = Depends(mapper),
) -> Feature:
    """Get a centroid of each projects.

    Parameters:
        project_id (int): The ID of the project.
        db (Session): The database session, provided automatically.

    Returns:
        list[tuple[int, str]]: A list of tuples containing the task ID and
            the centroid as a string.
    """
    project = project_user.get("project")
    centroid = project.centroid
    return wkb_geom_to_feature(centroid)


@router.get("/task-status/{uuid}", response_model=project_schemas.BackgroundTaskStatus)
async def get_task_status(
    task_uuid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """Get the background task status by passing the task UUID."""
    # Get the background task status
    task_status, task_message = await project_crud.get_background_task_status(
        task_uuid, db
    )
    return project_schemas.BackgroundTaskStatus(
        status=task_status.name,
        message=task_message or None,
        # progress=some_func_to_get_progress,
    )


@router.get(
    "/project_dashboard/{project_id}", response_model=project_schemas.ProjectDashboard
)
async def project_dashboard(
    db_organisation: db_models.DbOrganisation = Depends(
        organisation_deps.org_from_project
    ),
    project_user: ProjectUserDict = Depends(mapper),
    db: Session = Depends(database.get_db),
):
    """Get the project dashboard details."""
    project = project_user.get("project")
    return await project_crud.get_dashboard_detail(project, db_organisation, db)


@router.get("/contributors/{project_id}")
async def get_contributors(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Get contributors of a project.

    TODO use a pydantic model for return type
    """
    project = project_user.get("project")
    return await project_crud.get_project_users(db, project.id)


@router.post("/add-manager/")
async def add_new_project_manager(
    db: Session = Depends(database.get_db),
    project_user_dict: ProjectUserDict = Depends(project_manager),
):
    """Add a new project manager.

    The logged in user must be either the admin of the organisation or a super admin.
    """
    return await project_crud.add_project_manager(
        db, project_user_dict["user"], project_user_dict["project"]
    )
