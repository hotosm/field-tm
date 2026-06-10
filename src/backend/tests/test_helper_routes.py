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
"""Tests for helper routes."""

import csv
import json
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.central.central_routes import odk_creds_test
from app.config import settings

HELPERS_PREFIX = "/api/v1/helpers"

# A single Polygon AOI around Kathmandu
_POLYGON_FEATCOL = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.299989110, 27.7140080437],
                        [85.299989110, 27.7108923499],
                        [85.304783157, 27.7108923499],
                        [85.304783157, 27.7140080437],
                        [85.299989110, 27.7140080437],
                    ]
                ],
            },
        }
    ],
}

# Two disjoint polygons as a single MultiPolygon feature
_MULTIPOLYGON_FEATCOL = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [85.299989110, 27.7140080437],
                            [85.299989110, 27.7108923499],
                            [85.304783157, 27.7108923499],
                            [85.304783157, 27.7140080437],
                            [85.299989110, 27.7140080437],
                        ]
                    ],
                    [
                        [
                            [85.317028828, 27.7052522097],
                            [85.317028828, 27.7041424888],
                            [85.318844411, 27.7041424888],
                            [85.318844411, 27.7052522097],
                            [85.317028828, 27.7052522097],
                        ]
                    ],
                ],
            },
        }
    ],
}


@pytest.fixture(autouse=True)
def _local_admin_auth(monkeypatch):
    """Route requests through the debug local-admin auth path.

    The helper routes depend on login_required, which otherwise needs a
    live hotosm-auth session cookie.
    """
    monkeypatch.setattr(settings, "DEBUG", True)


async def test_helper_odk_creds_test():
    """The surviving ODK JSON route should still validate credentials."""
    with patch(
        "app.central.central_routes.central_crud.odk_credentials_test",
        new_callable=AsyncMock,
    ) as mock_test_odk:
        await odk_creds_test.fn(
            external_project_instance_url="http://central:8383",
            external_project_username="admin@hotosm.org",
            external_project_password="Password1234",
        )

    mock_test_odk.assert_awaited_once()


# ---------------------------------------------------------------------------
# GET /download-template-xlsform
# ---------------------------------------------------------------------------


async def test_download_template_xlsform_success(client):
    """A bundled XLSForm template should download as a valid XLSX file."""
    response = await client.get(
        f"{HELPERS_PREFIX}/download-template-xlsform",
        params={"form_type": "OSM Buildings"},
    )

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"] == "attachment; filename=buildings.xlsx"
    )
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # XLSX files are zip archives, which always start with the PK magic bytes
    assert response.content[:2] == b"PK"


