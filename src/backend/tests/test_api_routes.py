"""Integration tests for external API v1 routes."""

import base64
import os
from pathlib import Path
from uuid import uuid4

import pytest

from app.auth.api_key import hash_api_key
from app.db.models import DbApiKey

TEST_DATA_DIR = Path(__file__).parent / "test_data"
_XLSFORM_B64 = base64.b64encode((TEST_DATA_DIR / "buildings.xls").read_bytes()).decode()
_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.31735, 27.70495],
                        [85.31735, 27.70455],
                        [85.31775, 27.70455],
                        [85.31775, 27.70495],
                        [85.31735, 27.70495],
                    ]
                ],
            },
            "properties": {"osm_id": 1, "building": "yes"},
        }
    ],
}
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


def _build_payload(**overrides) -> dict:
    payload = {
        "project_name": f"api-project-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": _OUTLINE,
        "hashtags": ["#api"],
        "xlsform_base64": _XLSFORM_B64,
        "geojson": _GEOJSON,
    }
    payload.update(overrides)
    return payload


@pytest.fixture()
async def ensure_api_keys_table(db):
    """Ensure API key table exists for integration auth flows."""
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


@pytest.fixture()
async def api_key(db, admin_user, ensure_api_keys_table):
    """Create a real API key directly in DB for API route tests."""
    raw_key = f"ftm_api_{uuid4().hex}"
    await DbApiKey.create(
        db,
        DbApiKey(
            user_sub=admin_user.sub,
            key_hash=hash_api_key(raw_key),
            name="api-routes-integration-key",
        ),
    )
    await db.commit()
    return raw_key


@pytest.mark.asyncio
async def test_api_v1_create_requires_api_key(client):
    """Create endpoint should reject requests with no API key."""
    response = await client.post("/api/v1/projects", json=_build_payload())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_v1_create_and_public_read(client, api_key):
    """Create/list/get should work end-to-end with real DB + ODK services."""
    create_response = await client.post(
        "/api/v1/projects",
        headers={"x-api-key": api_key},
        json=_build_payload(),
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()

    project_id = created["project_id"]
    assert project_id is not None
    assert "/#/projects/" in created["downstream_url"]
    assert created["manager_username"]
    assert created["manager_password"]

    list_response = await client.get("/api/v1/projects")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert any(item["id"] == project_id for item in listed)

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id

    # Keep test runs hermetic by cleaning up the FTM-side project record.
    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"x-api-key": api_key},
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_api_v1_create_accepts_custom_odk_credentials(client, api_key):
    """Create endpoint should support explicit ODK credentials in request payload."""
    create_response = await client.post(
        "/api/v1/projects",
        headers={"x-api-key": api_key},
        json=_build_payload(
            external_project_instance_url=os.getenv("ODK_CENTRAL_URL"),
            external_project_username=os.getenv("ODK_CENTRAL_USER"),
            external_project_password=os.getenv("ODK_CENTRAL_PASSWD"),
        ),
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["project_id"] is not None
    assert "/#/projects/" in created["downstream_url"]
