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

import base64
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

# Minimal valid XLSForm bytes (placeholder — process_xlsform is mocked)
_DUMMY_XLS = base64.b64encode(b"dummy-xlsform-content").decode()

# Small Kathmandu polygon shared across tests
_OUTLINE = {
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
}

# Minimal GeoJSON data extract (skips OSM download)
_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [85.317, 27.705]},
            "properties": {},
        }
    ],
}


@dataclass
class _FakeODKResult:
    odk_url: str = "https://central.example.org/#/projects/1"
    manager_username: str = "manager@example.org"
    manager_password: str = "s3cr3t"


@pytest.fixture()
async def ensure_api_keys_table(db):
    """Ensure api_keys table exists for tests where migration scripts are not run."""
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
async def test_api_v1_create_requires_api_key(client, ensure_api_keys_table):
    """POST /api/v1/projects is protected by X-API-KEY auth."""
    payload = {
        "project_name": f"api-missing-key-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": _OUTLINE,
        "xlsform_base64": _DUMMY_XLS,
    }
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_v1_create_and_public_read(client, ensure_api_keys_table):
    """Create project with API key (mocking heavy ops), then verify read endpoints."""
    key_response = await client.post("/auth/api-keys", json={"name": "api-test-key"})
    assert key_response.status_code == 201
    api_key = key_response.json()["api_key"]

    payload = {
        "project_name": f"api-create-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": _OUTLINE,
        "hashtags": ["#api"],
        # XLSForm via base64 upload (process_xlsform is mocked)
        "xlsform_base64": _DUMMY_XLS,
        # Data extract via explicit GeoJSON (save_data_extract is mocked)
        "geojson": _GEOJSON,
        # No splitting
    }

    with (
        patch(
            "app.api.api_routes.process_xlsform",
            new_callable=AsyncMock,
        ),
        patch(
            "app.api.api_routes.save_data_extract",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.api.api_routes.finalize_odk_project",
            new_callable=AsyncMock,
            return_value=_FakeODKResult(),
        ),
    ):
        create_response = await client.post(
            "/api/v1/projects", json=payload, headers={"X-API-KEY": api_key}
        )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["downstream_url"] == "https://central.example.org/#/projects/1"
    assert created["manager_username"] == "manager@example.org"
    assert "project_id" in created

    project_id = created["project_id"]

    list_response = await client.get("/api/v1/projects")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert any(project["id"] == project_id for project in list_response.json())

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_api_v1_create_forwards_custom_odk_credentials(
    client, ensure_api_keys_table
):
    """Create endpoint should pass explicit ODK advanced config to service layer."""
    from app.central.central_schemas import ODKCentral

    key_response = await client.post("/auth/api-keys", json={"name": "api-test-key"})
    assert key_response.status_code == 201
    api_key = key_response.json()["api_key"]

    payload = {
        "project_name": f"api-custom-odk-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API with custom ODK config",
        "outline": _OUTLINE,
        "hashtags": ["#api"],
        "xlsform_base64": _DUMMY_XLS,
        "geojson": _GEOJSON,
        "external_project_instance_url": "https://example-odk.trycloudflare.com",
        "external_project_username": "admin@example.org",
        "external_project_password": "test-password",
    }

    with (
        patch(
            "app.api.api_routes.process_xlsform",
            new_callable=AsyncMock,
        ),
        patch(
            "app.api.api_routes.save_data_extract",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.api.api_routes.finalize_odk_project",
            new_callable=AsyncMock,
            return_value=_FakeODKResult(),
        ) as mock_finalize,
    ):
        create_response = await client.post(
            "/api/v1/projects", json=payload, headers={"X-API-KEY": api_key}
        )

    assert create_response.status_code == 201
    mock_finalize.assert_awaited_once()

    custom_odk = mock_finalize.await_args.kwargs["custom_odk_creds"]
    assert isinstance(custom_odk, ODKCentral)
    assert (
        custom_odk.external_project_instance_url
        == payload["external_project_instance_url"]
    )
    assert custom_odk.external_project_username == payload["external_project_username"]
    assert custom_odk.external_project_password == payload["external_project_password"]
