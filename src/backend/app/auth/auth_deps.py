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

"""Auth dependencies, for restricted routes and cookie handling."""

from time import time
from typing import Optional

import jwt
from fastapi import Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger as log

from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.db.enums import HTTPStatus, UserRole

### Cookie / Token Handling


def get_cookie_value(request: Request, *cookie_names: str) -> Optional[str]:
    """Get the first available value from a list of cookie names."""
    for name in cookie_names:
        value = request.cookies.get(name)
        if value:
            return value
    return None


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
) -> JSONResponse:
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
    domain = settings.FMTM_DOMAIN

    set_cookie(
        response,
        cookie_name,
        access_token,
        max_age=86400,  # 1 day
        secure=secure,
        domain=domain,
    )
    set_cookie(
        response,
        refresh_cookie_name,
        refresh_token,
        max_age=86400 * 7,  # 1 week
        secure=secure,
        domain=domain,
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
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Could not validate refresh token",
        ) from e
    except Exception as e:
        log.exception(f"Unknown cookie/jwt error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Could not validate refresh token",
        ) from e


async def refresh_cookies(
    request: Request,
    current_user: AuthUser,
    cookie_name: str,
    refresh_cookie_name: str,
):
    """Reusable function to renew the expiry on cookies.

    Used by both management and mapper refresh endpoints.
    """
    if settings.DEBUG:
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={**current_user.model_dump()},
        )

    access_token = get_cookie_value(request, cookie_name)
    if not access_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="No access token provided",
        )

    refresh_token = get_cookie_value(request, refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
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
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to refresh tokens: {e}",
        ) from e

    # NOTE Append the user data to the JSONResponse so we can display in the
    # frontend header. For the mapper frontend this is enough, but for the
    # management frontend we instead use the return from /auth/me
    response = JSONResponse(status_code=HTTPStatus.OK, content=access_token_data)
    response_plus_cookies = set_cookies(response, new_access_token, new_refresh_token)

    # Invalidate any temp cookies from mapper frontend
    for cookie_name in [
        f"{settings.cookie_name}_temp",
        f"{settings.cookie_name}_temp_refresh",
    ]:
        log.debug(f"Resetting cookie in response named '{cookie_name}'")
        response_plus_cookies.set_cookie(
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

    return response_plus_cookies


### Endpoint Dependencies ###


async def login_required(
    request: Request, access_token: str = Header(None)
) -> AuthUser:
    """Dependency for endpoints requiring login."""
    if settings.DEBUG:
        return AuthUser(sub="fmtm|1", username="localadmin", role=UserRole.ADMIN)

    # Extract access token only from the FMTM cookie
    extracted_token = access_token or get_cookie_value(
        request,
        settings.cookie_name,  # FMTM cookie
    )
    print("manage")
    return await _authenticate_user(extracted_token)


async def mapper_login_required(
    request: Request, access_token: str = Header(None)
) -> AuthUser:
    """Dependency for mapper frontend login."""
    if settings.DEBUG:
        return AuthUser(sub="fmtm|1", username="localadmin", role=UserRole.ADMIN)

    # Extract access token from FMTM cookie, fallback to temp auth cookie
    extracted_token = access_token or get_cookie_value(
        request,
        settings.cookie_name,  # FMTM cookie
        f"{settings.cookie_name}_temp",  # Temp cookie
    )

    # Verify login and continue
    if extracted_token:
        print("mapper")
        return await _authenticate_user(extracted_token)

    # Else user has no token, so we provide login data automatically
    username = "svcfmtm"
    temp_user = {
        "sub": "fmtm|20386219",
        "username": username,
        "role": UserRole.MAPPER,
    }
    return AuthUser(**temp_user)


async def _authenticate_user(access_token: Optional[str]) -> AuthUser:
    """Authenticate user by verifying the access token."""
    if not access_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="No access token provided",
        )

    try:
        token_data = verify_jwt_token(access_token)
    except ValueError as e:
        log.exception(f"Failed to verify access token: {e}", stack_info=True)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Access token not valid",
        ) from e

    return AuthUser(**token_data)
