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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import database
from ..models.enums import TaskStatus
from ..users import user_schemas
from . import tasks_crud, tasks_schemas


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

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


@router.post("/near_me", response_model=tasks_schemas.TaskOut)
def get_task(lat: float, long: float, project_id: int = None, user_id: int = None):
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