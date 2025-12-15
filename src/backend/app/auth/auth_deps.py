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

"""Auth dependencies, for restricted routes and cookie handling."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_logic import get_cookie_value, verify_jwt_token
from app.auth.auth_schemas import AuthUser
from app.config import settings
from app.db.database import db_conn
from app.db.enums import HTTPStatus, UserRole


async def public_endpoint(
    request: Request,
    access_token: Annotated[Optional[str], Header()] = None,
) -> Optional[AuthUser]:
    """For fully public endpoints.

    Requires no database access to check auth roles.
    Optional login dependency: returns AuthUser if authenticated, else None.
    """
    if settings.DEBUG:
        return AuthUser(sub="osm|1", username="localadmin", role=UserRole.ADMIN)

    extracted_token = access_token or get_cookie_value(request, settings.cookie_name)

    svc_account_user = {
        "sub": "osm|20386219",
        "username": "svcfmtm",
        "role": UserRole.MAPPER,
    }
    if not extracted_token:
        return AuthUser(**svc_account_user)

    try:
        user = await _authenticate_cookie_token(extracted_token)
        return user
    except Exception:
        return AuthUser(**svc_account_user)


async def login_required(
    request: Request,
    db: Annotated[Connection, Depends(db_conn)],
    access_token: Annotated[Optional[str], Header()] = None,
) -> AuthUser:
    """Dependency for endpoints requiring login."""
    if settings.DEBUG:
        return AuthUser(sub="osm|1", username="localadmin", role=UserRole.ADMIN)

    # Else, extract access token only from the Field-TM cookie
    extracted_token = access_token or get_cookie_value(
        request,
        settings.cookie_name,  # Field-TM cookie
    )
    if extracted_token:
        return await _authenticate_cookie_token(extracted_token)

    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Auth cookie or API token must be provided",
    )


async def _authenticate_cookie_token(access_token: str) -> AuthUser:
    """Authenticate user by verifying the access token."""
    try:
        token_data = verify_jwt_token(access_token)
    except ValueError as e:
        log.exception(f"Failed to verify access token: {e}", stack_info=True)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Access token not valid",
        ) from e

    return AuthUser(**token_data)
