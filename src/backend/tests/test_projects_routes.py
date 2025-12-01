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
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from loguru import logger as log

from app.central.central_crud import create_odk_project
from app.config import settings
from app.db.enums import EntityState, HTTPStatus, MappingState
from app.db.models import DbProject, slugify
from app.db.postgis_utils import check_crs
from app.projects import project_crud
from tests.test_data import test_data_path


async def create_stub_project(client, organisation_id, stub_project_data):
    """Create a new project."""
    response = await client.post(
        f"/projects/stub?org_id={organisation_id}", json=stub_project_data
    )
    assert response.status_code == HTTPStatus.OK
    return response.json()


async def test_create_project_invalid(client, organisation, project_data):
    """Test project creation endpoint, duplicate checker."""
    project_data["task_split_type"] = "invalid"
    project_data["priority"] = "invalid"
    response_invalid = await client.patch(
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


async def test_create_project_with_dup(client, organisation, stub_project_data):
    """Test project creation endpoint, duplicate checker."""
    project_name = stub_project_data["name"]

    new_project = await create_stub_project(client, organisation.id, stub_project_data)
    assert "id" in new_project
    assert isinstance(new_project["id"], int)
    assert isinstance(new_project["slug"], str)
    assert new_project["slug"] == slugify(project_name)
    assert new_project["location_str"] == "Kathmandu,Nepal"

    # Duplicate response to test error condition: project name already exists
    response_duplicate = await client.post(
        f"/projects/stub?org_id={organisation.id}", json=stub_project_data
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
async def test_valid_geojson_types(client, organisation, project_data, geojson_type):
    """Test valid geojson types."""
    project_data["outline"] = geojson_type
    response_data = await create_project(client, organisation.id, project_data)
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
async def test_invalid_geojson_types(client, organisation, project_data, geojson_type):
    """Test invalid geojson types."""
    project_data["outline"] = geojson_type
    response = await client.patch(
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
async def test_unsupported_crs(stub_project_data, crs):
    """Test unsupported CRS in GeoJSON."""
    stub_project_data["outline"]["crs"] = crs
    with pytest.raises(HTTPException) as exc_info:
        await check_crs(stub_project_data["outline"])
    assert exc_info.value.status_code == 400


async def create_project(client, organisation_id, stub_project_data):
    """Create a new project."""
    response = await client.post(
        f"/projects/stub?org_id={organisation_id}", json=stub_project_data
    )
    assert response.status_code == HTTPStatus.OK
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
    organisation,
    project_data,
    stub_project_data,
    hashtag_input,
    expected_output,
):
    """Test hashtag parsing."""
    project_data["hashtags"] = hashtag_input
    response_data = await create_stub_project(
        client, organisation.id, stub_project_data
    )
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
    # Field-TM gets appended to project name by default
    mock_project.createProject.assert_called_once_with("Field-TM Test Project")


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
    assert response.status_code == 200

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
    assert new_project.tasks and len(new_project.tasks) == 1
    assert new_project.tasks[0].task_state == MappingState.UNLOCKED_TO_MAP
    assert isinstance(new_project.odk_token, str)


async def test_update_project(client, admin_user, project):
    """Test update project metadata."""
    updated_project_data = {
        "name": f"Updated Test Project {uuid4()}",
        "short_description": "updated short description",
        "description": "updated description",
        "osm_category": "healthcare",
        "hashtags": "#Field-TM anothertag",
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

    assert response_data["osm_category"] == updated_project_data["osm_category"]
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
    assert data["author_sub"] == project.author_sub
    assert data["name"] == project.name
    assert data["short_description"] == project.short_description
    assert data["description"] == project.description
    assert data["per_task_instructions"] == project.per_task_instructions
    assert data["status"] == project.status
    assert data["osm_category"] == project.osm_category
    assert data["hashtags"] == project.hashtags
    assert data["organisation_id"] == project.organisation_id
    assert data["location_str"] == project.location_str
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
            "label": f"Feature {entity['osm_id']}",
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


async def test_read_project(client, project):
    """Test read project by id."""
    response = await client.get(f"projects/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["odkid"] == project.odkid
    assert data["name"] == project.name
    assert data["bbox"] == project.bbox
    assert data["organisation_logo"] == project.organisation_logo

    # Test with minimal param
    response = await client.get(f"/projects/{project.id}/minimal")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["odkid"] == project.odkid
    assert data["name"] == project.name
    assert data["bbox"] is None
    assert data["organisation_logo"] is None


async def test_update_and_download_project_form(client, project):
    """Test updating and downloading the XLSForm for a project."""
    updated_xls_content = b"updated xlsform data"
    xls_file = BytesIO(updated_xls_content)
    xls_file.name = "form.xlsx"

    with (
        patch("app.central.central_deps.read_xlsform", return_value=xls_file),
        patch("app.central.central_crud.update_odk_central_xform", return_value=None),
        patch(
            "app.central.central_crud.get_project_form_xml",
            return_value="<fake-xml></fake-xml>",
        ),
    ):
        response = await client.post(
            f"central/update-form?project_id={project.id}",
            data={"xform_id": "test-xform-id"},
            files={
                "xlsform": (
                    "form.xlsx",
                    updated_xls_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert response.status_code == 200
        assert (
            response.json()["message"]
            == f"Successfully updated the form for project {project.id}"
        )

        # Test downloading the updated XLSForm
        response = await client.get(f"central/download-form?project_id={project.id}")

        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == f"attachment; filename={project.id}_xlsform.xlsx"
        )
        assert response.headers["Content-Type"] == "application/media"
        assert response.content is not None
        assert response.content == b"updated xlsform data"


# NOTE we need odk_project and task_events fixture to populate data
# NOTE we need odk_project and task_events fixture to populate data
async def test_get_contributors(client, project, odk_project, submission, admin_user):
    """Test fetching contributors of a project."""
    response = await client.get(f"projects/contributors/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(
        "user" in contributor and "submissions" in contributor for contributor in data
    )

    contributor = data[0]
    assert contributor["user"] == admin_user.username
    assert contributor["submissions"] == 1


async def test_add_new_project_manager(client, project, new_mapper_user):
    """Test adding a new project manager."""
    with patch(
        "app.projects.project_crud.send_project_manager_message", return_value=None
    ):
        response = await client.post(
            "projects/add-manager",
            params={"project_id": project.id, "sub": new_mapper_user.sub},
        )

    assert response.status_code == 200

    # Verify manager was added by fetching project users
    response = await client.get(f"/projects/{project.id}/users")
    assert response.status_code == 200

    data = response.json()

    # Ensure the new manager is in the response
    assert any(
        user["user_sub"] == new_mapper_user.sub and user["role"] == "PROJECT_MANAGER"
        for user in data
    )


async def test_create_entity(client, db, project, odk_project, tasks):
    """Test creating an entity and verifying task_id matching within task boundary."""
    # NOTE here we need odk_project fixture to ensure the project exists

    # Sample GeoJSON with a point that would lie inside a task boundary
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"project_id": project.id},
                "geometry": {"type": "Point", "coordinates": [85.30125, 27.7122]},
            }
        ],
    }
    project_task_index_list = [task.project_task_index for task in tasks]

    entity_uuid = uuid4()
    response = await client.post(
        f"central/entity?project_id={project.id}&entity_uuid={entity_uuid}",
        json=geojson,
    )
    assert response.status_code == 200
    data = response.json()

    # Check if the task_id in the returned data matches the task_id within the boundary
    assert int(data["currentVersion"]["data"]["task_id"]) in project_task_index_list


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


async def test_download_task_boundaries(client, project, tasks):
    """Test downloading task boundaries as GeoJSON."""
    response = await client.get(f"/projects/{project.id}/download_tasks")

    assert response.status_code == 200
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=task_boundary.geojson"
    )
    assert response.headers["Content-Type"] == "application/media"

    content = json.loads(response.content)

    assert content["type"] == "FeatureCollection"
    assert "features" in content
    assert isinstance(content["features"], list)
    assert len(content["features"]) == len(tasks)

    project_task_index_list = [task.project_task_index for task in tasks]
    for feature in content["features"]:
        assert "geometry" in feature
        assert "properties" in feature
        assert "task_id" in feature["properties"]
        assert feature["properties"]["task_id"] in project_task_index_list


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
