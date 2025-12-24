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
"""Configuration and fixtures for PyTest."""

import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncGenerator
from urllib.parse import urlparse
from uuid import uuid4

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from litestar import Litestar
from psycopg import AsyncConnection

from app.auth.auth_schemas import AuthUser, FMTMUser
from app.central import central_crud, central_schemas
from app.central.central_schemas import ODKCentralDecrypted, ODKCentralIn
from app.config import encrypt_value, settings
from app.db.enums import (
    FieldMappingApp,
)
from app.db.models import (
    DbProject,
)
from app.main import api as litestar_api
from app.projects import project_crud
from app.projects.project_schemas import (
    ProjectIn,
    StubProjectIn,
)
from app.users.user_crud import get_or_create_user
from tests.test_data import test_data_path

log = logging.getLogger(__name__)

odk_central_url = os.getenv("ODK_CENTRAL_URL")
odk_central_user = os.getenv("ODK_CENTRAL_USER")
odk_central_password = encrypt_value(os.getenv("ODK_CENTRAL_PASSWD", ""))


def pytest_configure(config):
    """Configure pytest runs."""
    # Example of stopping sqlalchemy logs
    # sqlalchemy_log = logging.getLogger("sqlalchemy")
    # sqlalchemy_log.propagate = False


@pytest_asyncio.fixture(autouse=True)
async def app() -> AsyncGenerator[Litestar, Any]:
    """Get the Litestar test server."""
    # Create a fresh Litestar app instance for each test session using the
    # configured application factory.
    yield litestar_api


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncConnection:
    """The psycopg async database connection using psycopg3."""
    db_conn = await AsyncConnection.connect(
        settings.FMTM_DB_URL,
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
            sub="osm|1",
            username="localadmin",
            is_admin=True,
        ),
    )

    return FMTMUser(
        sub=db_user.sub,
        username=db_user.username,
        profile_img=db_user.profile_img,
    )


@pytest_asyncio.fixture(scope="function")
async def new_mapper_user(db):
    """A test user."""
    db_user = await get_or_create_user(
        db,
        AuthUser(
            sub="osm|2",
            username="local mapper",
            is_admin=False,
        ),
    )

    return FMTMUser(
        sub=db_user.sub,
        username=db_user.username,
        profile_img=db_user.profile_img,
    )


@pytest_asyncio.fixture(scope="function")
async def project(db, admin_user):
    """A test project, using the test user."""
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
        field_mapping_app=FieldMappingApp.ODK,
        description="test",
        osm_category="buildings",
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
        created_by_sub=admin_user.sub,
        external_project_id=odkproject.get("id"),
        xlsform_content=b"Dummy XLSForm content",
    )

    # Create Field-TM Project
    try:
        new_project = await DbProject.create(db, project_metadata)
        log.debug(f"Project returned: {new_project}")
        assert new_project is not None
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    # Get project, including all calculated fields
    project_all_data = await DbProject.one(db, new_project.id)
    assert isinstance(project_all_data.bbox, list)
    assert isinstance(project_all_data.bbox[0], float)
    return project_all_data


@pytest_asyncio.fixture(scope="function")
async def odk_project(db, client, project):
    """Create ODK Central resources for a project and generate the necessary files."""
    with open(f"{test_data_path}/data_extract_kathmandu.geojson", "rb") as f:
        data_extracts = json.dumps(json.load(f))
    log.debug(f"Uploading custom data extracts: {str(data_extracts)[:100]}...")
    data_extract_s3_path = await project_crud.upload_geojson_data_extract(
        db,
        project.id,
        data_extracts,
    )

    internal_s3_url = f"{settings.S3_ENDPOINT}{urlparse(data_extract_s3_path).path}"

    async with AsyncClient() as client_httpx:
        response = await client_httpx.head(internal_s3_url, follow_redirects=True)
        assert response.status_code < 400, (
            f"HEAD request failed with status {response.status_code}"
        )

    xlsform_file = Path(f"{test_data_path}/buildings.xls")
    with open(xlsform_file, "rb") as xlsform_data:
        xlsform_obj = BytesIO(xlsform_data.read())

    try:
        response = await client.post(
            f"/central/upload-xlsform?project_id={project.id}",
            files={
                "xlsform": (
                    "buildings.xls",
                    xlsform_obj,
                )
            },
        )
        log.debug(f"Uploaded XLSForm for project: {project.id}")
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Failed to upload XLSForm for project: {str(e)}")

    try:
        response = await client.post(
            f"/projects/{project.id}/generate-project-data",
        )
        log.debug(f"Generated project files for project: {project.id}")
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Failed to generate project files: {str(e)}")

    yield project


@pytest_asyncio.fixture(scope="function")
async def stub_project_data():
    """Sample data for creating a project."""
    project_name = f"Test Project {uuid4()}"
    data = {
        "name": project_name,
        "field_mapping_app": "FieldTM",
        "description": "test",
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
    return data


@pytest_asyncio.fixture(scope="function")
async def stub_project(db, stub_project_data):
    """A stub project."""
    stub_project_data = StubProjectIn(**stub_project_data)
    stub_project = await DbProject.create(
        db,
        stub_project_data,
    )
    yield stub_project


@pytest_asyncio.fixture(scope="function")
async def project_data(stub_project_data):
    """Sample data for creating a project."""
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }
    odk_creds_decrypted = central_schemas.ODKCentralDecrypted(**odk_credentials)

    data = stub_project_data.copy()
    data.pop("outline")  # Remove outline from copied data
    data["name"] = "new project name"
    data.update(**odk_creds_decrypted.model_dump())
    return data


@pytest_asyncio.fixture(scope="function")
async def client(app: Litestar, db: AsyncConnection):
    """The Litestar test server."""
    # NOTE we increase startup_timeout from 5s --> 30s to avoid timeouts
    # during slow initialisation / startup (due to yaml conversion etc)
    manager = None
    try:
        async with LifespanManager(app, startup_timeout=30) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app),
                base_url=f"http://{settings.FMTM_DOMAIN}",
                follow_redirects=True,
            ) as ac:
                yield ac
    except* Exception as eg:
        # Handle ExceptionGroup from async task cleanup
        # This can happen when background tasks (e.g., from AsyncNearestCity)
        # aren't fully cleaned up before the test ends
        # We'll suppress these as they're typically harmless cleanup issues
        cleanup_related = any(
            "TaskGroup" in str(e) or "unhandled" in str(e).lower()
            for e in eg.exceptions
        )
        if cleanup_related:
            log.debug(
                f"Suppressed ExceptionGroup during test cleanup "
                f"(likely from background tasks): {eg}"
            )
        else:
            # Re-raise if it's not a cleanup issue
            raise
