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
"""Tests for API key auth dependencies and key management routes."""

import pytest
from litestar.exceptions import HTTPException

from app.auth.api_key import api_key_required, hash_api_key
from app.db.models import DbApiKey, DbUser


@pytest.fixture()
async def ensure_api_keys_table(db):
    """Ensure the api_keys table exists in test DBs without new migrations applied."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public.api_keys (
                id SERIAL PRIMARY KEY,
                user_sub character varying NOT NULL
                    REFERENCES public.users(sub) ON DELETE CASCADE,
                key_hash character varying NOT NULL UNIQUE,
                name character varying,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_used_at TIMESTAMPTZ,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            """
        )
    await db.commit()


@pytest.mark.asyncio
async def test_api_key_routes_create_list_and_revoke(client, db, ensure_api_keys_table):
    """Create, list, and revoke API keys via auth routes."""
    create_resp = await client.post(
        "/api/v1/auth/api-keys",
        json={"name": "integration key"},
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["api_key"].startswith("ftm_")
    assert body["name"] == "integration key"

    raw_key = body["api_key"]
    db_key = await DbApiKey.get_by_hash(db, hash_api_key(raw_key))
    assert db_key is not None
    assert db_key.key_hash != raw_key
    assert db_key.is_active is True

    list_resp = await client.get("/api/v1/auth/api-keys")
    assert list_resp.status_code == 200
    listed_keys = list_resp.json()
    assert any(key["id"] == body["id"] for key in listed_keys)

    revoke_resp = await client.delete(f"/api/v1/auth/api-keys/{body['id']}")
    assert revoke_resp.status_code == 204

    revoked = await DbApiKey.get_by_hash(db, hash_api_key(raw_key), active_only=False)
    assert revoked is not None
    assert revoked.is_active is False


@pytest.mark.asyncio
async def test_api_key_required_validates_and_updates_last_used(
    client, db, ensure_api_keys_table
):
    """api_key_required authenticates valid keys and rejects invalid ones (real DB)."""
    # Create a real API key via the HTTP endpoint
    create_resp = await client.post(
        "/api/v1/auth/api-keys", json={"name": "test-valid-key"}
    )
    assert create_resp.status_code == 201
    raw_key = create_resp.json()["api_key"]

    # Valid key --> returns an AuthUser
    auth_user = await api_key_required(request=None, db=db, x_api_key=raw_key)
    assert auth_user.sub is not None
    assert auth_user.username is not None

    # The key record's last_used_at should now be set
    db_key = await DbApiKey.get_by_hash(db, hash_api_key(raw_key))
    assert db_key is not None
    assert db_key.last_used_at is not None

    # Invalid key --> 401
    with pytest.raises(HTTPException) as exc_info:
        await api_key_required(request=None, db=db, x_api_key="ftm_invalid_key")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_profile_me_returns_and_persists_authenticated_user(client, db):
    """GET /api/v1/auth/profile/me returns and persists the authenticated user."""
    resp = await client.get("/api/v1/auth/profile/me")
    assert resp.status_code == 200

    body = resp.json()
    assert body["sub"]
    assert body["username"]

    db_user = await DbUser.one(db, body["sub"])
    assert db_user.sub == body["sub"]
    assert db_user.username == body["username"]
    assert db_user.is_admin is body["is_admin"]
