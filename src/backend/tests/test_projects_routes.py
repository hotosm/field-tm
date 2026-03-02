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
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.central.central_crud import create_odk_project
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.helpers.geometry_utils import check_crs

log = logging.getLogger(__name__)


def test_create_project_request_split_defaults():
    """API split defaults should match the onboarding UI default."""
    import base64

    from app.api.api_schemas import CreateProjectRequest

    payload = CreateProjectRequest(
        project_name="test",
        field_mapping_app="ODK",
        description="test",
        outline={
            "type": "Polygon",
            "coordinates": [
                [
                    [85.317, 27.705],
                    [85.317, 27.704],
                    [85.318, 27.704],
                    [85.318, 27.705],
                    [85.317, 27.705],
                ]
            ],
        },
        xlsform_base64=base64.b64encode(b"dummy").decode(),
    )

    assert payload.no_of_buildings == 10
    assert payload.include_roads is True
    assert payload.include_rivers is True
    assert payload.include_railways is True
    assert payload.include_aeroways is True


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


async def test_download_osm_data_handles_null_features_as_no_matches(monkeypatch):
    """Null features from extract API should return a validation error."""
    from app.projects import project_services

    downloaded_geojson = {"type": "FeatureCollection", "features": None}

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

    def parse_aoi_should_not_run(*_args, **_kwargs):
        raise AssertionError("parse_aoi should not be called for empty extract results")

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
    monkeypatch.setattr(project_services, "parse_aoi", parse_aoi_should_not_run)

    with pytest.raises(
        project_services.ValidationError,
        match="No matching OSM features were found",
    ):
        await project_services.download_osm_data(
            db=Mock(),
            project_id=1,
            osm_category="highways",
            geom_type="POLYLINE",
            centroid=False,
        )


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
        options=project_services.SplitAoiOptions(
            algorithm=algorithm,
            no_of_buildings=50,
        ),
    )

    assert callable(captured.get("func"))
    algorithm_params = captured["func"].keywords["algorithm_params"]
    assert algorithm_params["num_buildings"] == 50
    assert algorithm_params["include_roads"] == "TRUE"
    assert algorithm_params["include_rivers"] == "TRUE"
    assert algorithm_params["include_railways"] == "TRUE"
    assert algorithm_params["include_aeroways"] == "TRUE"
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1


async def test_finalize_odk_project_uses_outline_geometry_for_single_task(
    monkeypatch,
):
    """Finalize should create fallback task from DbProject.outline geometry."""
    from app.projects import project_services

    project = Mock(
        id=1,
        project_name="Test Project",
        xlsform_content=b"xlsform-bytes",
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
        task_areas_geojson=None,
        outline={
            "type": "Polygon",
            "coordinates": [
                [
                    [85.40, 27.81],
                    [85.40, 27.80],
                    [85.41, 27.80],
                    [85.41, 27.81],
                    [85.40, 27.81],
                ]
            ],
        },
        external_project_id=17,
        external_project_instance_url="https://central.example.org",
    )

    async def fake_project_one(_db, _project_id):
        return project

    fake_update = AsyncMock(return_value=project)
    fake_commit = AsyncMock()
    created_datasets: list[dict] = []
    captured_outline_feature: dict = {}

    async def fake_task_geojson_dict_to_entity_values(
        _geojson, additional_features=True
    ):
        return [{"label": "Feature 1", "data": {"geometry": "g"}}]

    async def fake_feature_geojson_to_entity_dict(feature, additional_features=True):
        captured_outline_feature["value"] = feature
        return {"label": "Outline Task", "data": {"geometry": "outline-geom"}}

    async def fake_create_entity_list(
        _odk_creds,
        _odk_id,
        properties,
        dataset_name,
        entities_list,
    ):
        created_datasets.append(
            {
                "dataset_name": dataset_name,
                "properties": properties,
                "entities_list": entities_list,
            }
        )

    async def fake_read_and_test_xform(_xlsform_bytes):
        return BytesIO(b"<xml></xml>")

    async def fake_create_odk_xform(*_args, **_kwargs):
        return None

    async def fake_generate_project_files(_db, _project_id):
        return True

    async def fake_create_project_manager_user(**_kwargs):
        return ("fmtm-manager-17@example.org", "StrongPass123")

    class FakeDatasetClient:
        async def listDatasets(self, _project_odk_id):  # noqa: N802
            return []

    @asynccontextmanager
    async def fake_get_odk_dataset(_creds):
        yield FakeDatasetClient()

    db = Mock()
    db.commit = fake_commit

    monkeypatch.setattr(project_services.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_services.DbProject, "update", fake_update)
    monkeypatch.setattr(
        project_services.central_crud,
        "task_geojson_dict_to_entity_values",
        fake_task_geojson_dict_to_entity_values,
    )
    monkeypatch.setattr(
        project_services.central_crud,
        "feature_geojson_to_entity_dict",
        fake_feature_geojson_to_entity_dict,
    )
    monkeypatch.setattr(
        project_services.central_crud,
        "create_entity_list",
        fake_create_entity_list,
    )
    monkeypatch.setattr(
        project_services.central_crud,
        "read_and_test_xform",
        fake_read_and_test_xform,
    )
    monkeypatch.setattr(
        project_services.central_crud,
        "create_odk_xform",
        fake_create_odk_xform,
    )
    monkeypatch.setattr(
        project_services.central_crud,
        "create_project_manager_user",
        fake_create_project_manager_user,
    )
    monkeypatch.setattr(
        project_services.project_crud,
        "generate_project_files",
        fake_generate_project_files,
    )
    monkeypatch.setattr(
        project_services.central_deps,
        "get_odk_dataset",
        fake_get_odk_dataset,
    )

    result = await project_services.finalize_odk_project(
        db=db,
        project_id=1,
        custom_odk_creds=ODKCentral(
            external_project_instance_url="https://central.example.org",
            external_project_username="admin@example.org",
            external_project_password="password",
        ),
    )

    assert captured_outline_feature["value"]["type"] == "Feature"
    assert captured_outline_feature["value"]["geometry"] == project.outline

    tasks_dataset = next(ds for ds in created_datasets if ds["dataset_name"] == "tasks")
    assert tasks_dataset["entities_list"][0]["label"] == "Task 1"

    assert result.odk_url == "https://central.example.org/#/projects/17"
    assert result.manager_username == "fmtm-manager-17@example.org"
    assert result.manager_password == "StrongPass123"


