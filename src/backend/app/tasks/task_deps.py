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

"""Task dependencies for use in Depends."""

from fastapi import Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_models import DbTask
from app.models.enums import HTTPStatus


async def get_task_by_id(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
):
    """Get a single task by task index."""
    if (
        db_task := db.query(DbTask)
        .filter(DbTask.project_task_index == task_id, DbTask.project_id == project_id)
        .first()
    ):
        return db_task
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Task with ID {task_id} does not exist",
        )
