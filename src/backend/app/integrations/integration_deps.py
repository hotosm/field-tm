# Copyright (c) Humanitarian OpenStreetMap Team
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

"""Integration dependencies, for API token validation."""

from typing import Annotated

from fastapi import (
    Depends,
    Header,
)
from fastapi.exceptions import HTTPException
from psycopg import Connection
from psycopg.rows import class_row

from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbUser


async def valid_api_token(
    db: Annotated[Connection, Depends(db_conn)],
    x_api_key: Annotated[str, Header()],
) -> DbUser:
    """Check the API token is present for an active database user.

    A header X-API-Key must be provided in the request.

    TODO currently this only checks for a valid key, but does not
    TODO include checking roles.
    TODO If roles other than 'mapper' are required, this should be integrated.
    """
    async with db.cursor(row_factory=class_row(DbUser)) as cur:
        await cur.execute(
            """
                SELECT *
                FROM users
                WHERE api_key = %(api_key)s
                AND is_email_verified = TRUE;
            """,
            {"api_key": x_api_key},
        )
        db_user = await cur.fetchone()
        if not db_user:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail=f"API key invalid: ({x_api_key})",
            )

    return db_user
