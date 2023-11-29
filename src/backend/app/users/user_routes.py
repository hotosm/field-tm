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

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import database
from ..models.enums import UserRole as UserRoleEnum
from . import user_crud, user_schemas

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[user_schemas.UserOut])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    """Get all user details."""
    users = await user_crud.get_users(db, skip=skip, limit=limit)

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users


@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_identifier(id: str, db: Session = Depends(database.get_db)):
    """Get a single users details.

    The OSM ID should be used.
    If this is not known, the endpoint falls back to searching
    for the username.
    """
    user = None
    # Search by ID
    try:
        osm_id = int(id)
        user = await user_crud.get_user(db, user_id=osm_id)
    except ValueError:
        # Skip if not a valid integer
        pass

    if not user:
        # Search by Username
        user = await user_crud.get_user_by_username(db, username=id)

        # No user found
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/user-role")
async def create_user_role(
    user_role: user_schemas.UserRoles, db: Session = Depends(database.get_db)
):
    """Create a new user role.

    # FIXME is this endpoint really necessary?

    The role can be:
        - Admin
        - Organization Admin
        - Field Admin
        - Mapper
        - Validator
        - Read Only

    The request param `user_role` is a json of user_id, organization_id,
    project_id, user_role:
        user_id (required): ID of the user for whom the role is being created
        organization_id (optional): ID of the organization for which the
            user is being assigned a role
        project_id (optional): ID of the project for which the user is
            being assigned a role
        user_role (required): Role being assigned to the user

    Response:
        Status Code 200 (OK): If the role is successfully created
        Status Code 400 (Bad Request): If the user is already assigned a role
    """
    existing_user_role = await user_crud.get_user_role_by_user_id(
        db, user_id=user_role.user_id
    )
    if existing_user_role is not None:
        raise HTTPException(status_code=400, detail="User is already assigned a role")

    user = await user_crud.get_user(db, user_id=user_role.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return await user_crud.create_user_roles(user_role, db)


@router.get("/user-role-options/")
async def get_user_roles():
    """Check for available user role options."""
    user_roles = {}
    for role in UserRoleEnum:
        user_roles[role.name] = role.value
    return user_roles
