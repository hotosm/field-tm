# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Tests for project routes."""

import json
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
import requests
from fastapi import HTTPException
from geoalchemy2.elements import WKBElement
from loguru import logger as log
from shapely import Polygon

from app.central.central_crud import create_odk_project
from app.central.central_schemas import TaskStatus
from app.config import encrypt_value, settings
from app.db import db_models
from app.db.postgis_utils import check_crs
from app.projects import project_crud, project_schemas
from tests.test_data import test_data_path

odk_central_url = os.getenv("ODK_CENTRAL_URL")
odk_central_user = os.getenv("ODK_CENTRAL_USER")
odk_central_password = encrypt_value(os.getenv("ODK_CENTRAL_PASSWD", ""))


def create_project(client, organisation_id, project_data):
    """Create a new project."""
    response = client.post(
        f"/projects/create-project?org_id={organisation_id}", json=project_data
    )
    assert response.status_code == 200
    return response.json()


def test_create_project(client, organisation, project_data):
    """Test project creation endpoint."""
    response_data = create_project(client, organisation.id, project_data)
    project_name = project_data["project_info"]["name"]
    assert "id" in response_data

    # Duplicate response to test error condition: project name already exists
    response_duplicate = client.post(
        f"/projects/create-project?org_id={organisation.id}", json=project_data
    )
    assert response_duplicate.status_code == 400
    assert (
        response_duplicate.json()["detail"]
        == f"Project already exists with the name {project_name}"
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
    ],
)
def test_valid_geojson_types(client, organisation, project_data, geojson_type):
    """Test valid geojson types."""
    project_data["outline_geojson"] = geojson_type
    response_data = create_project(client, organisation.id, project_data)
    assert "id" in response_data


