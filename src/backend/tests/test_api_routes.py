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
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.auth.auth_schemas import AuthUser
from app.db.enums import FieldMappingApp
from app.projects.project_routes import (
    api_create_project,
    api_get_project,
    api_list_projects,
)
from app.projects.project_schemas import CreateProjectRequest

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


def _fake_db():
    """Build a simple async DB mock for direct route tests."""
    db = Mock()
    db.commit = AsyncMock()
    return db


def _build_request(api_key: str | None = None) -> Mock:
    """Build a minimal request mock with header access."""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    return Mock(headers=headers)


def _build_payload(**overrides) -> CreateProjectRequest:
    """Create a valid API project payload."""
    payload = {
        "project_name": f"api-project-{uuid4()}",
        "field_mapping_app": "ODK",
        "description": "Create via external API",
        "outline": _OUTLINE,
        "hashtags": ["#api"],
        "xlsform_base64": _DUMMY_XLS,
        "geojson": _GEOJSON,
    }
    payload.update(overrides)
    return CreateProjectRequest(**payload)


@pytest.mark.asyncio
async def test_api_v1_create_requires_api_key():
    """Create handler should reject requests with no API key."""
    with pytest.raises(HTTPException) as exc_info:
        await api_create_project.fn(
            request=_build_request(),
            db=_fake_db(),
            data=_build_payload(),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_api_v1_create_and_public_read():
    """Create and read handlers should return project data via the shared API flow."""
    db = _fake_db()
    project = Mock(
        id=123,
        field_mapping_app=FieldMappingApp.ODK,
        project_name="api-create",
        description="Create via external API",
        status="DRAFT",
        hashtags=["#api"],
        outline=_OUTLINE,
        location_str="Kathmandu, Nepal",
    )

    with (
        patch(
            "app.projects.project_routes.api_key_required",
            new_callable=AsyncMock,
            return_value=AuthUser(
                sub="osm|1",
                username="localadmin",
                is_admin=True,
            ),
        ),
        patch(
            "app.projects.project_routes.create_project_stub",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch(
            "app.projects.project_routes.process_xlsform",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_routes.save_data_extract",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.projects.project_routes.finalize_odk_project",
            new_callable=AsyncMock,
            return_value=_FakeODKResult(),
        ),
        patch(
            "app.projects.project_routes.DbProject.all",
            new_callable=AsyncMock,
            return_value=[project],
        ),
        patch(
            "app.projects.project_routes.DbProject.one",
            new_callable=AsyncMock,
            return_value=project,
        ),
    ):
        create_response = await api_create_project.fn(
            request=_build_request("ftm_test_key"),
            db=db,
            data=_build_payload(project_name=project.project_name),
        )
        list_response = await api_list_projects.fn(db=db)
        get_response = await api_get_project.fn(project_id=project.id, db=db)

    assert create_response.downstream_url == "https://central.example.org/#/projects/1"
    assert create_response.manager_username == "manager@example.org"
    assert create_response.project_id == project.id
    assert isinstance(list_response, list)
    assert any(item["id"] == project.id for item in list_response)
    assert get_response["id"] == project.id


@pytest.mark.asyncio
async def test_api_v1_create_forwards_custom_odk_credentials():
    """Create endpoint should pass explicit ODK advanced config to service layer."""
    from app.central.central_schemas import ODKCentral

    db = _fake_db()
    project = Mock(id=456, field_mapping_app=FieldMappingApp.ODK)
    payload = _build_payload(
        project_name=f"api-custom-odk-{uuid4()}",
        external_project_instance_url="https://example-odk.trycloudflare.com",
        external_project_username="admin@example.org",
        external_project_password="test-password",
    )

    with (
        patch(
            "app.projects.project_routes.api_key_required",
            new_callable=AsyncMock,
            return_value=AuthUser(
                sub="osm|1",
                username="localadmin",
                is_admin=True,
            ),
        ),
        patch(
            "app.projects.project_routes.create_project_stub",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch(
            "app.projects.project_routes.process_xlsform",
            new_callable=AsyncMock,
        ),
        patch(
            "app.projects.project_routes.save_data_extract",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "app.projects.project_routes.finalize_odk_project",
            new_callable=AsyncMock,
            return_value=_FakeODKResult(),
        ) as mock_finalize,
    ):
        create_response = await api_create_project.fn(
            request=_build_request("ftm_test_key"),
            db=db,
            data=payload,
        )

    assert create_response.project_id == project.id
    mock_finalize.assert_awaited_once()

    custom_odk = mock_finalize.await_args.kwargs["custom_odk_creds"]
    assert isinstance(custom_odk, ODKCentral)
    assert (
        custom_odk.external_project_instance_url
        == payload.external_project_instance_url
    )
    assert custom_odk.external_project_username == payload.external_project_username
    assert custom_odk.external_project_password == payload.external_project_password