async def test_finalize_qfield_project_allows_collect_new_data_only_mode(monkeypatch):
    """Finalize should allow an explicitly empty FeatureCollection for QField."""
    from app.db.enums import ProjectStatus
    from app.projects import project_services

    project = Mock(
        id=1,
        xlsform_content=b"xlsform-bytes",
        data_extract_geojson={"type": "FeatureCollection", "features": []},
    )

    async def fake_project_one(_db, _project_id):
        return project

    fake_update = AsyncMock(return_value=project)
    fake_commit = AsyncMock()

    async def fake_create_qfield_project(_db, _project, _custom_qfield_creds=None):
        return "https://qfield.example.org/projects/1"

    db = Mock()
    db.commit = fake_commit

    monkeypatch.setattr(project_services.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_services.DbProject, "update", fake_update)
    monkeypatch.setattr(
        "app.qfield.qfield_crud.create_qfield_project",
        fake_create_qfield_project,
    )

    result = await project_services.finalize_qfield_project(
        db=db,
        project_id=1,
    )

    assert result == "https://qfield.example.org/projects/1"
    fake_update.assert_awaited_once()
    assert fake_update.await_args.args[2].status == ProjectStatus.PUBLISHED
    fake_commit.assert_awaited_once()


async def test_get_project_qrcode_prefers_project_external_url(monkeypatch):
    """QR payload should use project external URL, not internal docker URL."""
    import base64
    import zlib

    from app.db.enums import FieldMappingApp
    from app.projects import project_crud

    project = Mock(
        id=2,
        project_name="ODK Tunnel Project",
        field_mapping_app=FieldMappingApp.ODK,
        external_project_id=2,
        external_project_instance_url="https://example-odk.trycloudflare.com",
    )
    project.get_odk_credentials = Mock(return_value=None)

    async def fake_get_project_by_id(_db, _project_id):
        return project

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class DummySession:
        def get(self, path):
            assert path == "projects/2/app-users"
            return DummyResponse([{"token": "app-token"}])

        def post(self, path, json=None):
            return DummyResponse({"token": "new-token"})

    class DummyClient:
        def __init__(self):
            self.session = DummySession()

    captured = {}

    @asynccontextmanager
    async def fake_pyodk_client(odk_creds):
        captured["resolved_url"] = odk_creds.external_project_instance_url
        yield DummyClient()

    class DummyQRCode:
        def png_data_uri(self, scale=5):
            return "data:image/png;base64,fake"

    def fake_segno_make(qr_data, micro=False):
        captured["qr_settings"] = json.loads(zlib.decompress(base64.b64decode(qr_data)))
        captured["qr_micro"] = micro
        return DummyQRCode()

    monkeypatch.setattr(
        project_crud.project_deps, "get_project_by_id", fake_get_project_by_id
    )
    monkeypatch.setattr(project_crud.central_deps, "pyodk_client", fake_pyodk_client)
    monkeypatch.setattr(project_crud.segno, "make", fake_segno_make)
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_PUBLIC_URL", "")
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_URL", "http://central:8383")
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_USER", "admin@example.org")
    monkeypatch.setattr(
        project_crud.settings,
        "ODK_CENTRAL_PASSWD",
        Mock(get_secret_value=Mock(return_value="env-pass")),
    )

    qr_data_url = await project_crud.get_project_qrcode(
        db=Mock(),
        project_id=2,
    )

    assert qr_data_url == "data:image/png;base64,fake"
    assert captured["resolved_url"] == "https://example-odk.trycloudflare.com"
    assert (
        captured["qr_settings"]["general"]["server_url"]
        == "https://example-odk.trycloudflare.com/v1/key/app-token/projects/2"
    )
    assert captured["qr_micro"] is False


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
