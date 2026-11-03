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

import base64
import json
import os
import zlib
from contextlib import asynccontextmanager
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.central.central_crud import create_odk_project
from app.central.central_schemas import ODKCentral
from app.db.enums import FieldMappingApp, ProjectStatus
from app.errors import UpstreamError
from app.helpers.geometry_utils import check_crs, featcol_polygons_to_centroids
from app.projects import (
    data_extract_services,
    odk_services,
    project_crud,
    project_deps,
    project_services,
)
from app.projects.project_schemas import ProjectUpdate


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


def test_project_update_accepts_qfield_uuid_external_project_id():
    """QFieldCloud UUID project IDs should validate for project updates."""
    qfield_project_id = "becce310-e99e-4a7e-b1db-9e3f00e2c5ba"

    payload = ProjectUpdate(external_project_id=qfield_project_id)

    assert payload.external_project_id == qfield_project_id


async def test_download_osm_data_parses_geojson_object_not_string(monkeypatch):
    """Ensure OSM extract parsing passes GeoJSON object, not JSON string path."""
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

    async def fake_download(_url):
        return downloaded_geojson

    captured_input: dict = {}

    def fake_parse_aoi(_db_url, input_geojson, merge=True):
        captured_input["value"] = input_geojson
        return input_geojson

    def fake_featcol_keep_single_geom_type(featcol, geom_type=None):
        return featcol

    async def fake_check_crs(_featcol):
        return None

    monkeypatch.setattr(
        project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )
    monkeypatch.setattr(
        data_extract_services, "_download_extract_geojson", fake_download
    )
    monkeypatch.setattr(data_extract_services, "parse_aoi", fake_parse_aoi)
    monkeypatch.setattr(
        data_extract_services,
        "featcol_keep_single_geom_type",
        fake_featcol_keep_single_geom_type,
    )
    monkeypatch.setattr(data_extract_services, "check_crs", fake_check_crs)

    result = await data_extract_services.download_osm_data(
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

    async def fake_download(_url):
        return downloaded_geojson

    def parse_aoi_should_not_run(*_args, **_kwargs):
        raise AssertionError("parse_aoi should not be called for empty extract results")

    monkeypatch.setattr(
        project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )
    monkeypatch.setattr(
        data_extract_services, "_download_extract_geojson", fake_download
    )
    monkeypatch.setattr(data_extract_services, "parse_aoi", parse_aoi_should_not_run)

    with pytest.raises(
        project_services.ValidationError,
        match=(
            "No data found in OSM. Please continue with the Collect New "
            "Data Only option."
        ),
    ):
        await data_extract_services.download_osm_data(
            db=Mock(),
            project_id=1,
            osm_category="highways",
            geom_type="POLYLINE",
            centroid=False,
        )


async def test_download_osm_data_maps_invalid_geometry_parse_to_validation_error(
    monkeypatch,
):
    """Invalid extract geometries should return actionable validation guidance."""
    downloaded_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": None,
                "properties": {"osm_id": 101},
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

    async def fake_download(_url):
        return downloaded_geojson

    def fake_parse_aoi(*_args, **_kwargs):
        raise TypeError("'NoneType' object is not iterable")

    monkeypatch.setattr(
        project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )
    monkeypatch.setattr(
        data_extract_services, "_download_extract_geojson", fake_download
    )
    monkeypatch.setattr(data_extract_services, "parse_aoi", fake_parse_aoi)

    with pytest.raises(
        project_services.ValidationError,
        match=(
            "No valid geometries found in OSM for the selected extract settings. "
            "Please continue with the Collect New Data Only option."
        ),
    ):
        await data_extract_services.download_osm_data(
            db=Mock(),
            project_id=1,
            osm_category="buildings",
            geom_type="POLYGON",
            centroid=False,
        )


async def test_download_osm_data_maps_extract_generation_failure(monkeypatch):
    """Raw-data extraction failures should return actionable guidance."""

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
        raise UpstreamError("Failed to generate data extract from the raw data API.")

    monkeypatch.setattr(
        project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )

    with pytest.raises(
        project_services.ServiceError,
        match=(
            "OSM data extraction timed out or failed upstream. "
            "Please reduce the AOI size or choose Collect New Data Only."
        ),
    ):
        await data_extract_services.download_osm_data(
            db=Mock(),
            project_id=1,
            osm_category="buildings",
            geom_type="POLYGON",
            centroid=False,
        )


async def test_download_osm_data_computes_centroids_locally(monkeypatch):
    """'Use centroids' requests polygons and converts them to points here."""
    downloaded_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 27.70],
                            [85.31, 27.70],
                            [85.31, 27.71],
                            [85.30, 27.71],
                            [85.30, 27.70],
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

    captured: dict = {}

    async def fake_generate_data_extract(
        project_id, aoi, geom_types, config_data, centroid, use_st_within
    ):
        captured["geom_types"] = geom_types
        captured["centroid"] = centroid
        captured["config_from"] = config_data.get("from")
        return Mock(data={"download_url": "https://example.test/extract.geojson"})

    async def fake_download(_url):
        return downloaded_geojson

    def fake_parse_aoi(_db_url, input_geojson, merge=True):
        return input_geojson

    async def fake_check_crs(_featcol):
        return None

    monkeypatch.setattr(
        project_deps,
        "get_project_by_id",
        fake_get_project_by_id,
    )
    monkeypatch.setattr(
        project_crud,
        "generate_data_extract",
        fake_generate_data_extract,
    )
    monkeypatch.setattr(
        data_extract_services, "_download_extract_geojson", fake_download
    )
    monkeypatch.setattr(data_extract_services, "parse_aoi", fake_parse_aoi)
    monkeypatch.setattr(data_extract_services, "check_crs", fake_check_crs)

    result = await data_extract_services.download_osm_data(
        db=Mock(),
        project_id=1,
        osm_category="buildings",
        geom_type="POLYGON",
        centroid=True,
    )

    assert captured["centroid"] is False
    assert captured["geom_types"] == ["polygon"]
    # POLYGON + centroid must resolve to ways_poly, not None
    assert captured["config_from"] == ["ways_poly"]
    [feature] = result["features"]
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == pytest.approx([85.305, 27.705])
    assert feature["properties"] == {"osm_id": 1}


