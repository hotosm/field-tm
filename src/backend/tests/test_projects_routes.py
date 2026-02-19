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
"""Tests for project routes."""

import json
import logging
import os
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from httpx import AsyncClient
from litestar import status_codes as status

from app.central.central_crud import create_odk_project
from app.config import settings
from app.db.models import DbProject, slugify
from app.helpers.geometry_utils import check_crs
from app.projects import project_crud
from tests.test_data import test_data_path

log = logging.getLogger(__name__)


async def create_stub_project(client, stub_project_data):
    """Create a new project."""
    response = await client.post("/projects/stub", json=stub_project_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def test_patch_project_invalid(client, project, project_data):
    """Test project creation endpoint, duplicate checker."""
    log.debug(f"Existing project: {project}")
    # First update the project name to ensure it doesn't exist and
    # trigger duplicate validation
    project_data["project_name"] = "a new project name that doesn't exist"
    # Then use invalid enum options for some fields
    project_data["task_split_type"] = "invalid_option"
    project_data["priority"] = "invalid_option"
    response_invalid = await client.patch(
        f"/projects?project_id={project.id}",
        json=project_data,
    )
    assert response_invalid.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response_invalid.json()

    expected_errors = {
        "task_split_type": (
            "'DIVIDE_BY_SQUARE', 'CHOOSE_AREA_AS_TASK' or 'TASK_SPLITTING_ALGORITHM'"
        ),
        "priority": "'MEDIUM', 'LOW', 'HIGH' or 'URGENT'",
    }

    for error in response_data["detail"]:
        # Get the field name from the last element of the 'loc' list
        field_name = error["loc"][-1]
        if field_name in expected_errors:
            assert error["ctx"]["expected"] == expected_errors[field_name]


async def test_patch_project_dup_name(client, project, project_data):
    """Test project patch to a duplicate name is not possible."""
    log.debug(f"Existing project: {project}")
    # First update the project name to ensure it doesn't exist and
    # trigger duplicate validation
    project_data["project_name"] = "new project name"
    response_duplicate = await client.patch(
        f"/projects?project_id={project.id}",
        json=project_data,
    )
    assert response_duplicate.status_code == status.HTTP_409_CONFLICT
    assert (
        response_duplicate.json()["detail"]
        == f"Project with name '{project_data['project_name']}' already exists."
    )


async def test_create_project_with_dup(client, stub_project_data):
    """Test project creation endpoint, duplicate checker."""
    project_name = stub_project_data["project_name"]

    new_project = await create_stub_project(client, stub_project_data)
    assert "id" in new_project
    assert isinstance(new_project["id"], int)
    assert isinstance(new_project["slug"], str)
    assert new_project["slug"] == slugify(project_name)
    assert new_project["location_str"] == "Kathmandu,Nepal"

    # Duplicate response to test error condition: project name already exists
    response_duplicate = await client.post("/projects/stub", json=stub_project_data)

    assert response_duplicate.status_code == status.HTTP_409_CONFLICT
    assert (
        response_duplicate.json()["detail"]
        == f"Project with name '{project_name}' already exists."
    )


@pytest.mark.parametrize(
    "geojson_type",
    [
        {
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
        {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [85.317028828, 27.7052522097],
                        [85.317028828, 27.7041424888],
                        [85.318844411, 27.7041424888],
                        [85.318844411, 27.7052522097],
                        [85.317028828, 27.7052522097],
                    ]
                ]
            ],
        },
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
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
        },
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
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
                }
            ],
        },
        {
            "type": "LineString",
            "coordinates": [
                [85.317028828, 27.7052522097],
                [85.318844411, 27.7041424888],
            ],
        },
        {
            "type": "MultiLineString",
            "coordinates": [
                [[85.317028828, 27.7052522097], [85.318844411, 27.7041424888]]
            ],
        },
    ],
)
async def test_valid_geojson_types(client, project_data, geojson_type):
    """Test valid geojson types."""
    project_data["outline"] = geojson_type
    response_data = await create_project(client, project_data)
    assert "id" in response_data


