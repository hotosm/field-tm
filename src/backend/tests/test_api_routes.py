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
"""Tests for external API v1 routes."""

from uuid import uuid4

import pytest


@pytest.fixture()
async def ensure_api_keys_table(db):
    """Ensure api_keys table exists for tests where migration scripts are not run."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public.api_keys (
                id SERIAL PRIMARY KEY,
                user_sub character varying NOT NULL REFERENCES public.users(sub) ON DELETE CASCADE,
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
async def test_api_v1_create_requires_api_key(client, ensure_api_keys_table):
    """POST /api/v1/projects is protected by X-API-KEY auth."""
    payload = {
        "project_name": f"api-missing-key-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.317028828, 27.7052522097],
                    [85.317028828, 27.7041424888],
                    [85.318844411, 27.7041424888],
                    [85.318844411, 27.7052522097],
                    [85.317028828, 27.7052522097],
                ]
            ],
        },
        "hashtags": ["#api"],
    }
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_v1_create_and_public_read(client, ensure_api_keys_table):
    """Create with API key, then verify public read endpoints."""
    key_response = await client.post("/auth/api-keys", json={"name": "api-test-key"})
    assert key_response.status_code == 201
    api_key = key_response.json()["api_key"]

    payload = {
        "project_name": f"api-create-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.317028828, 27.7052522097],
                    [85.317028828, 27.7041424888],
                    [85.318844411, 27.7041424888],
                    [85.318844411, 27.7052522097],
                    [85.317028828, 27.7052522097],
                ]
            ],
        },
        "hashtags": ["#api"],
    }
    create_response = await client.post(
        "/api/v1/projects", json=payload, headers={"X-API-KEY": api_key}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["project_name"] == payload["project_name"]
    assert created["field_mapping_app"] == "ODK"

    list_response = await client.get("/api/v1/projects")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert any(project["id"] == created["id"] for project in list_response.json())

    get_response = await client.get(f"/api/v1/projects/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]
