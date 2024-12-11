# Copyright (c) Humanitarian OpenStreetMap Team
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

from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.auth_deps import (
    create_jwt_tokens,
    get_cookie_value,
    login_required,
    mapper_login_required,
    refresh_jwt_token,
    set_cookies,
    verify_jwt_token,
)
from app.auth.auth_schemas import AuthUser, FMTMUser
from app.auth.providers.osm import handle_osm_callback, init_osm_auth
from app.config import settings
from app.db.database import db_conn
from app.db.enums import HTTPStatus, UserRole
from app.db.models import DbUser

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/osm-login")
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
    return JSONResponse(content=login_url, status_code=HTTPStatus.OK)


@router.get("/callback")
async def callback(
    request: Request, osm_auth: Annotated[AuthUser, Depends(init_osm_auth)]
) -> JSONResponse:
    """Performs oauth token exchange with OpenStreetMap.

    Provides an access token that can be used for authenticating other endpoints.
    Also returns a cookie containing the access token for persistence in frontend apps.
    """
    try:
        response_plus_cookies = await handle_osm_callback(request, osm_auth)
        return response_plus_cookies
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=str(e)) from e


@router.get("/logout")
async def logout():
    """Reset httpOnly cookie to sign out user."""
    response = Response(status_code=HTTPStatus.OK)
    # Reset all cookies (logout)
    fmtm_cookie_name = settings.cookie_name
    refresh_cookie_name = f"{fmtm_cookie_name}_refresh"
    temp_cookie_name = f"{fmtm_cookie_name}_temp"
    temp_refresh_cookie_name = f"{fmtm_cookie_name}_temp_refresh"
    osm_cookie_name = f"{fmtm_cookie_name}_osm"

    for cookie_name in [
        fmtm_cookie_name,
        refresh_cookie_name,
        temp_cookie_name,
        temp_refresh_cookie_name,
        osm_cookie_name,
    ]:
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
    db: Connection,
    user_data: AuthUser,
):
    """Get user from User table if exists, else create."""
    try:
        upsert_sql = """
            WITH upserted_user AS (
                INSERT INTO users (
                    id, username, profile_img, role, registered_at
                ) VALUES (
                    %(user_id)s, %(username)s, %(profile_img)s, %(role)s, NOW()
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    profile_img = EXCLUDED.profile_img
                RETURNING id, username, profile_img, role
            )

            SELECT
                u.id, u.username, u.profile_img, u.role,

                -- Aggregate the organisation IDs managed by the user
                array_agg(
                    DISTINCT om.organisation_id
                ) FILTER (WHERE om.organisation_id IS NOT NULL) AS orgs_managed,

                -- Aggregate project roles for the user, as project:role pairs
                jsonb_object_agg(
                    ur.project_id,
                    COALESCE(ur.role, 'MAPPER')
                ) FILTER (WHERE ur.project_id IS NOT NULL) AS project_roles

            FROM upserted_user u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN organisation_managers om ON u.id = om.user_id
            GROUP BY u.id, u.username, u.profile_img, u.role;
        """

        async with db.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(
                upsert_sql,
                {
                    "user_id": user_data.id,
                    "username": user_data.username,
                    "profile_img": user_data.picture or "",
                    "role": UserRole(user_data.role).name,
                },
            )
            db_user_details = await cur.fetchone()

        if not db_user_details:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User ID ({user_data.id}) could not be inserted in db",
            )

        return db_user_details

    except Exception as e:
        await db.rollback()
        log.exception(f"Exception occurred: {e}", stack_info=True)
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


@router.get("/me", response_model=FMTMUser)
async def my_data(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Read access token and get user details from OSM.

    Args:
        db (Connection): The db connection.
        current_user (AuthUser): User data provided by osm-login-python Auth.

    Returns:
        FMTMUser: The dict of user data.
    """
    return await get_or_create_user(db, current_user)


async def refresh_fmtm_cookies(request: Request, current_user: AuthUser):
    """Reusable function to renew the expiry on the FMTM and expiry tokens.

    Used by both management and mapper refresh endpoints.
    """
    if settings.DEBUG:
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={**current_user.model_dump()},
        )

    try:
        access_token = get_cookie_value(
            request,
            settings.cookie_name,  # OSM cookie
        )
        if not access_token:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="No access token provided",
            )

        refresh_token = get_cookie_value(
            request,
            f"{settings.cookie_name}_refresh",  # OSM refresh cookie
        )
        if not refresh_token:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="No refresh token provided",
            )

        # Decode JWT and get data from both cookies
        access_token_data = verify_jwt_token(access_token, ignore_expiry=True)
        refresh_token_data = verify_jwt_token(refresh_token)

        # Refresh token + refresh token
        new_access_token = refresh_jwt_token(access_token_data)
        new_refresh_token = refresh_jwt_token(refresh_token_data)

        response = set_cookies(new_access_token, new_refresh_token)
        # Append the user data to the JSONResponse
        # We use this in the frontend to determine if the token user matches the
        # currently logged in user. If no, we clear the frontend auth state.
        response.content = access_token_data
        return response

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to refresh the access token: {e}",
        ) from e


@router.get("/refresh/management", response_model=AuthUser)
async def refresh_management_cookies(
    request: Request,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Uses the refresh token to generate a new access token.

    This endpoint is specific to the management desktop frontend.
    Any temp auth cookies will be ignored and removed.
    OSM login is required.
    """
    response = await refresh_fmtm_cookies(request, current_user)

    # Invalidate any temp cookies from mapper frontend
    fmtm_cookie_name = settings.cookie_name
    temp_cookie_name = f"{fmtm_cookie_name}_temp"
    temp_refresh_cookie_name = f"{fmtm_cookie_name}_temp_refresh"
    for cookie_name in [
        temp_cookie_name,
        temp_refresh_cookie_name,
    ]:
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


@router.get("/refresh/mapper", response_model=AuthUser)
async def refresh_mapper_token(
    request: Request,
    current_user: Annotated[AuthUser, Depends(mapper_login_required)],
):
    """Uses the refresh token to generate a new access token.

    This endpoint is specific to the mapper mobile frontend.
    By default the user will be logged in with a temporary auth cookie.
    OSM auth is optional, if the user wishes to be attributed for contributions.
    """
    try:
        response = await refresh_fmtm_cookies(request, current_user)
        return response
    except HTTPException:
        # NOTE we allow for token verification to fail for the main cookie
        # and fallback to to generate a temp auth cookie
        pass

    username = "svcfmtm"
    jwt_data = {
        "sub": "fmtm|20386219",
        "aud": settings.FMTM_DOMAIN,
        "iat": int(time()),
        "exp": int(time()) + 86400,  # set token expiry to 1 day
        "username": username,
        "picture": None,
        "role": UserRole.MAPPER,
    }
    access_token, refresh_token = create_jwt_tokens(jwt_data)
    response = set_cookies(
        access_token,
        refresh_token,
        f"{settings.cookie_name}_temp",
        f"{settings.cookie_name}_temp_refresh",
    )
    response.content = jwt_data
    return response
