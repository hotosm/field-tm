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
"""Configuration and fixtures for PyTest."""

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
import requests
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from loguru import logger as log
from psycopg import AsyncConnection

from app.auth.auth_routes import get_or_create_user
from app.auth.auth_schemas import AuthUser, FMTMUser
from app.central import central_crud, central_schemas
from app.central.central_schemas import ODKCentralDecrypted, ODKCentralIn
from app.config import encrypt_value, settings
from app.db.database import db_conn
from app.db.enums import TaskStatus, UserRole, get_action_for_status_change
from app.db.models import DbProject, DbTask, DbTaskHistory
from app.main import get_application
from app.organisations.organisation_deps import get_organisation
from app.projects import project_crud
from app.projects.project_schemas import ProjectIn
from app.tasks.task_schemas import TaskHistoryIn
from app.users.user_deps import get_user
from tests.test_data import test_data_path

odk_central_url = os.getenv("ODK_CENTRAL_URL")
odk_central_user = os.getenv("ODK_CENTRAL_USER")
odk_central_password = encrypt_value(os.getenv("ODK_CENTRAL_PASSWD", ""))


def pytest_configure(config):
    """Configure pytest runs."""
    # Example of stopping sqlalchemy logs
    # sqlalchemy_log = logging.getLogger("sqlalchemy")
    # sqlalchemy_log.propagate = False


@pytest_asyncio.fixture(autouse=True)
async def app() -> AsyncGenerator[FastAPI, Any]:
    """Get the FastAPI test server."""
    yield get_application()


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncConnection:
    """The psycopg async database connection using psycopg3."""
    db_conn = await AsyncConnection.connect(
        settings.FMTM_DB_URL.unicode_string(),
    )
    try:
        yield db_conn
    finally:
        await db_conn.close()


@pytest_asyncio.fixture(scope="function")
async def admin_user(db):
    """A test user."""
    db_user = await get_or_create_user(
        db,
        AuthUser(
            sub="fmtm|1",
            username="localadmin",
            role=UserRole.ADMIN,
        ),
    )

    return FMTMUser(
        id=db_user.id,
        username=db_user.username,
        role=UserRole[db_user.role],
        profile_img=db_user.profile_img,
    )


@pytest_asyncio.fixture(scope="function")
async def organisation(db):
    """A test organisation."""
    return await get_organisation(db, "HOTOSM")


@pytest_asyncio.fixture(scope="function")
async def project(db, admin_user, organisation):
    """A test project, using the test user and org."""
    odk_creds_encrypted = ODKCentralIn(
        odk_central_url=os.getenv("ODK_CENTRAL_URL"),
        odk_central_user=os.getenv("ODK_CENTRAL_USER"),
        odk_central_password=os.getenv("ODK_CENTRAL_PASSWD"),
    )
    odk_creds_decrypted = ODKCentralDecrypted(
        odk_central_url=odk_creds_encrypted.odk_central_url,
        odk_central_user=odk_creds_encrypted.odk_central_user,
        odk_central_password=odk_creds_encrypted.odk_central_password,
    )

    project_name = f"test project {uuid4()}"
    # Create ODK Central Project
    try:
        odkproject = central_crud.create_odk_project(
            project_name,
            odk_creds_decrypted,
        )
        log.debug(f"ODK project returned: {odkproject}")
        assert odkproject is not None
        assert odkproject.get("id") is not None
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    project_metadata = ProjectIn(
        name=project_name,
        short_description="test",
        description="test",
        xform_category="buildings",
        odk_central_url=os.getenv("ODK_CENTRAL_URL"),
        odk_central_user=os.getenv("ODK_CENTRAL_USER"),
        odk_central_password=os.getenv("ODK_CENTRAL_PASSWD"),
        hashtags="hashtag1 hashtag2",
        outline={
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
        author_id=admin_user.id,
        organisation_id=organisation.id,
        odkid=odkproject.get("id"),
    )

    # Create FMTM Project
    try:
        new_project = await DbProject.create(db, project_metadata)
        log.debug(f"Project returned: {new_project}")
        assert new_project is not None
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    # Get project, including all calculated fields
    project_all_data = await DbProject.one(db, new_project.id)
    assert isinstance(project_all_data.organisation_logo, str)
    assert isinstance(project_all_data.bbox, list)
    assert isinstance(project_all_data.bbox[0], float)
    return project_all_data


@pytest_asyncio.fixture(scope="function")
async def tasks(project, db):
    """Test tasks, using the test project."""
    boundaries = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.3012091, 27.7122369],
                            [85.3012129, 27.7121403],
                            [85.3013408, 27.7121442],
                            [85.3013371, 27.7122408],
                            [85.3012441, 27.712238],
                            [85.3012091, 27.7122369],
                        ]
                    ],
                },
                "properties": {
                    "osm_id": 650958368,
                    "version": 2,
                    "tags": {"building": "yes"},
                    "changeset": 99124278,
                    "timestamp": "2021-02-11T17:21:06",
                },
            }
        ],
    }

    try:
        success = await DbTask.create(db, project.id, boundaries)
        assert success
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    return await DbTask.all(db, project.id)


