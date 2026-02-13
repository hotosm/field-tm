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
"""Routes for API key lifecycle management."""

from __future__ import annotations

from litestar import delete, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel

from app.auth.api_key import generate_api_key, hash_api_key
from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser
from app.db.database import db_conn
from app.db.models import DbApiKey


class ApiKeyCreateRequest(BaseModel):
    """Input payload for creating an API key."""

    name: str | None = None


@post(
    "/api-keys",
    summary="Create a new API key for the current user.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key_route(
    db: AsyncConnection,
    auth_user: AuthUser,
    data: ApiKeyCreateRequest,
) -> dict:
    """Generate a key, store only the hash, and return the raw key once."""
    raw_key = generate_api_key()
    db_key = await DbApiKey.create(
        db,
        DbApiKey(
            user_sub=auth_user.sub,
            key_hash=hash_api_key(raw_key),
            name=data.name,
        ),
    )
    await db.commit()

    return {
        "id": db_key.id,
        "name": db_key.name,
        "created_at": db_key.created_at,
        "is_active": db_key.is_active,
        "api_key": raw_key,
    }


@get(
    "/api-keys",
    summary="List API keys for the current user.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def list_api_keys_route(db: AsyncConnection, auth_user: AuthUser) -> list[dict]:
    """List API keys (without exposing raw key or stored hash)."""
    keys = await DbApiKey.all_for_user(db, auth_user.sub)
    return [
        {
            "id": key.id,
            "name": key.name,
            "created_at": key.created_at,
            "last_used_at": key.last_used_at,
            "is_active": key.is_active,
        }
        for key in keys
    ]


@delete(
    "/api-keys/{key_id:int}",
    summary="Revoke (deactivate) an API key for the current user.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_api_key_route(
    key_id: int,
    db: AsyncConnection,
    auth_user: AuthUser,
) -> None:
    """Deactivate a key so it can no longer authenticate requests."""
    revoked = await DbApiKey.deactivate(db, key_id, auth_user.sub)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id={key_id} not found.",
        )
    await db.commit()
