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
import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..db import database
from ..models.enums import TaskStatus
from ..users import user_schemas
from . import tasks_crud, tasks_schemas
from ..projects import project_crud, project_schemas
from ..central import central_crud
from sqlalchemy.sql import text


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/task-list", response_model=List[tasks_schemas.TaskOut])
async def read_task_list(
    project_id: int,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
    ):
    tasks = tasks_crud.get_tasks(db, project_id, limit)
    if tasks:
        return tasks
    else:
        raise HTTPException(status_code=404, detail="Tasks not found")
    

@router.get("/", response_model=List[tasks_schemas.TaskOut])
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

    tasks = tasks_crud.get_tasks(db, project_id, user_id, skip, limit)
    if tasks:
        return tasks
    else:
        raise HTTPException(status_code=404, detail="Tasks not found")


@router.get("/point_on_surface")
async def get_point_on_surface(
    project_id:int,
    db: Session = Depends(database.get_db)
    ):

    """
    Get a point on the surface of the geometry for each task of the project.

    Parameters:
        project_id (int): The ID of the project.

    Returns:
        List[Tuple[int, str]]: A list of tuples containing the task ID and the centroid as a string.
    """

    query = text(f"""
            SELECT id, ARRAY_AGG(ARRAY[ST_X(ST_PointOnSurface(outline)), ST_Y(ST_PointOnSurface(outline))]) AS point
            FROM tasks
            WHERE project_id = {project_id}
            GROUP BY id; """)

    result = db.execute(query)
    result_dict_list = [{"id": row[0], "point": row[1]} for row in result.fetchall()]
    return result_dict_list


@router.post("/near_me", response_model=tasks_schemas.TaskOut)
def get_task(lat: float, long: float, project_id: int = None, user_id: int = None):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/{task_id}", response_model=tasks_schemas.TaskOut)
async def read_tasks(task_id: int, db: Session = Depends(database.get_db)):
    task = tasks_crud.get_task(db, task_id)
    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/new_status/{new_status}", response_model=tasks_schemas.TaskOut)
async def update_task_status(
    user: user_schemas.User,
    task_id: int,
    new_status: tasks_schemas.TaskStatusOption,
    db: Session = Depends(database.get_db),
):
    # TODO verify logged in user
    user_id = user.id

    task = tasks_crud.update_task_status(
        db, user_id, task_id, TaskStatus[new_status.name]
    )
    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail="Task status could not be updated.")


@router.post("/task-qr-code/{task_id}")
async def get_qr_code_list(
    task_id: int,
    db: Session = Depends(database.get_db),
):
    return tasks_crud.get_qr_codes_for_task(db=db, task_id=task_id)


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

    task_list = tasks_crud.get_task_lists(db, project_id)

    # Get the project object.
    project = project_crud.get_project(db, project_id)

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url = project.odk_central_url,
        odk_central_user = project.odk_central_user,
        odk_central_password = project.odk_central_password,
        )

    def process_task(task):
        feature_count_query = text(f"""
            select count(*)from features where project_id = {project_id} and task_id = {task}
        """)
        result = db.execute(feature_count_query)
        feature_count = result.fetchone()

        submission_list = central_crud.list_task_submissions(
            project.odkid, task, odk_credentials)

        # form_details = central_crud.get_form_full_details(project.odkid, task, odk_credentials)
        return {
            "task_id": task,
            "feature_count": feature_count[0],
            # 'submission_count': form_details['submissions'],
            "submission_count": len(submission_list)
            if isinstance(submission_list, list)
            else 0,
        }

    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, process_task, task) for task in task_list]
    processed_results = await asyncio.gather(*tasks)

    return processed_results
