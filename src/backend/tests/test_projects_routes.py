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
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.central.central_crud import create_odk_project
from app.config import settings
from app.helpers.geometry_utils import check_crs

log = logging.getLogger(__name__)


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


async def test_download_osm_data_parses_geojson_object_not_string(monkeypatch):
    """Ensure OSM extract parsing passes GeoJSON object, not JSON string path."""
    from app.projects import project_services

    downloaded_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 27.71],
                            [85.30, 27.70],
                            [85.31, 27.70],
                            [85.31, 27.71],
                            [85.30, 27.71],
                        ]
                    ],
                },
                "properties": {"osm_id": 1},
            }
        ],
    }

    async def fake_get_project_by_id(_db, _project_id):
        return Mock(
            id=1,
            outline={
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.30, 27.71],
                        [85.30, 27.70],
                        [85.31, 27.70],
                        [85.31, 27.71],
                        [85.30, 27.71],
                    ]
                ],
            },
        )

    async def fake_generate_data_extract(*_args, **_kwargs):
        return Mock(data={"download_url": "https://example.test/extract.geojson"})

    class FakeResponse:
        ok = True

        async def text(self):
            return json.dumps(downloaded_geojson)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, _url):
            return FakeResponse()

    captured_input: dict = {}

    def fake_parse_aoi(_db_url, input_geojson, merge=True):
        captured_input["value"] = input_geojson
        return input_geojson

    def fake_featcol_keep_single_geom_type(featcol):
        return featcol

    async def fake_check_crs(_featcol):
        return None

    monkeypatch.setattr(
        project_services.project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_services.project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )
    monkeypatch.setattr(project_services.aiohttp, "ClientSession", FakeSession)
    monkeypatch.setattr(project_services, "parse_aoi", fake_parse_aoi)
    monkeypatch.setattr(
        project_services,
        "featcol_keep_single_geom_type",
        fake_featcol_keep_single_geom_type,
    )
    monkeypatch.setattr(project_services, "check_crs", fake_check_crs)

    result = await project_services.download_osm_data(
        db=Mock(),
        project_id=1,
        osm_category="buildings",
        geom_type="POLYGON",
        centroid=False,
    )

    assert isinstance(captured_input.get("value"), dict)
    assert result["type"] == "FeatureCollection"


@pytest.mark.parametrize(
    "algorithm",
    ["AVG_BUILDING_VORONOI", "AVG_BUILDING_SKELETON"],
)
async def test_split_aoi_building_algorithms_run_sync_without_kwargs(
    monkeypatch, algorithm
):
    """Ensure split_aoi does not pass kwargs to anyio.to_thread.run_sync."""
    from app.projects import project_services

    project = Mock(
        outline={
            "type": "Polygon",
            "coordinates": [
                [
                    [85.30, 27.71],
                    [85.30, 27.70],
                    [85.31, 27.70],
                    [85.31, 27.71],
                    [85.30, 27.71],
                ]
            ],
        },
        data_extract_geojson={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [85.30, 27.71],
                                [85.30, 27.70],
                                [85.31, 27.70],
                                [85.31, 27.71],
                                [85.30, 27.71],
                            ]
                        ],
                    },
                    "properties": {"osm_id": 1},
                }
            ],
        },
    )

    async def fake_project_one(_db, _project_id):
        return project

    captured: dict = {}

    async def fake_run_sync(func, *args):
        # Intentionally no **kwargs: old buggy code passes kwargs here.
        captured["func"] = func
        captured["args"] = args
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": project.outline,
                    "properties": {"task_id": 1},
                }
            ],
        }

    async def fake_check_crs(_featcol):
        return None

    monkeypatch.setattr(project_services.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_services.to_thread, "run_sync", fake_run_sync)
    monkeypatch.setattr(project_services, "check_crs", fake_check_crs)

    result = await project_services.split_aoi(
        db=Mock(),
        project_id=1,
        algorithm=algorithm,
        no_of_buildings=50,
    )

    assert callable(captured.get("func"))
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1


async def test_delete_project(client, admin_user, project):
    """Test deleting a Field-TM project, plus ODK Central project."""
    response = await client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


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