@pytest_asyncio.fixture(scope="function")
async def task_event(db, project, tasks, admin_user):
    """Create a new task event in the database."""
    user = await get_user(admin_user.id, db)
    for task in tasks:
        new_event = TaskHistoryIn(
            task_id=task.id,
            user_id=user.id,
            action=get_action_for_status_change(TaskStatus.READY),
            action_text="We added a comment!",
        )
        db_task_event = await DbTaskHistory.create(db, new_event)
    return db_task_event


@pytest_asyncio.fixture(scope="function")
async def odk_project(db, client, project, tasks):
    """Create ODK Central resources for a project and generate the necessary files."""
    with open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb") as f:
        data_extracts = json.dumps(json.load(f))
    log.debug(f"Uploading custom data extracts: {str(data_extracts)[:100]}...")
    data_extract_s3_path = await project_crud.upload_custom_geojson_extract(
        db,
        project.id,
        data_extracts,
    )

    internal_file_path = (
        f"{settings.S3_ENDPOINT}"
        f"{data_extract_s3_path.split(settings.FMTM_DEV_PORT)[1]}"
    )
    response = requests.head(internal_file_path, allow_redirects=True)
    assert response.status_code < 400

    xlsform_file = Path(f"{test_data_path}/buildings.xls")
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    xform_file = {
        "xls_form_upload": (
            "buildings.xls",
            xlsform_obj,
        )
    }
    try:
        response = await client.post(
            f"/projects/{project.id}/generate-project-data",
            files=xform_file,
        )
        log.debug(f"Generated project files for project: {project.id}")
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    yield project


@pytest_asyncio.fixture(scope="function")
async def entities(odk_project):
    """Get entities data."""
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_credentials = ODKCentralDecrypted(**odk_credentials)

    entities = await central_crud.get_entities_data(
        odk_credentials,
        odk_project.odkid,
    )
    yield entities


@pytest_asyncio.fixture(scope="function")
async def project_data():
    """Sample data for creating a project."""
    project_name = f"Test Project {uuid4()}"
    data = {
        "name": project_name,
        "short_description": "test",
        "description": "test",
        "xform_category": "buildings",
        "hashtags": "testtag",
        "outline": {
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

    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_creds_decrypted = central_schemas.ODKCentralDecrypted(**odk_credentials)
    data.update(**odk_creds_decrypted.model_dump())

    return data


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI, db: AsyncConnection):
    """The FastAPI test server."""
    # Override server db connection to use same as in conftest
    # NOTE this is marginally slower, but required else tests fail
    app.dependency_overrides[db_conn] = lambda: db

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url=f"http://{settings.FMTM_DOMAIN}",
            follow_redirects=True,
        ) as ac:
            yield ac
