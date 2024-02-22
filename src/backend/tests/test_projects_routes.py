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

import functools
import json
import os
import uuid
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
import requests
from fastapi.concurrency import run_in_threadpool
from geoalchemy2.elements import WKBElement
from loguru import logger as log
from shapely import Polygon

from app.central.central_crud import create_odk_project
from app.config import encrypt_value, settings
from app.db import db_models
from app.db.postgis_utils import split_geojson_by_task_areas
from app.projects import project_crud, project_schemas
from app.tasks import tasks_crud
from tests.test_data import test_data_path

odk_central_url = os.getenv("ODK_CENTRAL_URL")
odk_central_user = os.getenv("ODK_CENTRAL_USER")
odk_central_password = encrypt_value(os.getenv("ODK_CENTRAL_PASSWD", ""))


async def test_create_project(client, admin_user, organisation):
    """Test project creation endpoint."""
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_credentials = project_schemas.ODKCentralDecrypted(**odk_credentials)

    project_data = {
        "project_info": {
            "name": "test project",
            "short_description": "test",
            "description": "test",
        },
        "xform_title": "buildings",
        "hashtags": ["#FMTM"],
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
    project_data.update(**odk_credentials.model_dump())

    response = client.post(
        f"/projects/create_project?org_id={organisation.id}", json=project_data
    )

    assert response.status_code == 200

    response_data = response.json()
    assert "id" in response_data


async def test_delete_project(client, admin_user, project):
    """Test deleting a FMTM project, plus ODK Central project."""
    log.warning(project)
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
    mock_project.createProject.assert_called_once_with("Test Project")


async def test_convert_to_app_project():
    """Test conversion ot app project."""
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

    assert result.project_tasks is not None
    assert isinstance(result.project_tasks, list)


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

    # Extract data extract from flatgeobuf
    feature_collection = await project_crud.get_project_features_geojson(db, project)
    # Split extract by task area
    split_extract_dict = await split_geojson_by_task_areas(
        db, feature_collection, project_id
    )
    assert split_extract_dict is not None

    # Get project tasks list (no longer required)
    task_ids = await tasks_crud.get_task_id_list(db, project_id)
    assert isinstance(task_ids, list)

    # Provide custom xlsform file path
    xlsform_file = f"{test_data_path}/buildings.xls"
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    for task_id in split_extract_dict.keys():
        # NOTE avoid the lambda function for run_in_threadpool
        # functools.partial captures the loop variable task_id in a
        # way that is safe for use within asynchronous code
        success = await run_in_threadpool(
            functools.partial(
                project_crud.generate_task_files,
                db,
                project_id,
                task_id,
                split_extract_dict[task_id],
                xlsform_file,
                "building",
                odk_credentials,
            )
        )
        assert success

    # Generate appuser files
    result = await run_in_threadpool(
        lambda: project_crud.generate_project_files(
            db,
            project_id,
            custom_form=xlsform_obj,
            form_category="buildings",
            form_format="example_form_type",
            background_task_id=uuid.uuid4(),
        )
    )

    assert result is None


# async def test_update_project_boundary(db, project):
#     """Test updating project boundary."""
#     project_id = project.id
#     log.debug(f"Testing updating boundary for project ID: {project_id}")

#     db_project = await project_crud.get_project_by_id(db, project_id)

#     # Outline
#     boundary_geojson = json.loads(
#         json.dumps(
#             {
#                 "type": "Polygon",
#                 "coordinates": [
#                     [
#                         [85.317028828, 27.7052522097],
#                         [85.317028828, 27.7041424888],
#                         [85.318844411, 27.7041424888],
#                         [85.318844411, 27.7052522097],
#                         [85.317028828, 27.7052522097],
#                     ]
#                 ],
#             }
#         )
#     )
#     log.debug(f"Creating project boundary: {boundary_geojson}")
#     boundary_created = await project_crud.update_project_boundary(
#         db, project_id, boundary_geojson, 500
#     )
#     assert boundary_created is True
#     project_outline = db_project.outline.data.tobytes()
#     file_outline = shape(boundary_geojson)
#     assert wkb.loads(project_outline).wkt == file_outline.wkt

#     # Centroid
#     project_centroid = wkb.loads(db_project.centroid.data.tobytes()).wkt
#     file_centroid = file_outline.centroid.wkt
#     assert project_centroid == file_centroid

#     # Location string
#     assert db_project.location_str == "Zurich,Switzerland"


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
