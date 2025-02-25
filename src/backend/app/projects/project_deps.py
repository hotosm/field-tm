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

"""Project dependencies for use in Depends."""

from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from psycopg import Connection
from pydantic import Field

from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbProject


async def get_project(
    db: Annotated[Connection, Depends(db_conn)],
    project_id: Annotated[int, Field(gt=0)],
):
    """Wrap get_project_by_id in a route Depends."""
    return await get_project_by_id(db, project_id)


async def get_project_by_id(db: Connection, project_id: int):
    """Get a single project by it's ID."""
    try:
        return await DbProject.one(db, project_id, warn_on_missing_token=False)
    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


async def check_project_dup_name(db: Connection, name: str):
    """Simple check if project already exists with name."""
    # Check if the project name already exists
    sql = """
        SELECT EXISTS (
            SELECT 1 FROM projects
            WHERE LOWER(name) = %(project_name)s
        )
    """
    async with db.cursor() as cur:
        await cur.execute(sql, {"project_name": name.lower()})
        project_exists = await cur.fetchone()
    if project_exists:
        project_exists = project_exists[0]

    if project_exists:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Project with name '{name}' already exists.",
        )
