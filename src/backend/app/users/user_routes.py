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
def get_users(
    username: str = "",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users
    # TODO error thrown when no users are in db


@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_id(id: int, db: Session = Depends(database.get_db)):
    user = user_crud.get_user(db, user_id=id)
    if user:
        user.role = user.role.name
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/user-role")
async def create_user_role(
    user_role: user_schemas.UserRoles, db: Session = Depends(database.get_db)
):
    """This api creates a new role for the user.
    The role can be Admin, Organization Admin, Field Admin, Mapper, Validator or Read Only.

    Request Parameters:
        user_id (required): ID of the user for whom the role is being created
        organization_id (optional): ID of the organization for which the user is being assigned a role
        project_id (optional): ID of the project for which the user is being assigned a role
        role (required): Role being assigned to the user

    Response:
        Status Code 200 (OK): If the role is successfully created
        Status Code 400 (Bad Request): If the user is already assigned a role
    """
    existing_user_role = user_crud.get_user_role_by_user_id(
        db, user_id=user_role.user_id
    )
    if existing_user_role is not None:
        raise HTTPException(status_code=400, detail="User is already assigned a role")

    user = user_crud.get_user(db, user_id=user_role.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    print("Hellooo")

    return await user_crud.create_user_roles(user_role, db)


@router.get("/user-role-options/")
async def get_user_roles():
    user_roles = {}
    for role in UserRoleEnum:
        user_roles[role.name] = role.value
    return user_roles