@pytest.mark.parametrize(
    "geojson_type",
    [
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
def test_invalid_geojson_types(client, organisation, project_data, geojson_type):
    """Test invalid geojson types."""
    project_data["outline_geojson"] = geojson_type
    response = client.post(
        f"/projects/create-project?org_id={organisation.id}", json=project_data
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "crs",
    [
        {"type": "name", "properties": {"name": "GGRS87"}},
        {"type": "name", "properties": {"name": "NAD83"}},
        {"type": "name", "properties": {"name": "NAD27"}},
    ],
)
async def test_unsupported_crs(project_data, crs):
    """Test unsupported CRS in GeoJSON."""
    project_data["outline_geojson"]["crs"] = crs
    with pytest.raises(HTTPException) as exc_info:
        await check_crs(project_data["outline_geojson"])
    assert exc_info.value.status_code == 400


@pytest.mark.parametrize(
    "hashtag_input, expected_output",
    [
        ("tag1, tag2, tag3", ["#tag1", "#tag2", "#tag3", "#FMTM"]),
        ("tag1   tag2    tag3", ["#tag1", "#tag2", "#tag3", "#FMTM"]),
        ("tag1, tag2 tag3    tag4", ["#tag1", "#tag2", "#tag3", "#tag4", "#FMTM"]),
        ("TAG1, tag2 #TAG3", ["#TAG1", "#tag2", "#TAG3", "#FMTM"]),
    ],
)
def test_hashtags(client, organisation, project_data, hashtag_input, expected_output):
    """Test hashtag parsing."""
    project_data["hashtags"] = hashtag_input
    response_data = create_project(client, organisation.id, project_data)
    project_id = response_data["id"]
    assert "id" in response_data
    assert response_data["hashtags"][:-1] == expected_output
    assert response_data["hashtags"][-1] == f"#{settings.FMTM_DOMAIN}-{project_id}"


async def test_delete_project(client, admin_user, project):
    """Test deleting a FMTM project, plus ODK Central project."""
    response = client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


async def test_create_odk_project():
    """Test creating an odk central project."""
    mock_project = Mock()
    mock_project.createProject.return_value = {"status": "success"}

    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_credentials = project_schemas.ODKCentralDecrypted(**odk_credentials)

    with patch("app.central.central_crud.get_odk_project", return_value=mock_project):
        result = create_odk_project("Test Project", odk_credentials)

    assert result == {"status": "success"}
    # FMTM gets appended to project name by default
    mock_project.createProject.assert_called_once_with("FMTM Test Project")


async def test_convert_to_app_project():
    """Test conversion to app project."""
    polygon = Polygon(
        [
            (85.317028828, 27.7052522097),
            (85.317028828, 27.7041424888),
            (85.318844411, 27.7041424888),
            (85.318844411, 27.7052522097),
            (85.317028828, 27.7052522097),
        ]
    )

    # Get the WKB representation of the Polygon
    wkb_outline = WKBElement(polygon.wkb, srid=4326)
    mock_db_project = db_models.DbProject(
        id=1,
        outline=wkb_outline,
    )

    result = await project_crud.convert_to_app_project(mock_db_project)

    assert result is not None
    assert isinstance(result, db_models.DbProject)

    assert result.outline_geojson is not None

    assert result.tasks is not None
    assert isinstance(result.tasks, list)


async def test_create_project_with_project_info(db, project):
    """Test creating a project with all project info."""
    assert isinstance(project.id, int)
    assert isinstance(project.project_name_prefix, str)


async def test_upload_data_extracts(client, project):
    """Test uploading data extracts in GeoJSON and flatgeobuf formats."""
    # Flatgeobuf
    fgb_file = {
        "custom_extract_file": (
            "file.fgb",
            open(f"{test_data_path}/data_extract_kathmandu.fgb", "rb"),
        )
    }
    response = client.post(
        f"/projects/upload-custom-extract/?project_id={project.id}",
        files=fgb_file,
    )

    assert response.status_code == 200

    response = client.get(
        f"/projects/data-extract-url/?project_id={project.id}",
    )
    assert "url" in response.json()

    # Geojson
    geojson_file = {
        "custom_extract_file": (
            "file.geojson",
            open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb"),
        )
    }
    response = client.post(
        f"/projects/upload-custom-extract/?project_id={project.id}",
        files=geojson_file,
    )

    assert response.status_code == 200

    response = client.get(
        f"/projects/data-extract-url/?project_id={project.id}",
    )
    assert "url" in response.json()

    # TODO add extra handling for custom extras not in specific format
    # TODO replace properties
    # TODO fix loading extracts without standard structure
    # data_extracts_file = f"{test_data_path}/building_footprint.zip"
    # with zipfile.ZipFile(data_extracts_file, "r") as zip_archive:
    #     data_extracts = zip_archive.read("building_foot_jnk.geojson")


async def test_generate_project_files(db, client, project):
    """Test generate all appuser files (during creation)."""
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_credentials = project_schemas.ODKCentralDecrypted(**odk_credentials)

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
    response = client.post(
        f"/projects/{project_id}/upload-task-boundaries",
        files=task_geojson_file,
    )
    assert response.status_code == 200

    # Upload data extracts
    with open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb") as f:
        data_extracts = json.dumps(json.load(f))
    log.debug(f"Uploading custom data extracts: {str(data_extracts)[:100]}...")
    data_extract_s3_path = await project_crud.upload_custom_geojson_extract(
        db,
        project_id,
        data_extracts,
    )
    assert data_extract_s3_path is not None
    # Test url, but first sub localhost url with docker network for backend connection
    internal_file_path = (
        f"{settings.S3_ENDPOINT}"
        f"{data_extract_s3_path.split(settings.FMTM_DEV_PORT)[1]}"
    )
    response = requests.head(internal_file_path, allow_redirects=True)
    assert response.status_code < 400

    # Get custom XLSForm path
    xlsform_file = Path(f"{test_data_path}/buildings.xls")
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    xform_file = {
        "xls_form_upload": (
            "buildings.xls",
            xlsform_obj,
        )
    }
    response = client.post(
        f"/projects/{project_id}/generate-project-data",
        files=xform_file,
    )
    assert response.status_code == 200


async def test_update_project(client, admin_user, project):
    """Test update project metadata."""
    updated_project_data = {
        "project_info": {
            "name": f"Updated Test Project {uuid4()}",
            "short_description": "updated short description",
            "description": "updated description",
        },
        "xform_category": "healthcare",
        "hashtags": "#FMTM anothertag",
        "outline_geojson": {
            "coordinates": [
                [
                    [85.317028828, 27.7052522097],
                    [85.317028828, 27.7041424888],
                    [85.318844411, 27.7041424888],
                    [85.318844411, 27.7052522097],
                    [85.317028828, 27.7052522097],
                ]
            ],
            "type": "Polygon",
        },
    }

    response = client.put(f"/projects/{project.id}", json=updated_project_data)

    if response.status_code != 200:
        log.error(response.json())
    assert response.status_code == 200

    response_data = response.json()
    # Assert that project_info in response_data matches updated_project_data
    assert (
        response_data["project_info"]["name"]
        == updated_project_data["project_info"]["name"]
    )
    assert (
        response_data["project_info"]["short_description"]
        == updated_project_data["project_info"]["short_description"]
    )
    assert (
        response_data["project_info"]["description"]
        == updated_project_data["project_info"]["description"]
    )

    assert response_data["xform_category"] == updated_project_data["xform_category"]
    assert response_data["hashtags"] == ["#FMTM", "#anothertag"]


async def test_project_summaries(client, project):
    """Test read project summaries."""
    response = client.get("/projects/summaries")
    assert response.status_code == 200
    assert "results" in response.json()

    results = response.json()["results"]
    result = results[0]

    assert result["id"] == project.id
    assert result["title"] == project.title
    assert result["description"] == project.description
    assert result["hashtags"] == project.hashtags
    assert result["organisation_id"] == project.organisation_id


async def test_project_by_id(client, project):
    """Test read project by id."""
    response = client.get(f"projects/{project.id}")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project.id
    assert data["odkid"] == project.odkid
    assert data["author"]["username"] == project.author.username
    assert data["author"]["id"] == project.author.id
    assert data["project_info"]["name"] == project.project_info.name
    assert (
        data["project_info"]["short_description"]
        == project.project_info.short_description
    )
    assert data["project_info"]["description"] == project.project_info.description
    assert (
        data["project_info"]["per_task_instructions"]
        == project.project_info.per_task_instructions
    )
    assert data["status"] == project.status
    assert data["xform_category"] == project.xform_category
    assert data["hashtags"] == project.hashtags
    assert data["organisation_id"] == project.organisation_id
    assert data["tasks"] == project.tasks


async def test_set_entity_mapping_status(client, odk_project, entities):
    """Test set the ODK entity mapping status."""
    entity = entities[0]
    expected_status = TaskStatus.LOCKED_FOR_MAPPING

    response = client.post(
        f"/projects/{odk_project.id}/entity/status",
        json={
            "entity_id": entity["id"],
            "status": expected_status,
            "label": f"Task {entity['task_id']} Feature {entity['osm_id']}",
        },
    )
    response_entity = response.json()

    expected_entity = entity
    expected_entity["status"] = expected_status.value
    assert response.status_code == 200
    compare_entities(response_entity, expected_entity)


async def test_get_entity_mapping_status(client, odk_project, entities):
    """Test get the ODK entity mapping status."""
    entity = entities[0]
    response = client.get(
        f"/projects/{odk_project.id}/entity/status", params={"entity_id": entity["id"]}
    )
    response_entity = response.json()

    assert response.status_code == 200
    compare_entities(response_entity, entity)


async def test_get_entities_mapping_statuses(client, odk_project, entities):
    """Test get the ODK entities mapping statuses."""
    odk_project_id = odk_project.id
    response = client.get(f"projects/{odk_project_id}/entities/statuses")
    response_entities = response.json()

    assert len(response_entities) == len(entities)
    for response_entity, expected_entity in zip(
        response_entities, entities, strict=False
    ):
        compare_entities(expected_entity, response_entity)


def compare_entities(response_entity, expected_entity):
    """Utility function for testing by comparing response and expected entity fields."""
    assert response_entity["id"] == str(expected_entity["id"])
    assert str(response_entity["task_id"]) == str(expected_entity["task_id"])
    assert str(response_entity["osm_id"]) == str(expected_entity["osm_id"])
    assert str(response_entity["status"]) == str(expected_entity["status"])


def test_project_task_split(client):
    """Test project task split."""
    with open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb") as project_file:
        project_geojson = project_file.read()

    response = client.post(
        "/projects/task-split",
        files={"project_geojson": ("data_extract_kathmandu.geojson", project_geojson)},
        data={"no_of_buildings": 40},
    )

    assert response.status_code == 200
    assert response.json() is not None
    assert "features" in response.json()

    # Test without required value should cause validation error
    response = client.post("/projects/task-split")
    assert response.status_code == 422


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
