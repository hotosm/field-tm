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
import time

import jwt
from fastapi import Header, HTTPException, Request, Response
from loguru import logger as log
from osm_login_python.core import Auth

from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.models.enums import UserRole

if settings.DEBUG:
    # Required as callback url is http during dev
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


async def init_osm_auth():
    """Initialise Auth object from osm-login-python."""
    return Auth(
        osm_url=settings.OSM_URL,
        client_id=settings.OSM_CLIENT_ID,
        client_secret=settings.OSM_CLIENT_SECRET,
        secret_key=settings.OSM_SECRET_KEY,
        login_redirect_uri=settings.OSM_LOGIN_REDIRECT_URI,
        scope=settings.OSM_SCOPE,
    )


async def login_required(
    request: Request, access_token: str = Header(None)
) -> AuthUser:
    """Dependency to inject into endpoints requiring login."""
    if settings.DEBUG:
        return AuthUser(
            sub="fmtm|1",
            username="localadmin",
            role=UserRole.ADMIN,
        )

    # Attempt extract from cookie if access token not passed
    if not access_token:
        access_token = extract_token_from_cookie(request)

    if not access_token:
        raise HTTPException(status_code=401, detail="No access token provided")

    try:
        token_data = verify_token(access_token)
    except ValueError as e:
        log.error(e)
        log.error("Failed to deserialise access token")
        raise HTTPException(status_code=401, detail="Access token not valid") from e

    return AuthUser(**token_data)


def extract_token_from_cookie(request: Request) -> str:
    """Extract access token from cookies."""
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    log.debug(f"Extracting token from cookie {cookie_name}")
    return request.cookies.get(cookie_name)


def extract_refresh_token_from_cookie(request: Request) -> str:
    """Extract refresh token from cookies."""
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    return request.cookies.get(f"{cookie_name}_refresh")


def create_tokens(payload: dict) -> tuple[str, str]:
    """Generates tokens for the specified user.

    Args:
        payload (dict): user data for which the access token is being generated.

    Returns:
        Tuple: The generated access tokens.
    """
    access_token_payload = payload
    access_token_payload["exp"] = (
        int(time.time()) + 86400
    )  # set access token expiry to 1 day
    access_token = jwt.encode(
        access_token_payload,
        settings.ENCRYPTION_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )
    refresh_token = jwt.encode(
        payload, settings.ENCRYPTION_KEY, algorithm=settings.JWT_ENCRYPTION_ALGORITHM
    )
    return access_token, refresh_token


def refresh_access_token(payload: dict) -> str:
    """Generate a new access token."""
    payload["exp"] = int(time.time()) + 60  # Access token valid for 15 minutes

    return jwt.encode(
        payload,
        settings.ENCRYPTION_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


def verify_token(token: str):
    """Verifies the access token and returns the payload if valid.

    Args:
        token (str): The access token to be verified.

    Returns:
        dict: The payload of the access token if verification is successful.

    Raises:
        HTTPException: If the token has expired or credentials could not be validated.
    """
    try:
        return jwt.decode(
            token,
            settings.ENCRYPTION_KEY,
            algorithms=[settings.JWT_ENCRYPTION_ALGORITHM],
            audience=settings.FMTM_DOMAIN,
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Refresh token has expired") from e
    except Exception as e:
        raise HTTPException(
            status_code=401, detail="Could not validate refresh token"
        ) from e


def set_cookies(access_token: str, refresh_token: str):
    """Sets cookies for the access token and refresh token.

    Args:
        access_token (str): The access token to be stored in the cookie.
        refresh_token (str): The refresh token to be stored in the cookie.

    Returns:
        Response: A response object with the cookies set.
    """
    response = Response(status_code=200)
    cookie_name = settings.FMTM_DOMAIN.replace(".", "_")
    response.set_cookie(
        key=cookie_name,
        value=access_token,
        max_age=86400,
        expires=86400,  # expiry set for 1 day
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key=f"{cookie_name}_refresh",
        value=refresh_token,
        max_age=86400 * 7,
        expires=86400 * 7,  # expiry set for 7 days
        path="/",
        domain=settings.FMTM_DOMAIN,
        secure=False if settings.DEBUG else True,
        httponly=True,
        samesite="lax",
    )
    return response
