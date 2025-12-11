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

"""Auth routes, to login, logout, and get user details."""

from time import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_logic import (
    create_jwt_tokens,
    expire_cookies,
    refresh_cookies,
    set_cookies,
)
from app.auth.auth_schemas import AuthUser, FMTMUser
from app.auth.providers.osm import (
    get_mapper_osm_auth,
    handle_osm_callback,
    init_osm_auth,
)
from app.config import settings
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.users.user_crud import get_or_create_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/login/osm/management")
async def get_osm_management_login_url(osm_auth=Depends(init_osm_auth)):
    """Get Login URL for OSM Oauth Application.

    The application must be registered on openstreetmap.org.
    Open the download url returned to get access_token.

    Args:
        osm_auth: The Auth object from osm-login-python.

    Returns:
        login_url (string): URL to authorize user in OSM.
            Includes URL params: client_id, redirect_uri, permission scope.
    """
    login_url = osm_auth.login()
    log.debug(f"OSM Login URL returned: {login_url}")
    return JSONResponse(content=login_url, status_code=HTTPStatus.OK)


@router.get("/login/osm/mapper")
async def get_osm_mapper_login_url(osm_auth=Depends(get_mapper_osm_auth)):
    """Get Login URL for OSM Oauth Application.

    The application must be registered on openstreetmap.org.
    Open the download url returned to get access_token.
    This endpoint is specifically for mapper page.

    Args:
        osm_auth: The Auth object from osm-login-python.

    Returns:
        login_url (string): URL to authorize user in OSM.
            Includes URL params: client_id, redirect_uri, permission scope.
    """
    login_url = osm_auth.login()
    log.debug(f"OSM Login URL returned: {login_url}")
    return JSONResponse(content=login_url, status_code=HTTPStatus.OK)


@router.get("/callback/osm")
async def osm_callback(
    request: Request, osm_auth: Annotated[AuthUser, Depends(init_osm_auth)]
) -> JSONResponse:
    """Performs oauth token exchange with OpenStreetMap.

    Provides an access token that can be used for authenticating other endpoints.
    Also returns a cookie containing the access token for persistence in frontend apps.
    """
    try:
        # This includes the main cookie, refresh cookie, osm token cookie
        response_plus_cookies = await handle_osm_callback(request, osm_auth)
        return response_plus_cookies
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=str(e)) from e


@router.get("/callback/osm/mapper")
async def mapper_osm_callback(
    request: Request, osm_auth: Annotated[AuthUser, Depends(get_mapper_osm_auth)]
) -> JSONResponse:
    """Performs oauth token exchange with OpenStreetMap.

    Provides an access token that can be used for authenticating other endpoints.
    Also returns a cookie containing the access token for persistence in frontend apps.
    """
    try:
        # This includes the main cookie, refresh cookie, osm token cookie
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
    osm_cookie_name = f"{fmtm_cookie_name}_osm"

    cookie_names = [
        fmtm_cookie_name,
        refresh_cookie_name,
        osm_cookie_name,
    ]

    response = await expire_cookies(response, cookie_names)
    return response


@router.get("/me", response_model=FMTMUser)
async def my_data(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Read access token and get user details.

    Args:
        db (Connection): The db connection.
        current_user (AuthUser): User data provided by authentication.

    Returns:
        FMTMUser: The dict of user data.
    """
    return await get_or_create_user(db, current_user)


@router.get("/refresh/management", response_model=FMTMUser)
async def refresh_management_cookies(
    request: Request,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Uses the refresh token to generate a new access token.

    This endpoint is specific to the management desktop frontend.
    Authentication is required.
    If signed in with login method other than OSM, the user will be logged out and
    a forbidden status will be returned.

    NOTE this endpoint has no db calls and returns in ~2ms.
    """
    # Only allow login via OSM for management frontend
    # and revoke cookies if service account set via mapper frontend
    user_sub = current_user.sub.lower()
    if "osm" not in user_sub or current_user.username == "svcfmtm":
        response = Response(
            status_code=HTTPStatus.FORBIDDEN,
            content="Please log in using OSM for management access.",
        )
        cookie_names = [
            settings.cookie_name,
            f"{settings.cookie_name}_refresh",
        ]

        response = await expire_cookies(response, cookie_names)
        return response

    return await refresh_cookies(
        request,
        current_user,
        settings.cookie_name,
        f"{settings.cookie_name}_refresh",
    )


@router.get("/refresh/mapper", response_model=Optional[FMTMUser])
async def refresh_mapper_token(
    request: Request,
    current_user: Annotated[AuthUser, Depends(public_endpoint)],
):
    """Uses the refresh token to generate a new access token.

    This endpoint is specific to the mapper mobile frontend.
    By default the user will be logged in with a service account.
    Authentication is optional, if the user wishes to be attributed for contributions.

    NOTE this endpoint has no db calls and returns in ~2ms.
    """
    try:
        # If standard login cookie is passed, use that
        response = await refresh_cookies(
            request,
            current_user,
            settings.cookie_name,
            f"{settings.cookie_name}_refresh",
        )
        return response
    except HTTPException:
        # NOTE we allow for token verification to fail for the main cookie
        # and fallback to to generate a temp auth cookie
        pass

    # Refresh the temp cookies (we must re-create the 'sub' field)
    temp_jwt_details = {
        **current_user.model_dump(exclude=["id"]),
        "sub": current_user.sub,
        "aud": settings.FMTM_DOMAIN,
        "iat": int(time()),
        "exp": int(time()) + 86400,  # set token expiry to 1 day
    }

    fmtm_token, refresh_token = create_jwt_tokens(temp_jwt_details)
    # NOTE be sure to not append content=current_user.model_dump() to this JSONResponse
    # as we want the login state on the frontend to remain empty (allowing the user to
    # log in via OSM instead / override)
    response = JSONResponse(status_code=HTTPStatus.OK, content=temp_jwt_details)
    return set_cookies(
        response,
        fmtm_token,
        refresh_token,
    )
