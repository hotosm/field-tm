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
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..db import database
from ..models.enums import TaskStatus
from ..projects import project_crud, project_schemas
from ..users import user_schemas
from . import tasks_crud, tasks_schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/task-list", response_model=List[tasks_schemas.Task])
async def read_task_list(
    project_id: int,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    tasks = await tasks_crud.get_tasks(db, project_id, limit)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return tasks


@router.get("/", response_model=List[tasks_schemas.Task])
async def read_tasks(
    project_id: int,
    user_id: int = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    if user_id:
        raise HTTPException(
            status_code=300,
            detail="Please provide either user_id OR task_id, not both.",
        )

    tasks = await tasks_crud.get_tasks(db, project_id, user_id, skip, limit)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return tasks


@router.get("/point_on_surface")
async def get_point_on_surface(project_id: int, db: Session = Depends(database.get_db)):
    """Get a point on the surface of the geometry for each task of the project.

    Parameters:
        project_id (int): The ID of the project.

    Returns:
        List[Tuple[int, str]]: A list of tuples containing the task ID and the centroid as a string.
    """
    query = text(
        f"""
            SELECT id, ARRAY_AGG(ARRAY[ST_X(ST_PointOnSurface(outline)), ST_Y(ST_PointOnSurface(outline))]) AS point
            FROM tasks
            WHERE project_id = {project_id}
            GROUP BY id; """
    )

    result = db.execute(query)
    result_dict_list = [{"id": row[0], "point": row[1]} for row in result.fetchall()]
    return result_dict_list


@router.post("/near_me", response_model=tasks_schemas.Task)
async def get_tasks_near_me(
    lat: float, long: float, project_id: int = None, user_id: int = None
):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/{task_id}", response_model=tasks_schemas.Task)
async def read_tasks(task_id: int, db: Session = Depends(database.get_db)):
    task = await tasks_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/new_status/{new_status}", response_model=tasks_schemas.Task)
async def update_task_status(
    user: user_schemas.User,
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(database.get_db),
):
    # TODO verify logged in user
    user_id = user.id

    task = await tasks_crud.update_task_status(db, user_id, task_id, new_status)
    if not task:
        raise HTTPException(status_code=404, detail="Task status could not be updated.")
    return task


@router.post("/task-qr-code/{task_id}")
async def get_qr_code_list(
    task_id: int,
    db: Session = Depends(database.get_db),
):
    return await tasks_crud.get_qr_codes_for_task(db=db, task_id=task_id)


@router.post("/edit-task-boundary")
async def edit_task_boundary(
    task_id: int,
    boundary: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    # read entire file
    content = await boundary.read()
    boundary_json = json.loads(content)

    edit_boundary = await tasks_crud.edit_task_boundary(db, task_id, boundary_json)

    return edit_boundary


@router.get("/tasks-features/")
async def task_features_count(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    # Get the project object.
    project = await project_crud.get_project(db, project_id)

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project.odk_central_url,
        odk_central_user=project.odk_central_user,
        odk_central_password=project.odk_central_password,
    )

    odk_details = central_crud.list_odk_xforms(project.odkid, odk_credentials, True)

    # Assemble the final data list
    data = []
    for x in odk_details:
        feature_count_query = text(
            f"""
            select count(*) from features where project_id = {project_id} and task_id = {x['xmlFormId']}
        """
        )

        result = db.execute(feature_count_query)
        feature_count = result.fetchone()

        data.append(
            {
                "task_id": x["xmlFormId"],
                "submission_count": x["submissions"],
                "last_submission": x["lastSubmission"],
                "feature_count": feature_count[0],
            }
        )

    return data
