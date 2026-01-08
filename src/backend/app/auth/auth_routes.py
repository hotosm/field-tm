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

"""Auth routes, to login, logout, and get user details (Litestar)."""

import logging

from litestar import Request, Response, Router, get
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from osm_login_python.core import Auth
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_logic import expire_cookies, refresh_cookies
from app.auth.auth_schemas import AuthUser, FMTMUser
from app.auth.providers.osm import handle_osm_callback, init_osm_auth
from app.config import settings
from app.db.database import db_conn
from app.db.models import DbUser
from app.users.user_crud import get_or_create_user

log = logging.getLogger(__name__)


@get(
    "/login/osm",
    summary="Get Login URL for OSM Oauth Application.",
    dependencies={"osm_auth": Provide(init_osm_auth)},
)
async def get_osm_management_login_url(
    osm_auth: Auth,
) -> dict[str, str]:
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
    return login_url


@get(
    "/callback/osm",
    summary="Performs oauth token exchange with OpenStreetMap.",
    dependencies={"osm_auth": Provide(init_osm_auth)},
)
async def osm_callback(
    request: Request,
    osm_auth: Auth,
) -> Response:
    """Performs oauth token exchange with OpenStreetMap.

    Provides an access token that can be used for authenticating other endpoints.
    Also returns a cookie containing the access token for persistence in frontend apps.
    """
    try:
        # This includes the main cookie, refresh cookie, osm token cookie
        response_plus_cookies = await handle_osm_callback(request, osm_auth)
        return response_plus_cookies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@get(
    "/logout",
    summary="Reset httpOnly cookie to sign out user.",
    status_code=status.HTTP_200_OK,
)
async def logout() -> Response:
    """Reset httpOnly cookie to sign out user."""
    response = Response(
        status_code=status.HTTP_200_OK,
        content=b'{"message":"ok"}',
        media_type="application/json",
    )
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


@get(
    "/me",
    summary="Read access token and get user details.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    return_dto=FMTMUser,
)
async def my_data(
    db: AsyncConnection,
    auth_user: AuthUser,
) -> DbUser:
    """Read access token and get user details.

    Args:
        db (Connection): The db connection.
        auth_user (AuthUser): User data provided by authentication.

    Returns:
        DbUser: The user data with project roles.
    """
    return await get_or_create_user(db, auth_user)


@get(
    "/refresh",
    summary="Uses the refresh token to generate a new access token.",
    dependencies={
        "auth_user": Provide(login_required),
    },
)
async def refresh_management_cookies(
    request: Request,
    auth_user: AuthUser,
) -> Response:
    """Uses the refresh token to generate a new access token.

    This endpoint is specific to the management desktop frontend.
    Authentication is required.
    If signed in with login method other than OSM, the user will be logged out and
    a forbidden status will be returned.

    NOTE this endpoint has no db calls and returns in ~2ms.
    """
    # Only allow login via OSM for management frontend
    # and revoke cookies if service account set via mapper frontend
    user_sub = auth_user.sub.lower()
    if "osm" not in user_sub or auth_user.username == "svcfmtm":
        response = Response(
            status_code=status.HTTP_403_FORBIDDEN,
            content=b"Please log in using OSM for management access.",
        )
        cookie_names = [
            settings.cookie_name,
            f"{settings.cookie_name}_refresh",
        ]

        response = await expire_cookies(response, cookie_names)
        return response

    return await refresh_cookies(
        request,
        auth_user,
        settings.cookie_name,
        f"{settings.cookie_name}_refresh",
    )


auth_router = Router(
    path="/auth",
    tags=["auth"],
    route_handlers=[
        get_osm_management_login_url,
        osm_callback,
        logout,
        my_data,
        refresh_management_cookies,
    ],
)
