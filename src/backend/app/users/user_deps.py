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

"""User dependencies and helpers."""

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection

from app.db.models import DbUser


async def get_user(sub: str, db: AsyncConnection) -> DbUser:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
