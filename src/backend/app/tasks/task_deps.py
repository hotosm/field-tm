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

from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from psycopg import Connection

from app.db.database import db_conn
from app.db.db_schemas import DbTask
from app.models.enums import HTTPStatus


async def get_task(
    db: Annotated[Connection, Depends(db_conn)],
    task_id: int,
):
    """Get a task by it's ID, used as route dependency."""
    try:
        return await DbTask.one(db, task_id)
    except KeyError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=str(e),
        ) from e
