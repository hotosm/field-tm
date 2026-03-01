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
"""Endpoints for users and roles."""

import logging
from typing import Literal

from litestar import Router, delete, get, patch
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.roles import super_admin
from app.db.database import db_conn
from app.db.models import DbUser
from app.helpers import helper_schemas
from app.users import user_schemas
from app.users.user_crud import get_paginated_users

log = logging.getLogger(__name__)


@get(
    "",
    summary="Get all user details.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    return_dto=user_schemas.UserOut,
)
async def get_users(  # noqa: PLR0913
    db: AsyncConnection,
    current_user: DbUser,
    page: int = Parameter(1, ge=1),
    results_per_page: int = Parameter(13, le=100),
    search: str = "",
    signin_type: Literal["osm"] | None = Parameter(
        default=None, description="Filter by signin type (osm or google)"
    ),
) -> helper_schemas.PaginatedResponse[DbUser]:
    """Get all user details."""
    return await get_paginated_users(db, page, results_per_page, search, signin_type)


@get(
    "/usernames",
    summary="Get all user list with info such as id and username.",
    dependencies={"db": Provide(db_conn)},
    return_dto=user_schemas.Usernames,
)
async def get_userlist(
    db: AsyncConnection,
    search: str = "",
    signin_type: Literal["osm"] | None = Parameter(
        default=None, description="Filter by signin type (osm or google)"
    ),
) -> list[DbUser]:
    """Get all user list with info such as id and username."""
    users = await DbUser.all(db, search=search, signin_type=signin_type)
    return users or []


@get(
    "/{user_sub:str}",
    summary="Get a single user details.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    return_dto=user_schemas.UserOut,
)
async def get_user_by_identifier(
    user_sub: str,
    current_user: DbUser,
    db: AsyncConnection,
) -> DbUser:
    """Get a single users details.

    The user_sub should be used (OSM ID format like 'osm|123456').
    """
    try:
        user = await DbUser.one(db, user_sub)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return user


@patch(
    "/{user_sub:str}",
    summary="Update an existing user.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    dto=user_schemas.UserUpdate,
    return_dto=user_schemas.UserOut,
)
async def update_existing_user(
    user_sub: str,
    current_user: DbUser,
    db: AsyncConnection,
    data: DbUser,
) -> DbUser:
    """Update field for an existing user."""
    return await DbUser.update(
        db=db,
        user_sub=user_sub,
        user_update=data,
    )


@delete(
    "/{user_sub:str}",
    summary="Delete a single user.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_by_identifier(
    user_sub: str,
    current_user: DbUser,
    db: AsyncConnection,
) -> None:
    """Delete a single user."""
    log.info(f"User {current_user.username} attempting deletion of user {user_sub}")

    user_to_delete = await DbUser.one(db, user_sub)
    await DbUser.delete(db, user_to_delete.sub)

    log.info(f"User {user_to_delete.sub} deleted successfully.")


user_router = Router(
    path="/users",
    tags=["users"],
    route_handlers=[
        get_users,
        get_userlist,
        update_existing_user,
        get_user_by_identifier,
        delete_user_by_identifier,
    ],
)