@pytest.mark.parametrize(
    "geojson_type",
    [
        {"type": "Point", "coordinates": [85.317028828, 27.7052522097]},
        {
            "type": "MultiPoint",
            "coordinates": [
                [85.317028828, 27.7052522097],
                [85.318844411, 27.7041424888],
            ],
        },
    ],
)
async def test_invalid_geojson_types(client, project_data, geojson_type):
    """Test invalid geojson types."""
    project_data["outline"] = geojson_type
    response = await client.patch("/projects", json=project_data)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "crs",
    [
        {"type": "name", "properties": {"name": "GGRS87"}},
        {"type": "name", "properties": {"name": "NAD83"}},
        {"type": "name", "properties": {"name": "NAD27"}},
    ],
)
async def test_unsupported_crs(stub_project_data, crs):
    """Test unsupported CRS in GeoJSON."""
    stub_project_data["outline"]["crs"] = crs
    # NOTE: We intentionally avoid importing framework-specific HTTP exceptions here.
    # The underlying implementation raises an HTTP-style exception that exposes
    # a `status_code` attribute; we assert on that contract rather than the
    # concrete exception type.
    with pytest.raises(Exception) as exc_info:
        await check_crs(stub_project_data["outline"])
    assert getattr(exc_info.value, "status_code", None) == 400


