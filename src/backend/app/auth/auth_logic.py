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

"""Logic for handling authentication, headers, tokens, and cookies."""

import logging
from time import time
from typing import Optional
from urllib.parse import urlparse

import jwt
from litestar import Request, Response
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from tldextract import extract as domain_root_extract

from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.db.models import DbUser

log = logging.getLogger(__name__)


async def get_uid(user_data: AuthUser | DbUser) -> int:
    """Extract user id from returned OSM user."""
    try:
        return user_data.sub

    except Exception as e:
        log.exception(
            f"Failed to get user id from auth object: {user_data}. Error: {e}",
            stack_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth failed. No user id present",
        ) from e


def get_cookie_value(request: Request, *cookie_names: str) -> Optional[str]:
    """Get the first available value from a list of cookie names."""
    for name in cookie_names:
        value = request.cookies.get(name)
        if value:
            return value
    return None


def get_root_domain(domain_or_url: str) -> str:
    """Extract root domain from a domain or URL."""
    if domain_or_url.startswith(("http://", "https://")):
        parsed = urlparse(domain_or_url)
        domain = parsed.hostname
        if not domain:
            raise ValueError("Domain root could not be determined")
    else:
        domain = domain_or_url

    # tldextract handles public suffixes nicely, like co.uk, com.np, etc
    ext = domain_root_extract(domain)
    if not ext.domain or not ext.suffix:
        raise ValueError(f"Invalid domain: {domain}")
    return f"{ext.domain}.{ext.suffix}"


def domains_compatible_for_cookies(domain1: str, domain2: str) -> bool:
    """Check if two domains can share cookies (same root domain)."""
    root1 = get_root_domain(domain1)
    root2 = get_root_domain(domain2)
    return root1 == root2


def set_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: int,
    secure: bool,
    domain: str,
) -> None:
    """Helper function to set a cookie on a response.

    For now, samesite is set lax, max_age equals expiry.
    """
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        expires=max_age,
        path="/",
        domain=domain,
        secure=secure,
        httponly=True,
        samesite="lax",
    )


def set_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    cookie_name: str = settings.cookie_name,
    refresh_cookie_name: str = f"{settings.cookie_name}_refresh",
) -> Response:
    """Set cookies for the access and refresh tokens.

    Args:
        response (str): The response to attach the cookies to.
        access_token (str): The access token to be stored in the cookie.
        refresh_token (str): The refresh token to be stored in the cookie.
        cookie_name (str, optional): The name of the cookie to store the access token.
        refresh_cookie_name (str, optional): The name of the cookie to store the
            refresh token.

    Returns:
        JSONResponse: A response with attached cookies (set-cookie headers).
    """
    secure = not settings.DEBUG
    cookie_domain = settings.FMTM_DOMAIN

    set_cookie(
        response,
        cookie_name,
        access_token,
        max_age=86400,  # 1 day
        secure=secure,
        domain=cookie_domain,
    )
    set_cookie(
        response,
        refresh_cookie_name,
        refresh_token,
        max_age=86400 * 7,  # 1 week
        secure=secure,
        domain=cookie_domain,
    )

    return response


def create_jwt_tokens(input_data: dict) -> tuple[str, str]:
    """Generate access and refresh tokens.

    Args:
        input_data (dict): user data for which the access token is being generated.

    Returns:
        tuple[str]: The generated access tokens.
    """
    access_token_data = input_data.copy()
    # Set refresh token expiry to 7 days
    refresh_token_data = {**input_data, "exp": int(time()) + 86400 * 7}

    encryption_key = settings.ENCRYPTION_KEY.get_secret_value()
    algorithm = settings.JWT_ENCRYPTION_ALGORITHM

    access_token = jwt.encode(access_token_data, encryption_key, algorithm=algorithm)
    refresh_token = jwt.encode(refresh_token_data, encryption_key, algorithm=algorithm)

    return access_token, refresh_token


def refresh_jwt_token(
    payload: dict,
    # Default expiry 1 day
    expiry_seconds: int = 86400,
) -> str:
    """Generate a new JTW token with expiry."""
    payload["exp"] = int(time()) + expiry_seconds
    return jwt.encode(
        payload,
        settings.ENCRYPTION_KEY.get_secret_value(),
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


def verify_jwt_token(token: str, ignore_expiry: bool = False) -> dict:
    """Verify the access token and return its payload.

    Args:
        token (str): The access token to be verified.
        ignore_expiry (bool): Do not throw an error if the token is expired
            upon deserialisation.

    Returns:
        dict: The payload of the access token if verification is successful.

    Raises:
        HTTPException: If the token has expired or credentials could not be validated.
    """
    try:
        return jwt.decode(
            token,
            settings.ENCRYPTION_KEY.get_secret_value(),
            algorithms=[settings.JWT_ENCRYPTION_ALGORITHM],
            audience=settings.FMTM_DOMAIN,
            options={"verify_exp": False if ignore_expiry else True},
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        ) from e
    except Exception as e:
        log.exception(f"Unknown cookie/jwt error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        ) from e


async def refresh_cookies(
    request: Request,
    current_user: AuthUser,
    cookie_name: str,
    refresh_cookie_name: str,
):
    """Reusable function to renew the expiry on cookies.

    Used the frontend refresh endpoints.
    """
    if settings.DEBUG:
        # Minimal, consistent body; caller only cares about status / cookies
        return Response(
            status_code=status.HTTP_200_OK,
            content=b'{"message":"ok"}',
            media_type="application/json",
        )

    access_token = get_cookie_value(request, cookie_name)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token provided",
        )

    refresh_token = get_cookie_value(request, refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    # Decode JWT and get data from both cookies,
    # checking refresh expiry is valid first
    refresh_token_data = verify_jwt_token(refresh_token)
    access_token_data = verify_jwt_token(access_token, ignore_expiry=True)

    try:
        # Refresh token + refresh token
        new_access_token = refresh_jwt_token(access_token_data)
        new_refresh_token = refresh_jwt_token(refresh_token_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh tokens: {e}",
        ) from e

    response = Response(
        status_code=status.HTTP_200_OK,
        content=b'{"message":"ok"}',
        media_type="application/json",
    )
    response_plus_cookies = set_cookies(response, new_access_token, new_refresh_token)

    return response_plus_cookies


async def expire_cookies(response: Response, cookie_names: list[str]) -> Response:
    """Expire cookies by setting max_age to 0."""
    for cookie_name in cookie_names:
        log.debug(f"Resetting cookie in response named '{cookie_name}'")
        cookie_domain = settings.FMTM_DOMAIN
        response.set_cookie(
            key=cookie_name,
            value="",
            max_age=0,  # Set to expire immediately
            expires=0,  # Set to expire immediately
            path="/",
            domain=cookie_domain,
            secure=False if settings.DEBUG else True,
            httponly=True,
            samesite="lax",
        )
    return response