async def test_featcol_polygons_to_centroids_keeps_points():
    """Point mode with centroids mixes OSM nodes and polygon centroids."""
    square = [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]
    featcol = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [5, 5]}},
            {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": square}},
            {
                "type": "Feature",
                "geometry": {"type": "MultiPolygon", "coordinates": [square]},
            },
        ],
    }

    result = await featcol_polygons_to_centroids(featcol)

    assert [f["geometry"] for f in result["features"]] == [
        {"type": "Point", "coordinates": [5, 5]},
        {"type": "Point", "coordinates": [1.0, 1.0]},
        {"type": "Point", "coordinates": [1.0, 1.0]},
    ]


def test_configure_extract_sources_polygon_centroid_maps_to_ways_poly():
    """Polygon + centroid should select ways_poly so the config isn't malformed."""
    config, geom_types = data_extract_services._configure_extract_sources(
        {}, "POLYGON", centroid=True
    )
    assert config["from"] == ["ways_poly"]
    assert geom_types == ["polygon"]


def test_configure_extract_sources_polyline_centroid_maps_to_ways_line():
    """Polyline + centroid should select ways_line and report 'line' to raw-data-api."""
    config, geom_types = data_extract_services._configure_extract_sources(
        {}, "POLYLINE", centroid=True
    )
    assert config["from"] == ["ways_line"]
    assert geom_types == ["line"]


