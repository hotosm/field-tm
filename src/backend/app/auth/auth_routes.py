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

"""Auth routes, to login, logout, and get user details."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.osm import AuthUser, init_osm_auth, login_required
from app.config import settings
from app.db import database
from app.models.enums import UserRole

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/osm_login/")
async def login_url(request: Request, osm_auth=Depends(init_osm_auth)):
    """Get Login URL for OSM Oauth Application.

    The application must be registered on openstreetmap.org.
    Open the download url returned to get access_token.

    Args:
        request: The GET request.
        osm_auth: The Auth object from osm-login-python.

    Returns:
        login_url (string): URL to authorize user in OSM.
            Includes URL params: client_id, redirect_uri, permission scope.
    """
    login_url = osm_auth.login()
    log.debug(f"Login URL returned: {login_url}")
    return JSONResponse(content=login_url, status_code=200)


@router.get("/callback/")
async def callback(request: Request, osm_auth=Depends(init_osm_auth)):
    """Performs oauth token exchange with OpenStreetMap.

    Provides an access token that can be used for authenticating other endpoints.
    Also returns a cookie containing the access token for persistence in frontend apps.

    Args:
        request: The GET request.
        request: The response, including a cookie.
        osm_auth: The Auth object from osm-login-python.

    Returns:
        access_token (string): The access token provided by the login URL request.
    """
    log.debug(f"Callback url requested: {request.url}")

    # Enforce https callback url for openstreetmap.org
    callback_url = str(request.url).replace("http://", "https://")

    # Get access token
    access_token = osm_auth.callback(callback_url).get("access_token")
    log.debug(f"Access token returned of length {len(access_token)}")
    response = JSONResponse(content={"access_token": access_token}, status_code=200)

    # Set cookie
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    log.debug(
        f"Setting cookie in response named '{cookie_name}' with params: "
        f"max_age=259200 | expires=259200 | path='/' | "
        f"domain={settings.FMTM_DOMAIN} | httponly=True | samesite='lax' | "
        f"secure={False if settings.DEBUG else True}"
    )
    response.set_cookie(
        key=cookie_name,
        value=access_token,
        max_age=31536000,  # OSM currently has no expiry
        expires=31536000,  # OSM currently has no expiry,
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/logout/")
async def logout():
    """Reset httpOnly cookie to sign out user."""
    response = Response(status_code=200)
    # Reset cookie (logout)
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    log.debug(f"Resetting cookie in response named '{cookie_name}'")
    response.set_cookie(
        key=cookie_name,
        value="",
        max_age=0,  # Set to expire immediately
        expires=0,  # Set to expire immediately
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )
    return response


async def get_or_create_user(
    db: Session,
    user_data: AuthUser,
):
    """Get user from User table if exists, else create."""
    try:
        update_sql = text(
            """
            INSERT INTO users (
                    id, username, profile_img, role, mapping_level,
                    is_email_verified, is_expert, tasks_mapped, tasks_validated,
                    tasks_invalidated, date_registered, last_validation_date
                    )
                VALUES (
                    :user_id, :username, :profile_img, :role,
                    :mapping_level, FALSE, FALSE, 0, 0, 0,
                    :current_date, :current_date
                    )
            ON CONFLICT (id)
                DO UPDATE SET profile_img = :profile_img;
            """
        )
        role = UserRole(user_data.role).name
        db.execute(
            update_sql,
            {
                "user_id": user_data.id,
                "username": user_data.username,
                "profile_img": user_data.img_url,
                "role": role,
                "mapping_level": "BEGINNER",
                "current_date": datetime.now(timezone.utc),
            },
        )
        db.commit()

        get_sql = text(
            """
            SELECT users.*,
                user_roles.project_id as project_id,
                organisation_managers.organisation_id as created_org,
                COALESCE(user_roles.role, 'MAPPER') as project_role
            FROM users
            LEFT JOIN user_roles ON users.id = user_roles.user_id
            LEFT JOIN organisation_managers on users.id = organisation_managers.user_id
            WHERE users.id = :user_id;
            """
        )
        result = db.execute(
            get_sql,
            {"user_id": user_data.id},
        )
        db_user = result.first()

        user = {
            "id": db_user.id,
            "username": db_user.username,
            "profile_img": db_user.profile_img,
            "role": db_user.role,
            "project_id": db_user.project_id,
            "project_role": db_user.project_role,
            "created_org": db_user.created_org,
        }
        return user

    except Exception as e:
        # Check if the exception is due to username already existing
        if 'duplicate key value violates unique constraint "users_username_key"' in str(
            e
        ):
            raise HTTPException(
                status_code=400,
                detail=f"User with this username {user_data.username} already exists.",
            ) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/me/")
async def my_data(
    db: Session = Depends(database.get_db),
    user_data: AuthUser = Depends(login_required),
):
    """Read access token and get user details from OSM.

    Args:
        db: The db session.
        user_data: User data provided by osm-login-python Auth.

    Returns:
        user_data(dict): The dict of user data.
    """
    return await get_or_create_user(db, user_data)


@router.get("/introspect", response_model=AuthUser)
async def check_login(
    db: Session = Depends(database.get_db),
    user_data: AuthUser = Depends(login_required),
):
    """Verifies the validity of login cookies.

    Returns True if authenticated, False otherwise.
    """
    return user_data


@router.get("/login/")
async def temp_login(
    request: Request,
    email: Optional[str] = None,
):
    """Handles the authentication check endpoint.

    By creating a temporary access token and
    setting it as a cookie.

    Args:
        request (Request): The incoming request object.
        email: email of non-osm user.

    Returns:
        Response: The response object containing the access token as a cookie.
    """
    access_token = settings.OSM_SVC_ACCOUNT_TOKEN
    response = JSONResponse(content={"access_token": access_token}, status_code=200)
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    response.set_cookie(
        key=cookie_name,
        value=access_token,
        max_age=604800,
        expires=604800,  # expiry set to 7 days,
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )
    return response
