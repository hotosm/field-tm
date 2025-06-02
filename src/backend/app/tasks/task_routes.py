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
"""Routes for Field-TM tasks."""

from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection

from app.auth.auth_schemas import ProjectUserDict
from app.auth.providers.osm import init_osm_auth
from app.auth.roles import Mapper, super_admin
from app.db.database import db_conn
from app.db.enums import HTTPStatus, TaskEvent
from app.db.models import DbProjectTeam, DbTask, DbTaskEvent, DbUser
from app.projects import project_deps
from app.tasks import task_crud, task_deps, task_schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=list[task_schemas.TaskOut])
async def read_tasks(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get all task details for a project."""
    return await DbTask.all(db, project_id)


@router.post("/near_me", response_model=task_schemas.TaskOut)
async def get_tasks_near_me(
    lat: float, long: float, project_id: int = None, user_sub: str = None
):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/activity", response_model=list[task_schemas.TaskEventCount])
async def task_activity(
    project_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
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
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get a specific task by it's ID."""
    try:
        return await DbTask.one(db, task_id)
    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


@router.post("/{task_id}/event", response_model=task_schemas.TaskEventOut)
async def add_new_task_event(
    request: Request,
    task: Annotated[DbTask, Depends(task_deps.get_task)],
    new_event: task_schemas.TaskEventIn,
    project_user: Annotated[ProjectUserDict, Depends(Mapper(check_completed=True))],
    db: Annotated[Connection, Depends(db_conn)],
    osm_auth: Annotated[Auth, Depends(init_osm_auth)],
    team: Annotated[Optional[DbProjectTeam], Depends(project_deps.get_project_team)],
    assignee_sub: Optional[str] = None,
    notify: bool = False,
):
    """Add a new event to the events table / update task status."""
    user_sub = project_user.get("user").sub

    log.info(f"Task {task.id} event: {new_event.event.name} (by user {user_sub})")
    new_event.user_sub = user_sub
    new_event.task_id = task.id

    if new_event.event == TaskEvent.ASSIGN:
        if not (assignee_sub or team.team_id):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Assignee or Team ID is required for ASSIGN event",
            )

        # NOTE: This is saving the assignee instead of the current user if assignee is
        # provided else it will save the team if team is provided
        if assignee_sub:
            new_event.user_sub = assignee_sub
        elif team:
            new_event.user_sub = None
            new_event.username = None
            new_event.team_id = team.team_id

    event = await DbTaskEvent.create(db, new_event)

    if notify and event.event == TaskEvent.ASSIGN and (assignee_sub or team):
        await task_crud.send_task_assignment_notifications(
            request, osm_auth, team, project_user, task, assignee_sub
        )

    return event


@router.get("/{task_id}/history", response_model=list[task_schemas.TaskEventOut])
async def get_task_event_history(
    task_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    days: int = 10,
    comments: bool = False,
):
    """Get the detailed history for a task."""
    return await DbTaskEvent.all(db, task_id=task_id, days=days, comments=comments)


@router.post("/unlock-tasks")
async def unlock_tasks(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[DbUser, Depends(super_admin)],
):
    """Endpoint to trigger unlock_old_locked_tasks manually."""
    log.info("Start processing inactive tasks")
    await task_crud.trigger_unlock_tasks(db)
    log.info("Finished processing inactive tasks")
    return {"message": "Old locked tasks unlocked successfully."}
