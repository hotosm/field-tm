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

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from loguru import logger as log
from psycopg import Connection

from app.auth.roles import mapper, org_admin, project_manager, super_admin
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.enums import UserRole as UserRoleEnum
from app.db.models import DbUser, DbUserRole
from app.users import user_schemas
from app.users.user_crud import get_paginated_users, process_inactive_users
from app.users.user_deps import get_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=user_schemas.PaginatedUsers)
async def get_users(
    db: Annotated[Connection, Depends(db_conn)],
    _: Annotated[DbUser, Depends(super_admin)],
    page: int = Query(1, ge=1),
    results_per_page: int = Query(13, le=100),
    search: str = "",
):
    """Get all user details."""
    return await get_paginated_users(db, page, results_per_page, search)


@router.get("/usernames", response_model=list[user_schemas.Usernames])
async def get_userlist(
    db: Annotated[Connection, Depends(db_conn)],
    _: Annotated[DbUser, Depends(org_admin)],
    search: str = "",
):
    """Get all user list with info such as id and username."""
    users = await DbUser.all(db, search=search)
    if not users:
        return []
    return [
        user_schemas.Usernames(id=user.id, username=user.username) for user in users
    ]


@router.get("/user-role-options")
async def get_user_roles(_: Annotated[DbUser, Depends(mapper)]):
    """Check for available user role options."""
    user_roles = {}
    for role in UserRoleEnum:
        user_roles[role.name] = role.value
    return user_roles


@router.patch("/{user_id}", response_model=user_schemas.UserOut)
async def update_existing_user(
    user_id: int,
    new_user_data: user_schemas.UserUpdate,
    _: Annotated[DbUser, Depends(super_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Change the role of a user."""
    return await DbUser.update(db=db, user_id=user_id, user_update=new_user_data)


@router.get("/{id}", response_model=user_schemas.UserOut)
async def get_user_by_identifier(
    user: Annotated[DbUser, Depends(get_user)],
    _: Annotated[DbUser, Depends(super_admin)],
):
    """Get a single users details.

    The OSM ID should be used.
    If this is not known, the endpoint falls back to searching
    for the username.
    """
    return user


@router.delete("/{id}")
async def delete_user_by_identifier(
    user: Annotated[DbUser, Depends(get_user)],
    current_user: Annotated[DbUser, Depends(super_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Delete a single user."""
    log.info(
        f"User {current_user.username} attempting deletion of user {user.username}"
    )
    await DbUser.delete(db, user.id)
    log.info(f"User {user.id} deleted successfully.")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/process-inactive-users")
async def delete_inactive_users(
    db: Annotated[Connection, Depends(db_conn)],
    _: Annotated[DbUser, Depends(super_admin)],
):
    """Identify inactive users, send warnings, and delete accounts."""
    log.info("Start processing inactive users")
    await process_inactive_users(db)
    log.info("Finished processing inactive users")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get(
    "/{project_id}/project-users", response_model=list[user_schemas.UserRolesOut]
)
async def get_project_users(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[DbUser, Depends(project_manager)],
):
    """Get project users and their project role."""
    project = project_user_dict.get("project")
    users = await DbUserRole.all(db, project.id)
    if not users:
        return []
    return [
        user_schemas.UserRolesOut(
            user_id=user.user_id, project_id=user.project_id, role=user.role
        )
        for user in users
    ]
