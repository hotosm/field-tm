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


from typing import Union

from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger as log
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_models import DbUser
from app.models.enums import HTTPStatus
from app.users.user_crud import get_user, get_user_by_username


async def user_exists_in_db(
    user_id: Union[str, int],
    db: Session = Depends(get_db),
) -> DbUser:
    """Check if a user exists, else Error.

    Args:
        user_id (Union[str, int]): The user ID (integer) or username (string) to check.
        db (Session, optional): The SQLAlchemy database session.

    Returns:
        DbUser: The user if found.

    Raises:
        HTTPException: Raised with a 404 status code if the user is not found.
    """
    try:
        user_id = int(user_id)
    except ValueError:
        pass

    if isinstance(user_id, int):
        log.debug(f"Getting user by ID: {user_id}")
        db_user = await get_user(db, user_id)

    if isinstance(user_id, str):
        log.debug(f"Getting user by username: {user_id}")
        db_user = await get_user_by_username(db, user_id)

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"User {user_id} does not exist",
        )

    return db_user
