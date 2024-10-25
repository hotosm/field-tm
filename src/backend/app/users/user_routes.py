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
"""Endpoints for users and role."""

from typing import Annotated, List

from fastapi import APIRouter, Depends
from psycopg import Connection

from app.auth.roles import mapper, super_admin
from app.db.database import db_conn
from app.db.enums import UserRole as UserRoleEnum
from app.db.models import DbUser
from app.users import user_schemas
from app.users.user_deps import get_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[user_schemas.UserOut])
async def get_users(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[DbUser, Depends(super_admin)],
):
    """Get all user details."""
    return await DbUser.all(db)


@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_identifier(
    user: Annotated[DbUser, Depends(get_user)],
    current_user: Annotated[DbUser, Depends(super_admin)],
):
    """Get a single users details.

    The OSM ID should be used.
    If this is not known, the endpoint falls back to searching
    for the username.
    """
    return user


@router.get("/user-role-options/")
async def get_user_roles(current_user: Annotated[DbUser, Depends(mapper)]):
    """Check for available user role options."""
    user_roles = {}
    for role in UserRoleEnum:
        user_roles[role.name] = role.value
    return user_roles
