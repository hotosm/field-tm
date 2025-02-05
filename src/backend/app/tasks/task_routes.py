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
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import mapper
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbTask, DbTaskEvent
from app.tasks import task_crud, task_schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=list[task_schemas.TaskOut])
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


@router.get("/activity", response_model=list[task_schemas.TaskEventCount])
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


@router.post("/{task_id}/event", response_model=task_schemas.TaskEventOut)
async def add_new_task_event(
    task_id: int,
    new_event: task_schemas.TaskEventIn,
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Add a new event to the events table / update task status."""
    user_id = project_user.get("user").id
    log.info(f"Task {task_id} event: {new_event.event.name} (by user {user_id})")

    new_event.user_id = user_id
    new_event.task_id = task_id
    return await DbTaskEvent.create(db, new_event)


@router.get("/{task_id}/history", response_model=list[task_schemas.TaskEventOut])
async def get_task_event_history(
    task_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(mapper)],
    days: int = 10,
    comments: bool = False,
):
    """Get the detailed history for a task."""
    return await DbTaskEvent.all(db, task_id=task_id, days=days, comments=comments)


@router.post("/unlock-tasks")
async def unlock_tasks(db: Annotated[Connection, Depends(db_conn)]):
    """Endpoint to trigger unlock_old_locked_tasks manually."""
    log.info("Start processing inactive tasks")
    await task_crud.trigger_unlock_tasks(db)
    log.info("Finished processing inactive tasks")
    return {"message": "Old locked tasks unlocked successfully."}