async def test_download_template_xlsform_invalid_form_type(client):
    """An unknown form_type should be rejected by enum validation."""
    response = await client.get(
        f"{HELPERS_PREFIX}/download-template-xlsform",
        params={"form_type": "not-a-real-form"},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /convert-geojson-to-odk-csv
# ---------------------------------------------------------------------------


async def test_convert_geojson_to_odk_csv_success(client):
    """A valid GeoJSON upload should convert to ODK CSV upload media."""
    response = await client.post(
        f"{HELPERS_PREFIX}/convert-geojson-to-odk-csv",
        files={
            "geojson": (
                "features.geojson",
                json.dumps(_POLYGON_FEATCOL).encode("utf-8"),
                "application/geo+json",
            )
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"] == "attachment; filename=features.csv"
    )

    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 1
    expected_columns = {
        "osm_id",
        "tags",
        "version",
        "changeset",
        "timestamp",
        "geometry",
    }
    assert expected_columns.issubset(rows[0].keys())
    # Geometry must be converted to JavaRosa format (lat lon alt acc; ...)
    assert rows[0]["geometry"]
    first_point = rows[0]["geometry"].split(";")[0].split()
    assert len(first_point) == 4


async def test_convert_geojson_to_odk_csv_invalid_extension(client):
    """A non-GeoJSON file extension should be rejected."""
    response = await client.post(
        f"{HELPERS_PREFIX}/convert-geojson-to-odk-csv",
        files={"geojson": ("features.txt", b"not geojson", "text/plain")},
    )

    assert response.status_code == 400
    assert "valid .json or .geojson" in response.text


# ---------------------------------------------------------------------------
# POST /create-entities-from-csv
# ---------------------------------------------------------------------------


async def test_create_entities_from_csv_success(client):
    """A valid CSV upload should create ODK Entities via Central."""
    mock_odk_central = AsyncMock()
    mock_odk_central.createEntities.return_value = {"success": True}
    mock_dataset_ctx = MagicMock()
    mock_dataset_ctx.__aenter__.return_value = mock_odk_central

    with patch(
        "app.helpers.helper_routes.central_deps.get_odk_dataset",
        return_value=mock_dataset_ctx,
    ):
        response = await client.post(
            f"{HELPERS_PREFIX}/create-entities-from-csv",
            params={"odk_project_id": 1, "entity_name": "features"},
            files={
                "data": ("entities.csv", b"label,status\nfeature1,ready", "text/csv")
            },
        )

    assert response.status_code == 201
    assert response.json() == {"success": True}
    mock_odk_central.createEntities.assert_awaited_once()
    # One CSV row should map to exactly one entity, keyed by generated UUID
    _, entity_name, entities = mock_odk_central.createEntities.await_args.args
    assert entity_name == "features"
    assert list(entities.values()) == [{"label": "feature1", "status": "ready"}]


async def test_create_entities_from_csv_invalid_extension(client):
    """A non-CSV file extension should be rejected."""
    response = await client.post(
        f"{HELPERS_PREFIX}/create-entities-from-csv",
        params={"odk_project_id": 1, "entity_name": "features"},
        files={"data": ("entities.txt", b"label\nfeature1", "text/plain")},
    )

    assert response.status_code == 400
    assert "valid .csv" in response.text


# ---------------------------------------------------------------------------
# POST /javarosa-geom-to-geojson
# ---------------------------------------------------------------------------


async def test_javarosa_geom_to_geojson_point(client):
    """A single JavaRosa point should convert to a GeoJSON Point."""
    response = await client.post(
        f"{HELPERS_PREFIX}/javarosa-geom-to-geojson",
        params={"javarosa_string": "27.7108923499 85.2999891100 0.0 0.0"},
    )

    assert response.status_code == 201
    geometry = response.json()
    assert geometry["type"] == "Point"
    assert geometry["coordinates"] == [85.29998911, 27.7108923499]


async def test_javarosa_geom_to_geojson_polygon(client):
    """A closed JavaRosa coordinate loop should convert to a GeoJSON Polygon."""
    javarosa_string = (
        "27.7140080437 85.2999891100 0.0 0.0;"
        "27.7108923499 85.2999891100 0.0 0.0;"
        "27.7108923499 85.3047831570 0.0 0.0;"
        "27.7140080437 85.2999891100 0.0 0.0"
    )
    response = await client.post(
        f"{HELPERS_PREFIX}/javarosa-geom-to-geojson",
        params={"javarosa_string": javarosa_string},
    )

    assert response.status_code == 201
    geometry = response.json()
    assert geometry["type"] == "Polygon"
    # One ring, closed (first == last)
    assert len(geometry["coordinates"]) == 1
    assert geometry["coordinates"][0][0] == geometry["coordinates"][0][-1]


# ---------------------------------------------------------------------------
# POST /convert-odk-submission-json-to-geojson
# ---------------------------------------------------------------------------


async def test_convert_odk_submission_json_to_geojson_success(client):
    """An ODK submission JSON list should convert to a GeoJSON download."""
    submission = [
        {
            "meta": {"instanceID": "uuid:test"},
            "__id": "uuid:test",
            "__system": {"submitterId": "1"},
            "xlocation": "27.7108923499 85.2999891100 0.0 0.0",
            "status": "complete",
        }
    ]
    response = await client.post(
        f"{HELPERS_PREFIX}/convert-odk-submission-json-to-geojson",
        files={
            "json_file": (
                "submissions.json",
                json.dumps(submission).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=submissions.geojson"
    )

    geojson = json.loads(response.content)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    feature = geojson["features"][0]
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["status"] == "complete"


async def test_convert_odk_submission_json_to_geojson_invalid_extension(client):
    """A non-JSON file extension should be rejected."""
    response = await client.post(
        f"{HELPERS_PREFIX}/convert-odk-submission-json-to-geojson",
        files={"json_file": ("submissions.csv", b"a,b,c", "text/csv")},
    )

    assert response.status_code == 400
    assert "valid .json" in response.text


async def test_convert_odk_submission_json_to_geojson_empty(client):
    """An empty submission list should return 422 (no submissions yet)."""
    response = await client.post(
        f"{HELPERS_PREFIX}/convert-odk-submission-json-to-geojson",
        files={
            "json_file": ("submissions.json", b"[]", "application/json"),
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /view-raw-data-api-token
# ---------------------------------------------------------------------------


async def test_view_raw_data_api_token_redirects(client):
    """A successful raw-data-api login should redirect to the login URL."""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"login_url": "https://example.com/osm-login"}

    with patch(
        "app.helpers.helper_routes.requests.get", return_value=mock_response
    ) as mock_get:
        response = await client.get(
            f"{HELPERS_PREFIX}/view-raw-data-api-token",
            follow_redirects=False,
        )

    mock_get.assert_called_once()
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/osm-login"


async def test_view_raw_data_api_token_upstream_failure(client):
    """A failed raw-data-api login should return a 500 error."""
    mock_response = Mock()
    mock_response.ok = False

    with patch("app.helpers.helper_routes.requests.get", return_value=mock_response):
        response = await client.get(
            f"{HELPERS_PREFIX}/view-raw-data-api-token",
            follow_redirects=False,
        )

    assert response.status_code == 500
    assert "Could not login" in response.text


# ---------------------------------------------------------------------------
# POST /multipolygons-to-polygons
# ---------------------------------------------------------------------------


async def test_multipolygons_to_polygons_success(client):
    """MultiPolygon geometries should be flattened to individual Polygons."""
    response = await client.post(
        f"{HELPERS_PREFIX}/multipolygons-to-polygons",
        files={
            "geojson": (
                "aoi.geojson",
                json.dumps(_MULTIPOLYGON_FEATCOL).encode("utf-8"),
                "application/geo+json",
            )
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=flattened_polygons.geojson"
    )

    featcol = json.loads(response.content)
    assert featcol["type"] == "FeatureCollection"
    assert len(featcol["features"]) >= 1
    assert all(
        feature["geometry"]["type"] == "Polygon" for feature in featcol["features"]
    )


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
