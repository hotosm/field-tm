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
"""Endpoints for users and role."""

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)
from fastapi.responses import JSONResponse
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import AuthUser, login_required
from app.auth.auth_schemas import OrgUserDict
from app.auth.providers.osm import check_osm_user, init_osm_auth
from app.auth.roles import (
    Mapper,
    ProjectUserDict,
    field_manager,
    super_admin,
)
from app.config import settings
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.enums import UserRole as UserRoleEnum
from app.db.models import DbUser, DbUserInvite, DbUserRole
from app.users import user_schemas
from app.users.user_crud import (
    get_paginated_users,
    process_inactive_users,
    send_invitation_message,
)
from app.users.user_deps import get_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=user_schemas.PaginatedUsers)
async def get_users(
    db: Annotated[Connection, Depends(db_conn)],
    _: Annotated[OrgUserDict, Depends(super_admin)],
    page: int = Query(1, ge=1),
    results_per_page: int = Query(13, le=100),
    search: str = "",
    signin_type: Literal["osm", "google"] = Query(
        None, description="Filter by signin type (osm or google)"
    ),
):
    """Get all user details."""
    return await get_paginated_users(db, page, results_per_page, search, signin_type)


@router.get("/usernames", response_model=list[user_schemas.Usernames])
async def get_userlist(
    db: Annotated[Connection, Depends(db_conn)],
    search: str = "",
    signin_type: Literal["osm", "google"] = Query(
        None, description="Filter by signin type (osm or google)"
    ),
):
    """Get all user list with info such as id and username."""
    users = await DbUser.all(db, search=search, signin_type=signin_type)
    if not users:
        return []
    return [
        user_schemas.Usernames(sub=user.sub, username=user.username) for user in users
    ]


@router.get("/user-role-options")
async def get_user_roles(_: Annotated[DbUser, Depends(Mapper())]):
    """Check for available user role options."""
    user_roles = {}
    for role in UserRoleEnum:
        user_roles[role.name] = role.value
    return user_roles


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


@router.get("/invites", response_model=list[DbUserInvite])
async def get_project_user_invites(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(field_manager)],
):
    """Get all user invites for a project."""
    project_id = project_user_dict.get("project").id
    return await DbUserInvite.all(db, project_id)


@router.post("/invite")
async def invite_new_user(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(field_manager)],
    user_in: user_schemas.UserInviteIn,
    osm_auth=Depends(init_osm_auth),
):
    """Invite a user to a project.

    If the user already exists, directly assign the role to the user.
    If the user does not exist, create an invite and send an email or OSM message.
    The invite URL is user specific with a token that expires after 7 days.
    - Including `osm_username` will send an OSM message notification (including email).
    - Including `email` will send an email to the user.
    - It's also possible to send the returned invite URL to the user via other means
    (e.g. mobile message).
    """
    project = project_user_dict.get("project")

    if user_in.osm_username:
        if await check_osm_user(user_in.osm_username):
            username = user_in.osm_username
            signin_type = "osm"
            domain = settings.FMTM_DOMAIN
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"OSM user not found: {user_in.osm_username}",
            )
    elif user_in.email:
        username = user_in.email.split("@")[0]
        signin_type = "google"
        # We use different domain for non OSM users since they can't access the
        # management interface
        domain = f"mapper.{settings.FMTM_DOMAIN}"
    else:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Either osm username or google email must be provided.",
        )

    # The user is unique by username and auth provider
    if users := await DbUser.all(db, username=username, signin_type=signin_type):
        user = users[0]
        latest_role = await DbUserRole.create(db, project.id, user.sub, user_in.role)

        return JSONResponse(
            status_code=HTTPStatus.CREATED,
            content={
                "message": f"User {user.username} already exists. "
                f"Role Assigned: {latest_role.role.value}."
            },
        )

    # Generate invite URL
    new_invite = await DbUserInvite.create(db, project.id, user_in)

    if settings.DEBUG:
        invite_url = (
            f"http://{domain}:{settings.FMTM_DEV_PORT}/invite?token={new_invite.token}"
        )
    else:
        invite_url = f"https://{domain}/invite?token={new_invite.token}"

    background_tasks.add_task(
        send_invitation_message,
        request=request,
        project=project,
        invitee_username=username,
        osm_auth=osm_auth,
        invite_url=invite_url,
        user_email=user_in.email,
        signin_type=signin_type,
    )
    return JSONResponse(status_code=HTTPStatus.OK, content={"invite_url": invite_url})


@router.get("/invite/{token}")
async def accept_invite(
    token: str,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Accept a user invite token and generate relevant DB entries."""
    invite = await DbUserInvite.one(db, token)
    if not invite or invite.is_expired():
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Invite has expired"
        )

    if (invite.osm_username and invite.osm_username != current_user.username) or (
        invite.email and invite.email != current_user.email
    ):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Invite is not for the current user.",
        )

    # Create the role for the user / project
    await DbUserRole.create(db, invite.project_id, current_user.sub, invite.role)
    # Expire the token
    await DbUserInvite.update(
        db,
        invite.token,
        user_update=user_schemas.UserInviteUpdate(used_at=datetime.now(timezone.utc)),
    )

    return Response(status_code=HTTPStatus.OK)


@router.patch("/{user_sub}", response_model=user_schemas.UserOut)
async def update_existing_user(
    user_sub: str,
    new_user_data: user_schemas.UserUpdate,
    _: Annotated[DbUser, Depends(super_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Change the role of a user."""
    return await DbUser.update(db=db, user_sub=user_sub, user_update=new_user_data)


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
    await DbUser.delete(db, user.sub)
    log.info(f"User {user.sub} deleted successfully.")
    return Response(status_code=HTTPStatus.NO_CONTENT)
