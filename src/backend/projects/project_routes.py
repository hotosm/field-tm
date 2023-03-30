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

import json
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.logger import logger as logger
from sqlalchemy.orm import Session

from ..central import central_crud
from ..db import database
from . import project_crud, project_schemas

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[project_schemas.ProjectOut])
async def read_projects(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    projects = project_crud.get_projects(db, user_id, skip, limit)
    return projects


@router.post("/near_me", response_model=project_schemas.ProjectSummary)
def get_task(lat: float, long: float, user_id: int = None):
    return "Coming..."


@router.get("/summaries", response_model=List[project_schemas.ProjectSummary])
async def read_project_summaries(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    projects = project_crud.get_project_summaries(db, user_id, skip, limit)
    return projects


@router.get("/{project_id}", response_model=project_schemas.ProjectOut)
async def read_project(project_id: int, db: Session = Depends(database.get_db)):
    project = project_crud.get_project_by_id(db, project_id)
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/delete/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    """Delete a project from ODK Central and the local database."""
    # FIXME: should check for error
    central_crud.delete_odk_project(project_id)
    # if not odkproject:
    #     logger.error(f"Couldn't delete project {project_id} from the ODK Central server")
    project = project_crud.delete_project_by_id(db, project_id)
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/create_project", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.BETAProjectUpload,
    db: Session = Depends(database.get_db),
):
    """Create a project in ODK Central and the local database."""
    odkproject = central_crud.create_odk_project(project_info.project_info.name)
    # TODO check token against user or use token instead of passing user
    # project_info.project_name_prefix = project_info.project_info.name
    project = project_crud.create_project_with_project_info(
        db, project_info, odkproject["id"]
    )

    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.put("/project/{id}", response_model=project_schemas.ProjectOut)
async def update_project(
    id : int,
    project_info: project_schemas.BETAProjectUpload,
    db: Session = Depends(database.get_db)
    ):
    """
    Update an existing project by ID.

    Parameters:
    - id: ID of the project to update
    - author: Author username and id
    - project_info: Updated project information

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """

    project = project_crud.update_project_info(
        db, project_info, id
    )
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/project/{id}", response_model=project_schemas.ProjectOut)
async def project_partial_update(
    id : int,
    project_info: project_schemas.ProjectUpdate,
    db: Session = Depends(database.get_db)
    ):

    """
    Partial Update an existing project by ID.

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
    
    # Update project informations 
    project = project_crud.partial_update_project_info(
        db, project_info, id
    )

    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/beta/{project_id}/upload")
async def upload_project_boundary_with_zip(
    project_id: int,
    project_name_prefix: str,
    task_type_prefix: str,
    upload: UploadFile,
    db: Session = Depends(database.get_db),
):
    """Upload a ZIP with task geojson polygons and QR codes for an existing project.

    {PROJECT_NAME}/\n
    ├─ {PROJECT_NAME}.geojson\n
    ├─ {PROJECT_NAME}_polygons.geojson\n
    ├─ geojson/\n
    │  ├─ {PROJECT_NAME}_TASK_TYPE__{TASK_NUM}.geojson\n
    ├─ QR_codes/\n
    │  ├─ {PROJECT_NAME}_{TASK_TYPE}__{TASK_NUM}.png\n
    """
    # TODO: consider replacing with this: https://stackoverflow.com/questions/73442335/how-to-upload-a-large-file-%e2%89%a53gb-to-fastapi-backend/73443824#73443824
    project = project_crud.update_project_with_zip(
        db, project_id, project_name_prefix, task_type_prefix, upload
    )
    if project:
        return project

    return {"Message": "Uploading project ZIP failed"}


@router.post("/{project_id}/upload_xlsform")
async def upload_custom_xls(
    project_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    # read entire file
    content = await upload.read()
    category = upload.filename.split(".")[0]
    project_crud.upload_xlsform(db, project_id, content, category)

    # FIXME: fix return value
    return {"Message": f"{project_id}"}


@router.post("/{project_id}/upload_multi_polygon")
async def upload_multi_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    ):

    '''
    This API allows for the uploading of a multi-polygon project boundary 
        in JSON format for a specified project ID. Each polygon in the uploaded geojson are made a single task.

    Required Parameters:
    project_id: ID of the project to which the boundary is being uploaded.
    upload: a file upload containing the multi-polygon boundary in geojson format.

    Returns:
    A success message indicating that the boundary was successfully uploaded.
    If the project ID does not exist in the database, an HTTP 428 error is raised.
    '''

    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    '''Create tasks for each polygon '''
    result = project_crud.update_multi_polygon_project_boundary(db, project_id, boundary)

    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    return {"message":"Project Boundary Uploaded",
            "project_id": f"{project_id}"}


@router.post("/{project_id}/upload")
async def upload_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    dimension : int = 500,
    db: Session = Depends(database.get_db),
):
    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    result = project_crud.update_project_boundary(db, project_id, boundary, dimension)
    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    # Use the ID we get from Central, as it's needed for many queries
    eval(project_crud.create_task_grid(db, project_id, dimension))
    # type = DataCategory()
    # result = project_crud.generate_appuser_files(db, grid, project_id)

    return {"message":"Project Boundary Uploaded",
            "project_id": f"{project_id}"}


@router.post("/{project_id}/download")
async def download_project_boundary(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the boundary polygon for this project."""
    out = project_crud.download_geometry(db, project_id, False)
    # FIXME: fix return value
    return {"Message": out}


@router.post("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the task boundary polygons for this project."""
    out = project_crud.download_geometry(db, project_id, True)
    # FIXME: fix return value
    return {"Message": out}


@router.post("/{project_id}/generate")
async def generate_files(
    project_id: int,
    dbname: str,
    category: str,
    db: Session = Depends(database.get_db),
):
    project_crud.generate_appuser_files(db, dbname, category, project_id)

    # FIXME: fix return value
    return {"Message": f"{project_id}"}
