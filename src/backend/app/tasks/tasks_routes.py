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
"""Routes for FMTM tasks."""

import asyncio
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import get_uid, mapper
from app.db import database
from app.models.enums import TaskStatus
from app.tasks import tasks_crud, tasks_schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/task-list", response_model=List[tasks_schemas.Task])
async def read_task_list(
    project_id: int,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """Get the task list for a project.

    FIXME this is broken
    """
    tasks = await tasks_crud.get_tasks(db, project_id, limit)
    updated_tasks = await tasks_crud.update_task_history(tasks, db)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return updated_tasks


@router.get("/", response_model=List[tasks_schemas.Task])
async def read_tasks(
    project_id: int,
    user_id: int = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """Get all task details, either for a project or user."""
    if user_id:
        raise HTTPException(
            status_code=300,
            detail="Please provide either user_id OR task_id, not both.",
        )

    tasks = await tasks_crud.get_tasks(db, project_id, user_id, skip, limit)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return tasks


# TODO remove this? Not used anywhere
# @router.get("/point_on_surface")
# async def get_point_on_surface(project_id: int,
# db: Session = Depends(database.get_db)):
#     """Get a point on the surface of the geometry for each task of the project.

#     Parameters:
#         project_id (int): The ID of the project.

#     Returns:
#         List[Tuple[int, str]]: A list of tuples containing the task ID
#             and the centroid as a string.
#     """
#     query = text(
#         f"""
#             SELECT id,
#             ARRAY_AGG(ARRAY[ST_X(ST_PointOnSurface(outline)),
#             ST_Y(ST_PointOnSurface(outline))]) AS point
#             FROM tasks
#             WHERE project_id = {project_id}
#             GROUP BY id; """
#     )

#     result = db.execute(query)
#     result_dict_list = [
#       {"id": row[0], "point": row[1]} for row in result.fetchall()]
#     return result_dict_list


@router.post("/near_me", response_model=tasks_schemas.Task)
async def get_tasks_near_me(
    lat: float, long: float, project_id: int = None, user_id: int = None
):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/{task_id}", response_model=tasks_schemas.Task)
async def get_specific_task(task_id: int, db: Session = Depends(database.get_db)):
    """Get a specific task by it's ID."""
    task = await tasks_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "/{task_id}/new-status/{new_status}", response_model=tasks_schemas.TaskHistoryOut
)
async def add_new_task_event(
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Add a new event to the events table / update task status."""
    project_id = project_user.get("project").id
    user_id = await get_uid(project_user.get("user"))
    return await tasks_crud.new_task_event(db, project_id, task_id, user_id, new_status)


@router.post("/task-comments/", response_model=tasks_schemas.TaskCommentResponse)
async def add_task_comments(
    comment: tasks_schemas.TaskCommentRequest,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Create a new task comment.

    Parameters:
        comment (TaskCommentRequest): The task comment to be created.
        db (Session): The database session.
        user_data (ProjectUserDict): The authenticated user.

    Returns:
        TaskCommentResponse: The created task comment.
    """
    user_id = await get_uid(project_user.get("user"))
    task_comment_list = await tasks_crud.add_task_comments(db, comment, user_id)
    return task_comment_list


@router.get("/activity/", response_model=List[tasks_schemas.TaskHistoryCount])
async def task_activity(
    project_id: int, days: int = 10, db: Session = Depends(database.get_db)
):
    """Retrieves the validate and mapped task count for a specific project.

    Args:
        project_id (int): The ID of the project.
        days (int): The number of days to consider for the
            task activity (default: 10).
        db (Session): The database session.

    Returns:
        list[TaskHistoryCount]: A list of task history counts.

    """
    end_date = datetime.now() - timedelta(days=days)
    task_list = await tasks_crud.get_task_id_list(db, project_id)
    tasks = []
    for task_id in task_list:
        tasks.extend(
            [tasks_crud.get_project_task_history(task_id, False, end_date, db)]
        )
    task_history = await asyncio.gather(*tasks)
    return await tasks_crud.count_validated_and_mapped_tasks(
        task_history,
        end_date,
    )


@router.get("/{task_id}/history/", response_model=List[tasks_schemas.TaskHistoryOut])
async def task_history(
    task_id: int,
    days: int = 10,
    comment: bool = False,
    db: Session = Depends(database.get_db),
):
    """Get the detailed task history for a project.

    Args:
        task_id (int): The unique task ID in the database.
        days (int): The number of days to consider for the
            task activity (default: 10).
        comment (bool): True or False, True to get comments
            from the project tasks and False by default for
            entire task status history.
        db (Session): The database session.

    Returns:
        List[TaskHistory]: A list of task history.
    """
    end_date = datetime.now() - timedelta(days=days)
    return await tasks_crud.get_project_task_history(task_id, comment, end_date, db)
