# Copyright (c) Humanitarian OpenStreetMap Team
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
from urllib.parse import urlparse
from uuid import uuid4

import pytest
import requests
from fastapi import HTTPException
from loguru import logger as log

from app.central.central_crud import create_odk_project
from app.config import settings
from app.db.enums import EntityState, HTTPStatus, MappingState
from app.db.models import DbProject, slugify
from app.db.postgis_utils import check_crs
from app.projects import project_crud
from tests.test_data import test_data_path


async def create_project(client, organisation_id, project_data):
    """Create a new project."""
    response = await client.post(
        f"/projects?org_id={organisation_id}", json=project_data
    )
    assert response.status_code == HTTPStatus.OK
    return response.json()


async def test_create_project_invalid(client, organisation, project_data):
    """Test project creation endpoint, duplicate checker."""
    project_data["task_split_type"] = "invalid"
    project_data["priority"] = "invalid"
    response_invalid = await client.post(
        f"/projects?org_id={organisation.id}", json=project_data
    )
    assert response_invalid.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    response_data = response_invalid.json()

    expected_errors = {
        "task_split_type": (
            "'DIVIDE_ON_SQUARE', 'CHOOSE_AREA_AS_TASK' or 'TASK_SPLITTING_ALGORITHM'"
        ),
        "priority": "'MEDIUM', 'LOW', 'HIGH' or 'URGENT'",
    }

    for error in response_data["detail"]:
        # Get the field name from the last element of the 'loc' list
        field_name = error["loc"][-1]
        if field_name in expected_errors:
            assert error["ctx"]["expected"] == expected_errors[field_name]