async def create_project(client, project_data):
    """Create a new project."""
    response = await client.post("/projects/stub", json=project_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest.mark.parametrize(
    "hashtag_input, expected_output",
    [
        ("tag1, tag2, tag3", ["#tag1", "#tag2", "#tag3", "#Field-TM"]),
        ("tag1   tag2    tag3", ["#tag1", "#tag2", "#tag3", "#Field-TM"]),
        ("tag1, tag2 tag3    tag4", ["#tag1", "#tag2", "#tag3", "#tag4", "#Field-TM"]),
        ("TAG1, tag2 #TAG3", ["#TAG1", "#tag2", "#TAG3", "#Field-TM"]),
    ],
)
async def test_project_hashtags(
    client,
    project_data,
    stub_project_data,
    hashtag_input,
    expected_output,
):
    """Test hashtag parsing."""
    project_data["hashtags"] = hashtag_input
    response_data = await create_stub_project(client, stub_project_data)
    project_id = response_data["id"]
    assert "id" in response_data
    response = await client.patch(
        f"/projects?project_id={project_id}", json=project_data
    )
    response_data = response.json()
    assert response_data["hashtags"][:-1] == expected_output
    assert response_data["hashtags"][-1] == f"#{settings.FMTM_DOMAIN}-{project_id}"


async def test_delete_project(client, admin_user, project):
    """Test deleting a Field-TM project, plus ODK Central project."""
    response = await client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


async def test_create_odk_project():
    """Test creating an odk central project."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": 123, "name": "Field-TM Test Project"}

    odk_credentials = {
        "external_project_instance_url": os.getenv("ODK_CENTRAL_URL"),
        "external_project_username": os.getenv("ODK_CENTRAL_USER"),
        "external_project_password": os.getenv("ODK_CENTRAL_PASSWD"),
    }

    class DummyClient:
        def __init__(self):
            self.session = Mock()
            self.session.base_url = "https://example.com"
            self.session.post.return_value = mock_response

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield DummyClient()

    with patch("app.central.central_crud.central_deps.pyodk_client", fake_pyodk_client):
        result = await create_odk_project("Test Project", odk_credentials)

    assert result == {"id": 123, "name": "Field-TM Test Project"}


async def test_upload_data_extracts(client, project):
    """Test uploading data extracts in GeoJSON and flatgeobuf formats."""
    geojson_file = {
        "data_extract_file": (
            "file.geojson",
            open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb"),
        )
    }
    response = await client.post(
        f"/projects/upload-data-extract?project_id={project.id}",
        files=geojson_file,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/projects/data-extract-url?project_id={project.id}",
    )
    assert "url" in response.json()


async def test_generate_project_files(db, client, project):
    """Test generate all appuser files (during creation)."""
    project_id = project.id
    log.debug(f"Testing project ID: {project_id}")

    # First generate a single task from the project area
    task_geojson = json.dumps(
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.29998911, 27.7140080437],
                        [85.29998911, 27.7108923499],
                        [85.304783157, 27.7108923499],
                        [85.304783157, 27.7140080437],
                        [85.29998911, 27.7140080437],
                    ]
                ],
            },
        }
    ).encode("utf-8")
    task_geojson_file = {
        "task_geojson": (
            "file.geojson",
            BytesIO(task_geojson).read(),
        )
    }
    response = await client.post(
        f"/projects/{project_id}/upload-task-boundaries",
        files=task_geojson_file,
    )
    assert response.status_code == 201

    # Upload data extracts
    with open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb") as f:
        data_extracts = json.dumps(json.load(f))
    log.debug(f"Uploading custom data extracts: {str(data_extracts)[:100]}...")
    data_extract_s3_path = await project_crud.upload_geojson_data_extract(
        db,
        project_id,
        data_extracts,
    )
    assert data_extract_s3_path is not None
    internal_s3_url = f"{settings.S3_ENDPOINT}{urlparse(data_extract_s3_path).path}"
    async with AsyncClient() as client_httpx:
        response = await client_httpx.head(internal_s3_url, follow_redirects=True)
        assert response.status_code < 400, (
            f"HEAD request failed with status {response.status_code}"
        )

    # Get custom XLSForm path
    xlsform_file = Path(f"{test_data_path}/buildings.xls")
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    response = await client.post(
        f"/central/upload-xlsform?project_id={project_id}",
        files={
            "xlsform": (
                "buildings.xls",
                xlsform_obj,
            )
        },
    )
    assert response.status_code == 200

    response = await client.post(
        f"/projects/{project_id}/generate-project-data",
    )
    assert response.status_code == 200

    # Now check required values were added to project
    new_project = await DbProject.one(db, project_id)
    assert isinstance(new_project.odk_token, str)


async def test_update_project(client, admin_user, project):
    """Test update project metadata."""
    updated_project_data = {
        "project_name": f"Updated Test Project {uuid4()}",
        "description": "updated description",
        "hashtags": "#Field-TM anothertag",
    }

    response = await client.patch(f"/projects/{project.id}", json=updated_project_data)

    if response.status_code != 200:
        log.error(response.json())
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["project_name"] == updated_project_data["project_name"]
    assert response_data["description"] == updated_project_data["description"]

    assert sorted(response_data["hashtags"]) == sorted(
        [
            "#Field-TM",
            f"#{settings.FMTM_DOMAIN}-{response_data['id']}",
            "#anothertag",
        ]
    )


async def test_project_summaries(client, project):
    """Test read project summaries."""
    response = await client.get("/projects/summaries")
    assert response.status_code == 200
    assert "results" in response.json()

    first_project = response.json()["results"][0]

    assert first_project["id"] == project.id
    assert first_project["project_name"] == project.project_name
    assert first_project["hashtags"] == project.hashtags


async def test_project_by_id(client, project):
    """Test read project by id."""
    response = await client.get(f"/projects/{project.id}?project_id={project.id}")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project.id
    assert data["external_project_id"] == project.external_project_id
    assert data["created_by_sub"] == project.created_by_sub
    assert data["project_name"] == project.project_name
    assert data["description"] == project.description
    assert data["status"] == project.status
    assert data["hashtags"] == project.hashtags
    assert data["location_str"] == project.location_str


async def test_project_task_split(client):
    """Test project AOI splitting into tasks."""
    aoi_geojson = json.dumps(
        {
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
    ).encode("utf-8")
    aoi_geojson_file = {
        "project_geojson": (
            "kathmandu_aoi.geojson",
            BytesIO(aoi_geojson).read(),
        )
    }

    response = await client.post(
        "/projects/task-split",
        files=aoi_geojson_file,
        data={"no_of_buildings": 40},
    )

    assert response.status_code == 200
    assert response.json() is not None
    assert "features" in response.json()

    # Test without required value should cause validation error
    response = await client.post("/projects/task-split")
    assert response.status_code == 422


async def test_read_project(client, project):
    """Test read project by id."""
    response = await client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["external_project_id"] == project.external_project_id
    assert data["project_name"] == project.project_name


async def test_download_project_boundary(client, project):
    """Test downloading a project boundary as GeoJSON."""
    response = await client.get(f"/projects/{project.id}/download")

    assert response.status_code == 200
    assert (
        response.headers["Content-Disposition"]
        == f"attachment; filename={project.slug}.geojson"
    )
    assert response.headers["Content-Type"] == "application/media"

    content = json.loads(response.content)
    assert content["type"] == "Polygon"
    assert "coordinates" in content
    assert isinstance(content["coordinates"], list)


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
