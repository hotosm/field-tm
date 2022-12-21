# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session

from ..db import database
from . import tasks_schemas, tasks_crud

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=tasks_schemas.TaskOut)
async def read_tasks(user_id: int = None, task_id: int = None, skip: int = 0, limit: int = 1000, db: Session = Depends(database.get_db)):
    if user_id and task_id:
        raise HTTPException(status_code=300, detail="Please provide either user_id OR task_id, not both.")
    
    tasks = tasks_crud.get_tasks(db, user_id, task_id, skip, limit)
    if tasks:
        return tasks
    else:
        raise HTTPException(status_code=404, detail="Tasks not found")
