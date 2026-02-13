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
"""API key authentication dependencies and helpers."""

from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from litestar import Request
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser
from app.db.models import DbApiKey, DbUser


def generate_api_key() -> str:
    """Generate a random API key (shown once to the user)."""
    return f"ftm_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Create a stable SHA-256 hash for DB storage and lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def _authenticate_api_key(db: AsyncConnection, raw_api_key: str) -> AuthUser:
    """Authenticate a user from a raw API key value."""
    if not raw_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-KEY header is required",
        )

    key_hash = hash_api_key(raw_api_key)
    db_key = await DbApiKey.get_by_hash(db, key_hash)
    if not db_key or not db_key.user_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    try:
        db_user = await DbUser.one(db, db_key.user_sub)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key user no longer exists",
        ) from e

    await DbApiKey.touch_last_used(db, db_key.id)
    await db.commit()

    return AuthUser(
        sub=db_user.sub,
        username=db_user.username or "unknown",
        is_admin=bool(db_user.is_admin),
        profile_img=db_user.profile_img,
    )


async def api_key_required(
    request: Request,  # noqa: ARG001 - required for Litestar dependency signature
    db: AsyncConnection,
    x_api_key: Optional[str] = Parameter(default=None, header="X-API-KEY"),
) -> AuthUser:
    """Dependency that authenticates requests via X-API-KEY header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-KEY header is required",
        )
    return await _authenticate_api_key(db, x_api_key)


async def login_or_api_key(
    request: Request,
    db: AsyncConnection,
    x_api_key: Optional[str] = Parameter(default=None, header="X-API-KEY"),
    access_token: Optional[str] = Parameter(default=None, header="access_token"),
) -> AuthUser:
    """Allow either cookie-based auth or API key auth."""
    if x_api_key:
        return await _authenticate_api_key(db, x_api_key)
    return await login_required(request=request, access_token=access_token)
