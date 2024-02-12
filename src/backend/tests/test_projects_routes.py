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
import sozipfile.sozipfile as zipfile
from fastapi.concurrency import run_in_threadpool
from geoalchemy2.elements import WKBElement
from loguru import logger as log
from shapely import Polygon, wkb
from shapely.geometry import shape

from app.central.central_crud import create_odk_project
from app.config import encrypt_value, settings
from app.db import db_models
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
    }
    project_data.update(**odk_credentials.model_dump())

    response = client.post(
        f"/projects/create_project?org_id={organisation.id}", json=project_data
    )

    assert response.status_code == 200

    response_data = response.json()
    assert "id" in response_data


async def test_delete_project(client, project):
    """Test deleting a FMTM project, plus ODK Central project."""
    response = client.delete(f"/projects/{project.id}")
    assert response.status_code == 204


async def test_create_odk_project():
    """Test creating an odk central project."""
    mock_project = Mock()
    mock_project.createProject.return_value = {"status": "success"}

    with patch("app.central.central_crud.get_odk_project", return_value=mock_project):
        result = create_odk_project("Test Project")

    assert result == {"status": "success"}
    mock_project.createProject.assert_called_once_with("Test Project")


async def test_convert_to_app_project():
    """Test conversion ot app project."""
    polygon = Polygon(
        [
            (85.924707758, 26.727727503),
            (85.922703741, 26.732440043),
            (85.928284549, 26.735158727),
            (85.930643709, 26.734365785),
            (85.932368686, 26.732372075),
            (85.924707758, 26.727727503),
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


async def test_generate_appuser_files(db, project):
    """Test generate all appuser files (during creation)."""
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_credentials = project_schemas.ODKCentralDecrypted(**odk_credentials)

    project_id = project.id
    log.debug(f"Testing project ID: {project_id}")

    # Set project boundary
    boundary_geojson = json.loads(
        json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [8.539551723844, 47.3765788922656],
                        [8.539551723844, 47.37303247378486],
                        [8.547135285454686, 47.37303247378486],
                        [8.547135285454686, 47.3765788922656],
                        [8.539551723844, 47.3765788922656],
                    ]
                ],
            }
        )
    )
    log.debug(f"Creating project boundary: {boundary_geojson}")
    boundary_created = await project_crud.update_project_boundary(
        db, project_id, boundary_geojson, 500
    )
    assert boundary_created is True
    # Check updated locations
    db_project = await project_crud.get_project_by_id(db, project_id)
    # Outline
    project_outline = db_project.outline.data.tobytes()
    file_outline = shape(boundary_geojson)
    assert wkb.loads(project_outline).wkt == file_outline.wkt
    # Centroid
    project_centroid = wkb.loads(db_project.centroid.data.tobytes()).wkt
    file_centroid = file_outline.centroid.wkt
    assert project_centroid == file_centroid
    # Location string
    assert db_project.location_str == "Zurich,Switzerland"

    # Load data extracts
    data_extracts_file = f"{test_data_path}/building_footprint.zip"
    with zipfile.ZipFile(data_extracts_file, "r") as zip_archive:
        data_extracts = zip_archive.read("building_foot_jnk.geojson")

    # Upload data extracts
    log.debug(f"Uploading custom data extracts: {str(data_extracts)[:100]}...")
    data_extract_s3_path = await project_crud.upload_custom_data_extract(
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

    # Get project tasks list
    task_ids = await tasks_crud.get_task_id_list(db, project_id)
    assert isinstance(task_ids, list)

    # Provide custom xlsform file path
    xlsform_file = f"{test_data_path}/buildings.xls"
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    for task_id in task_ids:
        # NOTE avoid the lambda function for run_in_threadpool
        # functools.partial captures the loop variable task_id in a
        # way that is safe for use within asynchronous code
        success = await run_in_threadpool(
            functools.partial(
                project_crud.generate_task_files,
                db,
                project_id,
                task_id,
                xlsform_file,
                "building",
                odk_credentials,
            )
        )
        assert success

    # Generate appuser files
    result = await run_in_threadpool(
        lambda: project_crud.generate_appuser_files(
            db,
            project_id,
            custom_form=xlsform_obj,
            form_category="buildings",
            form_format="example_form_type",
            background_task_id=uuid.uuid4(),
        )
    )

    assert result is None


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