async def test_create_project_with_dup(client, organisation, project_data):
    """Test project creation endpoint, duplicate checker."""
    project_name = project_data["name"]

    new_project = await create_project(client, organisation.id, project_data)
    assert "id" in new_project
    assert isinstance(new_project["id"], int)
    assert isinstance(new_project["slug"], str)
    assert new_project["slug"] == slugify(project_name)

    # Duplicate response to test error condition: project name already exists
    response_duplicate = await client.post(
        f"/projects?org_id={organisation.id}", json=project_data
    )

    assert response_duplicate.status_code == HTTPStatus.CONFLICT
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
    ],
)
async def test_valid_geojson_types(client, organisation, project_data, geojson_type):
    """Test valid geojson types."""
    project_data["outline"] = geojson_type
    response_data = await create_project(client, organisation.id, project_data)
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
async def test_invalid_geojson_types(client, organisation, project_data, geojson_type):
    """Test invalid geojson types."""
    project_data["outline"] = geojson_type
    response = await client.post(
        f"/projects?org_id={organisation.id}", json=project_data
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
    project_data["outline"]["crs"] = crs
    with pytest.raises(HTTPException) as exc_info:
        await check_crs(project_data["outline"])
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
async def test_project_hashtags(
    client, organisation, project_data, hashtag_input, expected_output
):
    """Test hashtag parsing."""
    project_data["hashtags"] = hashtag_input
    response_data = await create_project(client, organisation.id, project_data)
    project_id = response_data["id"]
    assert "id" in response_data
    assert response_data["hashtags"][:-1] == expected_output
    assert response_data["hashtags"][-1] == f"#{settings.FMTM_DOMAIN}-{project_id}"


async def test_delete_project(client, admin_user, project):
    """Test deleting a FMTM project, plus ODK Central project."""
    response = await client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


async def test_create_odk_project():
    """Test creating an odk central project."""
    mock_project = Mock()
    mock_project.createProject.return_value = {"status": "success"}

    odk_credentials = {
        "odk_central_url": os.getenv("ODK_CENTRAL_URL"),
        "odk_central_user": os.getenv("ODK_CENTRAL_USER"),
        "odk_central_password": os.getenv("ODK_CENTRAL_PASSWD"),
    }

    with patch("app.central.central_crud.get_odk_project", return_value=mock_project):
        result = create_odk_project("Test Project", odk_credentials)

    assert result == {"status": "success"}
    # FMTM gets appended to project name by default
    mock_project.createProject.assert_called_once_with("FMTM Test Project")


async def test_upload_data_extracts(client, project):
    """Test uploading data extracts in GeoJSON and flatgeobuf formats."""
    # Flatgeobuf
    fgb_file = {
        "custom_extract_file": (
            "file.fgb",
            open(f"{test_data_path}/data_extract_kathmandu.fgb", "rb"),
        )
    }
    response = await client.post(
        f"/projects/upload-custom-extract?project_id={project.id}",
        files=fgb_file,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/projects/data-extract-url?project_id={project.id}",
    )
    assert "url" in response.json()

    # Geojson
    geojson_file = {
        "custom_extract_file": (
            "file.geojson",
            open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb"),
        )
    }
    response = await client.post(
        f"/projects/upload-custom-extract?project_id={project.id}",
        files=geojson_file,
    )

    assert response.status_code == 200

    response = await client.get(
        f"/projects/data-extract-url?project_id={project.id}",
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
    internal_s3_url = f"{settings.S3_ENDPOINT}{urlparse(data_extract_s3_path).path}"
    response = requests.head(internal_s3_url, allow_redirects=True)
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
    response = await client.post(
        f"/projects/{project_id}/generate-project-data",
        files=xform_file,
    )
    assert response.status_code == 200

    # Now check required values were added to project
    new_project = await DbProject.one(db, project_id)
    assert len(new_project.tasks) == 1
    assert new_project.tasks[0].task_state == MappingState.UNLOCKED_TO_MAP
    assert isinstance(new_project.odk_token, str)


async def test_update_project(client, admin_user, project):
    """Test update project metadata."""
    updated_project_data = {
        "name": f"Updated Test Project {uuid4()}",
        "short_description": "updated short description",
        "description": "updated description",
        "xform_category": "healthcare",
        "hashtags": "#FMTM anothertag",
    }

    response = await client.patch(f"/projects/{project.id}", json=updated_project_data)

    if response.status_code != 200:
        log.error(response.json())
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["name"] == updated_project_data["name"]
    assert (
        response_data["short_description"] == updated_project_data["short_description"]
    )
    assert response_data["description"] == updated_project_data["description"]

    assert response_data["xform_category"] == updated_project_data["xform_category"]
    assert sorted(response_data["hashtags"]) == sorted(
        [
            "#FMTM",
            f"#{settings.FMTM_DOMAIN}-{response_data["id"]}",
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
    assert first_project["name"] == project.name
    assert first_project["short_description"] == project.short_description
    assert first_project["hashtags"] == project.hashtags
    assert first_project["organisation_id"] == project.organisation_id


async def test_project_by_id(client, project):
    """Test read project by id."""
    response = await client.get(f"projects/{project.id}?project_id={project.id}")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project.id
    assert data["odkid"] == project.odkid
    assert data["author_id"] == project.author_id
    assert data["name"] == project.name
    assert data["short_description"] == project.short_description
    assert data["description"] == project.description
    assert data["per_task_instructions"] == project.per_task_instructions
    assert data["status"] == project.status
    assert data["xform_category"] == project.xform_category
    assert data["hashtags"] == project.hashtags
    assert data["organisation_id"] == project.organisation_id
    assert data["tasks"] == []


async def test_set_entity_mapping_status(client, odk_project, entities):
    """Test set the ODK entity mapping status."""
    entity = entities[0]
    new_status = EntityState.OPENED_IN_ODK

    response = await client.post(
        f"/projects/{odk_project.id}/entity/status",
        json={
            "entity_id": entity["id"],
            "status": new_status,
            "label": f"Task {entity['task_id']} Feature {entity['osm_id']}",
        },
    )
    response_entity = response.json()

    # Here we update the original entity status for the comparison
    entity["status"] = new_status.value
    assert response.status_code == 200
    compare_entities(response_entity, entity)


async def test_get_entity_mapping_status(client, odk_project, entities):
    """Test get the ODK entity mapping status."""
    entity = entities[0]
    response = await client.get(
        f"/projects/{odk_project.id}/entity/status", params={"entity_id": entity["id"]}
    )
    response_entity = response.json()

    assert response.status_code == 200
    compare_entities(response_entity, entity)


async def test_get_entities_mapping_statuses(client, odk_project, entities):
    """Test get the ODK entities mapping statuses."""
    odk_project_id = odk_project.id
    response = await client.get(f"projects/{odk_project_id}/entities/statuses")
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


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
