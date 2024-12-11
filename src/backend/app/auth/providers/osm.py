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

"""Auth methods related to OSM OAuth2."""

import os
from time import time

from fastapi import Request
from loguru import logger as log
from osm_login_python.core import Auth

from app.auth.auth_deps import create_jwt_tokens, set_cookies
from app.config import settings
from app.db.enums import UserRole

if settings.DEBUG:
    # Required as callback url is http during dev
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


async def init_osm_auth():
    """Initialise Auth object from osm-login-python."""
    return Auth(
        osm_url=settings.OSM_URL,
        client_id=settings.OSM_CLIENT_ID,
        client_secret=settings.OSM_CLIENT_SECRET.get_secret_value(),
        secret_key=settings.OSM_SECRET_KEY.get_secret_value(),
        login_redirect_uri=settings.OSM_LOGIN_REDIRECT_URI,
        scope=settings.OSM_SCOPE,
    )


async def handle_osm_callback(request: Request, osm_auth: Auth):
    """Handle OSM callback in OAuth flow.

    Args:
        request: The GET request.
        osm_auth: The Auth object from osm-login-python.

    Returns:
        Response: A response including cookies that will be set in-browser.
    """
    log.debug(f"Callback url requested: {request.url}")

    # Enforce https callback url for openstreetmap.org
    callback_url = str(request.url).replace("http://", "https://")

    # Get user data from response
    try:
        tokens = osm_auth.callback(callback_url)
        serialised_user_data = tokens.get("user_data")
        log.debug(f"Access token returned of length {len(serialised_user_data)}")
        osm_user = osm_auth.deserialize_data(serialised_user_data)
        user_data = {
            "sub": f"fmtm|{osm_user['id']}",
            "aud": settings.FMTM_DOMAIN,
            "iat": int(time()),
            "exp": int(time()) + 86400,  # expiry set to 1 day
            "username": osm_user["username"],
            "email": osm_user.get("email"),
            "picture": osm_user.get("img_url"),
            "role": UserRole.MAPPER,
        }
    except Exception as e:
        raise ValueError(f"Invalid OSM token: {e}") from e

    # Create our JWT tokens from user data
    fmtm_token, refresh_token = create_jwt_tokens(user_data)
    response_plus_cookies = set_cookies(fmtm_token, refresh_token)

    # Get OSM token from response (serialised in cookie, deserialise to use)
    serialised_osm_token = tokens.get("oauth_token")
    cookie_name = settings.cookie_name
    osm_cookie_name = f"{cookie_name}_osm"
    log.debug(f"Creating cookie '{osm_cookie_name}' with OSM token")
    response_plus_cookies.set_cookie(
        key=osm_cookie_name,
        value=serialised_osm_token,
        max_age=864000,
        expires=864000,  # expiry set for 10 days
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )

    return response_plus_cookies
