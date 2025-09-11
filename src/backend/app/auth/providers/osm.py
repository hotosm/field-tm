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

"""Auth methods related to OSM OAuth2."""

import os
from time import time
from typing import Optional

import requests
from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from loguru import logger as log
from osm_login_python.core import Auth

from app.auth.auth_logic import create_jwt_tokens, get_cookie_domain, set_cookies
from app.config import settings
from app.db.enums import HTTPStatus, UserRole

if settings.DEBUG:
    # Required as callback url is http during dev
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


async def init_osm_auth(mapper: Optional[bool] = None):
    """Initialize Auth object from osm-login-python."""
    login_redirect_uri = (
        settings.mapper_osm_login_redirect_uri
        if mapper
        else settings.manager_osm_login_redirect_uri
    )

    return Auth(
        osm_url=settings.OSM_URL,
        client_id=settings.OSM_CLIENT_ID,
        client_secret=settings.OSM_CLIENT_SECRET.get_secret_value(),
        secret_key=settings.OSM_SECRET_KEY.get_secret_value(),
        login_redirect_uri=login_redirect_uri,
        scope=settings.OSM_SCOPE,
    )


async def get_mapper_osm_auth():
    """Wrapper function to await async dependency."""
    return await init_osm_auth(mapper=True)


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
            "sub": f"osm|{osm_user['id']}",
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
    response = Response(status_code=HTTPStatus.OK)
    response_plus_cookies = set_cookies(response, fmtm_token, refresh_token)

    # NOTE Here we create a separate cookie to store the OSM token, for later
    # workflows such as conflation (OSM changesets) or OSM messaging.
    # First, we get the OSM token from response.
    # The token is serialised in the cookie & must be deserialised using
    # osm_login_python.auth.deserialize_data.
    serialised_osm_token = tokens.get("oauth_token")
    cookie_name = settings.cookie_name
    osm_cookie_name = f"{cookie_name}_osm"
    log.debug(f"Creating cookie '{osm_cookie_name}' with OSM token")
    cookie_domain = get_cookie_domain()
    response_plus_cookies.set_cookie(
        key=osm_cookie_name,
        value=serialised_osm_token,
        max_age=864000,
        expires=864000,  # expiry set for 10 days
        path="/",
        domain=cookie_domain,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )

    return response_plus_cookies


def get_osm_token(request: Request, osm_auth: Auth) -> str:
    """Extract and deserialize OSM token from cookies."""
    cookie_name = f"{settings.cookie_name}_osm"
    log.debug(f"Extracting OSM token from cookie {cookie_name}")
    serialised_osm_token = request.cookies.get(cookie_name)
    if not serialised_osm_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="You must be logged in to your OpenStreetMap account.",
        )
    return osm_auth.deserialize_data(serialised_osm_token)


def send_osm_message(
    osm_token: str,
    title: str,
    body: str,
    osm_username: str = None,
    osm_sub: str = None,
) -> None:
    """Send a message via OSM API."""
    if not osm_username and not osm_sub:
        raise ValueError("Either recipient or recipient_id must be provided.")

    email_url = f"{settings.OSM_URL}api/0.6/user/messages"
    headers = {"Authorization": f"Bearer {osm_token}"}
    post_body = {
        "title": title,
        "body": body,
    }

    if osm_sub:
        post_body["recipient_id"] = osm_sub.split("|")[-1]
    else:
        post_body["recipient"] = osm_username

    log.debug(
        f"Sending message to user ({osm_sub or osm_username}) via OSM API: {email_url}"
    )
    response = requests.post(email_url, headers=headers, data=post_body)

    if response.status_code == 200:
        log.info("Message sent successfully")
    else:
        msg = "Sending message via OSM failed"
        log.error(f"{msg}: {response.text}")


async def check_osm_user(osm_username: str):
    """Check if the user is an OSM user based on their username."""
    osm_url = f"https://www.openstreetmap.org/user/{osm_username}/"

    user_exists = False
    try:
        response = requests.get(osm_url)
        if response.status_code == 200:
            user_exists = True
    except Exception as e:
        log.exception(
            f"Failed to check if user exists on OSM. Error: {e}",
            stack_info=True,
        )
    return user_exists
