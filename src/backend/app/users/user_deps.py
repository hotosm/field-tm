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

"""User dependencies for use in Depends."""

from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from psycopg import Connection

from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbUser


async def get_user(sub: str, db: Annotated[Connection, Depends(db_conn)]) -> DbUser:
    """Return a user from the DB, else exception.

    Args:
        sub (str): The user ID with provider.
        db (Connection): The database connection.

    Returns:
        DbUser: The user if found.

    Raises:
        HTTPException: Raised with a 404 status code if the user is not found.
    """
    try:
        return await DbUser.one(db, sub)
    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
