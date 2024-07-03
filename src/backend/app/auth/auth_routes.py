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

import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.auth_schemas import AuthUser, AuthUserWithToken, FMTMUser
from app.auth.osm import (
    create_tokens,
    extract_refresh_token_from_cookie,
    init_osm_auth,
    login_required,
    refresh_access_token,
    set_cookies,
    verify_token,
)
from app.config import settings
from app.db import database
from app.models.enums import HTTPStatus, UserRole

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/osm-login/")
async def login_url(osm_auth=Depends(init_osm_auth)):
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
    try:
        log.debug(f"Callback url requested: {request.url}")

        # Enforce https callback url for openstreetmap.org
        callback_url = str(request.url).replace("http://", "https://")

        # Get access token
        access_token = osm_auth.callback(callback_url).get("access_token")
        log.debug(f"Access token returned of length {len(access_token)}")
        osm_user = osm_auth.deserialize_access_token(access_token)
        user_data = {
            "sub": f"fmtm|{osm_user['id']}",
            "aud": settings.FMTM_DOMAIN,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,  # expiry set to 1 day
            "username": osm_user["username"],
            "email": osm_user.get("email"),
            "picture": osm_user.get("img_url"),
            "role": UserRole.MAPPER,
        }
        access_token, refresh_token = create_tokens(user_data)
        return set_cookies(access_token, refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail=f"Invalid OSM token: {e}"
        ) from e


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
        upsert_sql = text(
            """
            WITH upserted_user AS (
                INSERT INTO users (
                    id, username, profile_img, role, mapping_level,
                    is_email_verified, is_expert, tasks_mapped, tasks_validated,
                    tasks_invalidated, date_registered, last_validation_date
                ) VALUES (
                    :user_id, :username, :profile_img, :role,
                    'BEGINNER', FALSE, FALSE, 0, 0, 0, NOW(), NOW()
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    profile_img = EXCLUDED.profile_img
                RETURNING id, username, profile_img, role
            )
            SELECT
                u.id, u.username, u.profile_img, u.role,
                array_agg(
                    DISTINCT om.organisation_id
                ) FILTER (WHERE om.organisation_id IS NOT NULL) as orgs_managed,
                jsonb_object_agg(
                    ur.project_id,
                    COALESCE(ur.role, 'MAPPER')
                ) FILTER (WHERE ur.project_id IS NOT NULL) as project_roles
            FROM upserted_user u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN organisation_managers om ON u.id = om.user_id
            GROUP BY u.id, u.username, u.profile_img, u.role;
            """
        )

        parameters = {
            "user_id": user_data.id,
            "username": user_data.username,
            "profile_img": user_data.picture or "",
            "role": UserRole(user_data.role).name,
        }
        result = db.execute(upsert_sql, parameters)
        db.commit()

        db_user_details = result.first()
        if not db_user_details:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User ID ({user_data.id}) could not be inserted in db",
            )

        return db_user_details

    except Exception as e:
        db.rollback()
        log.error(f"Exception occurred: {e}")
        if 'duplicate key value violates unique constraint "users_username_key"' in str(
            e
        ):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User with this username {user_data.username} already exists.",
            ) from e
        else:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail=str(e)
            ) from e


@router.get("/me/", response_model=FMTMUser)
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


@router.get("/refresh", response_model=AuthUserWithToken)
async def refresh_token(
    request: Request, user_data: AuthUser = Depends(login_required)
):
    """Uses the refresh token to generate a new access token."""
    try:
        refresh_token = extract_refresh_token_from_cookie(request)
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token provided")

        token_data = verify_token(refresh_token)
        access_token = refresh_access_token(token_data)

        response = JSONResponse(
            status_code=HTTPStatus.OK,
            content={
                "token": access_token,
                **user_data.model_dump(),
            },
        )
        cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
        response.set_cookie(
            key=cookie_name,
            value=access_token,
            max_age=3600,
            expires=3600,
            path="/",
            domain=settings.FMTM_DOMAIN,
            secure=False if settings.DEBUG else True,
            httponly=True,
            samesite="lax",
        )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to refresh the access token: {e}",
        ) from e


@router.get("/temp-login")
async def temp_login(
    # email: Optional[str] = None,
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
    username = "svcfmtm"
    jwt_data = {
        "sub": "fmtm|20386219",
        "aud": settings.FMTM_DOMAIN,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # set token expiry to 1hr
        "username": username,
        "picture": None,
        "role": UserRole.MAPPER,
    }
    access_token, refresh_token = create_tokens(jwt_data)
    return set_cookies(access_token, refresh_token)
