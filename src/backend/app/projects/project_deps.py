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

"""Project dependencies and helpers for projects."""

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection

from app.db.models import DbProject


async def get_project_by_id(
    db: AsyncConnection, project_id: int, minimal: bool = False
):
    """Get a single project by it's ID."""
    try:
        return await DbProject.one(
            db, project_id, minimal=minimal, warn_on_missing_token=False
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


async def project_name_does_not_already_exist(db: AsyncConnection, project_name: str):
    """Simple check if project already exists with name."""
    # Check if the project name already exists
    sql = """
        SELECT EXISTS (
            SELECT 1 FROM projects
            WHERE LOWER(project_name) = %(project_name)s
        )
    """
    async with db.cursor() as cur:
        await cur.execute(sql, {"project_name": project_name.lower()})
        project_exists = await cur.fetchone()
    if project_exists:
        return project_exists[0]
    return False