def test_configure_extract_sources_point_centroid_unions_polygon_and_point():
    """Point + centroid should union ways_poly (centroid-ified) with OSM nodes."""
    config, geom_types = data_extract_services._configure_extract_sources(
        {}, "POINT", centroid=True
    )
    assert config["from"] == ["ways_poly", "nodes"]
    assert geom_types == ["polygon", "point"]


def test_configure_extract_sources_point_no_centroid_queries_nodes_only():
    """Point without centroid should only query OSM nodes."""
    config, geom_types = data_extract_services._configure_extract_sources(
        {}, "POINT", centroid=False
    )
    assert config["from"] == ["nodes"]
    assert geom_types == ["point"]


@pytest.mark.parametrize(
    "algorithm",
    ["AVG_BUILDING_VORONOI", "AVG_BUILDING_SKELETON"],
)
async def test_split_aoi_building_algorithms_run_sync_without_kwargs(
    monkeypatch, algorithm
):
    """Ensure split_aoi does not pass kwargs to anyio.to_thread.run_sync."""
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
        db=Mock(commit=AsyncMock()),
        project_id=1,
        algorithm=algorithm,
        num_buildings=50,
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
        **_kwargs,
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
        return ("field-tm-manager-17@fieldtm.org", "StrongPass123")

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
        project_crud,
        "generate_project_files",
        fake_generate_project_files,
    )

    result = await odk_services.finalize_odk_project(
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
    assert {"assigned_group", "assigned_to", "comment", "colour"} <= set(
        tasks_dataset["properties"]
    )

    assert result.odk_url == "https://central.example.org/#/projects/17"
    assert result.manager_username == "field-tm-manager-17@fieldtm.org"
    assert result.manager_password == "StrongPass123"


async def test_finalize_qfield_project_allows_collect_new_data_only_mode(monkeypatch):
    """Finalize should allow an explicitly empty FeatureCollection for QField."""
    project = Mock(
        id=1,
        xlsform_content=b"xlsform-bytes",
        data_extract_geojson={"type": "FeatureCollection", "features": []},
        task_areas_geojson=None,
    )

    async def fake_project_one(_db, _project_id):
        return project

    fake_update = AsyncMock(return_value=project)
    fake_commit = AsyncMock()

    async def fake_create_qfield_project(
        _db,
        _project,
        _custom_qfield_creds=None,
        default_language=None,
    ):
        return "https://qfield.example.org/projects/1"

    db = Mock()
    db.commit = fake_commit

    monkeypatch.setattr(project_services.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_services.DbProject, "update", fake_update)
    monkeypatch.setattr(
        project_services,
        "create_qfield_project",
        fake_create_qfield_project,
    )

    result = await project_services.finalize_qfield_project(
        db=db,
        project_id=1,
    )

    assert result.qfield_url == "https://qfield.example.org/projects/1"
    fake_update.assert_awaited_once()
    assert fake_update.await_args.args[2].status == ProjectStatus.PUBLISHED
    fake_commit.assert_awaited_once()


async def test_get_project_qr_data_prefers_project_external_url(monkeypatch):
    """QR payload should use project external URL, not internal docker URL."""
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

    monkeypatch.setattr(
        project_crud.project_deps, "get_project_by_id", fake_get_project_by_id
    )
    monkeypatch.setattr(project_crud.central_deps, "pyodk_client", fake_pyodk_client)
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_PUBLIC_URL", "")
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_URL", "http://central:8383")
    monkeypatch.setattr(project_crud.settings, "ODK_CENTRAL_USER", "admin@example.org")
    monkeypatch.setattr(
        project_crud.settings,
        "ODK_CENTRAL_PASSWD",
        Mock(get_secret_value=Mock(return_value="env-pass")),
    )

    qr_data = await project_crud.get_project_qr_data(db=Mock(), project_id=2)

    qr_settings = json.loads(zlib.decompress(base64.b64decode(qr_data)))
    assert captured["resolved_url"] == "https://example-odk.trycloudflare.com"
    assert (
        qr_settings["general"]["server_url"]
        == "https://example-odk.trycloudflare.com/v1/key/app-token/projects/2"
    )


async def test_delete_project_with_downstream_deletes_ftm_after_remote(monkeypatch):
    """Service should delete local project after successful downstream deletion."""
    project = SimpleNamespace(
        id=19,
        field_mapping_app=FieldMappingApp.ODK,
        external_project_id=45,
    )
    db = Mock()

    monkeypatch.setattr(
        project_services.DbProject,
        "one",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        project_services,
        "_delete_odk_downstream_project",
        AsyncMock(return_value="already deleted"),
    )
    delete_mock = AsyncMock()
    monkeypatch.setattr(project_services.DbProject, "delete", delete_mock)

    result = await project_services.delete_project_with_downstream(db, 19)

    assert "already deleted" in result.downstream_status
    delete_mock.assert_awaited_once_with(db, 19)


async def test_delete_project_with_downstream_keeps_ftm_on_remote_failure(monkeypatch):
    """Service should not delete local project if downstream deletion fails."""
    project = SimpleNamespace(
        id=20,
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="abc-123",
    )
    db = Mock()

    monkeypatch.setattr(
        project_services.DbProject,
        "one",
        AsyncMock(return_value=project),
    )
    monkeypatch.setattr(
        project_services,
        "_delete_qfield_downstream_project",
        AsyncMock(
            side_effect=project_services.DownstreamDeleteError("remote deletion failed")
        ),
    )
    delete_mock = AsyncMock()
    monkeypatch.setattr(project_services.DbProject, "delete", delete_mock)

    with pytest.raises(project_services.DownstreamDeleteError):
        await project_services.delete_project_with_downstream(db, 20)

    delete_mock.assert_not_awaited()


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()


async def test_fail_stale_jobs_marks_old_in_progress_jobs_failed(
    db, project, stub_project
):
    """Jobs older than 30 minutes fail; recent ones keep running."""
    old = "now() - interval '2 hours'"
    async with db.cursor() as cur:
        await cur.execute(
            f"""
            UPDATE projects SET creation_status = 'in_progress',
                creation_updated_at = {old},
                basemap_attach_status = 'in_progress',
                basemap_attach_updated_at = {old},
                updated_at = {old}
            WHERE id = %(id)s
            """,  # noqa: S608
            {"id": project.id},
        )
        await cur.execute(
            """
            UPDATE projects SET creation_status = 'in_progress',
                creation_updated_at = now()
            WHERE id = %(id)s
            """,
            {"id": stub_project.id},
        )
        await cur.execute(
            """
            INSERT INTO qgis_jobs (job_id, created_at)
            VALUES (gen_random_uuid(), now() - interval '2 hours'),
                   (gen_random_uuid(), now())
            RETURNING job_id
            """
        )
        old_job, new_job = [row[0] for row in await cur.fetchall()]
    await db.commit()

    await project_crud.fail_stale_jobs(db)

    stale = await project_crud.DbProject.one(db, project.id)
    assert stale.creation_status == "failed"
    assert stale.creation_error
    assert stale.basemap_attach_status == "failed"
    fresh = await project_crud.DbProject.one(db, stub_project.id)
    assert fresh.creation_status == "in_progress"
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT job_id FROM qgis_jobs WHERE job_id = ANY(%(ids)s)",
            {"ids": [old_job, new_job]},
        )
        remaining = [row[0] for row in await cur.fetchall()]
    assert remaining == [new_job]


async def test_download_extract_geojson(monkeypatch):
    """The extract is fetched with httpx; HTTP errors become ServiceErrors."""
    featcol = {"type": "FeatureCollection", "features": []}
    codes = iter([200, 500])

    def handler(_request):
        return httpx.Response(next(codes), json=featcol)

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        data_extract_services.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    url = "https://extract.example.org/a.geojson"
    assert await data_extract_services._download_extract_geojson(url) == featcol
    with pytest.raises(project_services.ServiceError):
        await data_extract_services._download_extract_geojson(url)
