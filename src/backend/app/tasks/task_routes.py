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

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import get_uid, mapper
from app.db.database import db_conn
from app.db.enums import HTTPStatus, TaskAction, TaskStatus
from app.db.models import DbTask, DbTaskHistory
from app.tasks import task_crud, task_schemas
from app.tasks.task_deps import get_task

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[task_schemas.TaskOut])
async def read_tasks(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get all task details for a project."""
    return await DbTask.all(db, project_id)


@router.post("/near_me", response_model=task_schemas.TaskOut)
async def get_tasks_near_me(
    lat: float, long: float, project_id: int = None, user_id: int = None
):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/{task_id}", response_model=task_schemas.TaskOut)
async def get_specific_task(
    task_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
):
    """Get a specific task by it's ID."""
    try:
        return await DbTask.one(db, task_id)
    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


# TODO SQL update this to be something like /next
@router.post(
    "/{task_id}/new-status/{new_status}", response_model=task_schemas.TaskHistoryOut
)
async def add_new_task_event(
    db_task: Annotated[DbTask, Depends(get_task)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    new_status: TaskStatus,
    db: Annotated[Connection, Depends(db_conn)],
):
    """Add a new event to the events table / update task status."""
    user_id = await get_uid(project_user.get("user"))
    return await task_crud.new_task_event(
        db,
        db_task.id,
        user_id,
        new_status,
    )


@router.post("/{task_id}/comment/", response_model=task_schemas.TaskHistoryOut)
async def add_task_comment(
    comment: str,
    db_task: Annotated[DbTask, Depends(get_task)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Create a new task comment.

    Parameters:
        comment (str): The task comment to add.
        db_task (DbTask): The database task entry.
            Retrieving this ensures the task exists before updating.
        project_user (ProjectUserDict): The authenticated user.
        db (Connection): The database connection.

    Returns:
        TaskHistoryOut: The created task comment.
    """
    user_id = await get_uid(project_user.get("user"))
    new_comment = task_schemas.TaskHistoryIn(
        task_id=db_task.id,
        user_id=user_id,
        action=TaskAction.COMMENT,
        action_text=comment,
    )
    return await DbTaskHistory.create(db, new_comment)


# NOTE this endpoint isn't used?
@router.get("/activity/", response_model=list[task_schemas.TaskHistoryCount])
async def task_activity(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    days: int = 10,
):
    """Get the number of mapped or validated tasks on each day.

    Return format:
    [
        {
            date: DD/MM/YYYY,
            validated: int,
            mapped: int,
        }
    ]
    """
    return await task_crud.get_project_task_activity(db, project_id, days)


@router.get("/{task_id}/history/", response_model=list[task_schemas.TaskHistoryOut])
async def task_history(
    db: Annotated[Connection, Depends(db_conn)],
    db_task: Annotated[DbTask, Depends(get_task)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    days: int = 10,
    comments: bool = False,
):
    """Get the detailed history for a task."""
    return await DbTaskHistory.all(db, task_id=db_task.id, days=days, comments=comments)
