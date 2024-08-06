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
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Generator
from uuid import uuid4

import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from geojson_pydantic import Polygon
from loguru import logger as log
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.auth_routes import get_or_create_user
from app.auth.auth_schemas import AuthUser, FMTMUser
from app.central import central_crud
from app.config import encrypt_value, settings
from app.db.database import Base, get_db
from app.db.db_models import DbOrganisation, DbTaskHistory
from app.main import get_application
from app.models.enums import TaskStatus, UserRole
from app.projects import project_crud, project_schemas
from app.projects.project_schemas import ODKCentralDecrypted, ProjectInfo, ProjectUpload
from app.users.user_crud import get_user
from tests.test_data import test_data_path

engine = create_engine(settings.FMTM_DB_URL.unicode_string())
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

odk_central_url = os.getenv("ODK_CENTRAL_URL")
odk_central_user = os.getenv("ODK_CENTRAL_USER")
odk_central_password = encrypt_value(os.getenv("ODK_CENTRAL_PASSWD", ""))


def pytest_configure(config):
    """Configure pytest runs."""
    # Stop sqlalchemy logs
    sqlalchemy_log = logging.getLogger("sqlalchemy")
    sqlalchemy_log.propagate = False


@pytest.fixture(autouse=True)
def app() -> Generator[FastAPI, Any, None]:
    """Get the FastAPI test server."""
    yield get_application()


@pytest.fixture(scope="session")
def db_engine():
    """The SQLAlchemy database engine to init."""
    engine = create_engine(settings.FMTM_DB_URL.unicode_string())
    yield engine


@pytest.fixture(scope="function")
def db(db_engine):
    """Database session using db_engine."""
    connection = db_engine.connect()

    # begin a non-ORM transaction
    connection.begin()

    # bind an individual Session to the connection
    db = TestingSessionLocal(bind=connection)

    yield db

    db.rollback()
    connection.close()


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def organisation(db):
    """A test organisation."""
    return (
        db.query(DbOrganisation)
        .filter(DbOrganisation.name == "FMTM Public Beta")
        .first()
    )


@pytest.fixture(scope="function")
async def project(db, admin_user, organisation):
    """A test project, using the test user and org."""
    project_metadata = ProjectUpload(
        project_info=ProjectInfo(
            name="test project",
            short_description="test",
            description="test",
        ),
        xform_category="buildings",
        odk_central_url=os.getenv("ODK_CENTRAL_URL"),
        odk_central_user=os.getenv("ODK_CENTRAL_USER"),
        odk_central_password=os.getenv("ODK_CENTRAL_PASSWD"),
        hashtags="hashtag1 hashtag2",
        outline_geojson=Polygon(
            type="Polygon",
            coordinates=[
                [
                    [85.299989110, 27.7140080437],
                    [85.299989110, 27.7108923499],
                    [85.304783157, 27.7108923499],
                    [85.304783157, 27.7140080437],
                    [85.299989110, 27.7140080437],
                ]
            ],
        ),
        organisation_id=organisation.id,
    )

    odk_creds_decrypted = ODKCentralDecrypted(
        odk_central_url=project_metadata.odk_central_url,
        odk_central_user=project_metadata.odk_central_user,
        odk_central_password=project_metadata.odk_central_password,
    )

    # Create ODK Central Project
    try:
        odkproject = central_crud.create_odk_project(
            project_metadata.project_info.name,
            odk_creds_decrypted,
        )
        log.debug(f"ODK project returned: {odkproject}")
        assert odkproject is not None
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    # Create FMTM Project
    try:
        new_project = await project_crud.create_project_with_project_info(
            db,
            project_metadata,
            odkproject["id"],
            admin_user,
        )
        log.debug(f"Project returned: {new_project.__dict__}")
        assert new_project is not None
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    return new_project


@pytest.fixture(scope="function")
async def tasks(project, db):
    """Test tasks, using the test project."""
    boundaries = {
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
    try:
        tasks = await project_crud.create_tasks_from_geojson(
            db=db, project_id=project.id, boundaries=boundaries
        )

        assert tasks is True

        # Refresh the project to include the tasks
        db.refresh(project)
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")
    return project.tasks


@pytest.fixture(scope="function")
async def task_history(db, project, tasks, admin_user):
    """A test task history using the test user, project and task."""
    user = await get_user(db, admin_user.id)
    for task in tasks:
        task_history_entry = DbTaskHistory(
            project_id=project.id,
            task_id=task.id,
            action=TaskStatus.READY,
            action_text=f"Task created with action {TaskStatus.READY}"
            "by {user.username}",
            actioned_by=user,
            user_id=user.id,
        )
        db.add(task_history_entry)
        db.commit()
        db.refresh(task_history_entry)
    return task_history_entry


@pytest.fixture(scope="function")
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
        response = client.post(
            f"/projects/{project.id}/generate-project-data",
            files=xform_file,
        )
        log.debug(f"Generated project files for project: {project.id}")
    except Exception as e:
        log.exception(e)
        pytest.fail(f"Test failed with exception: {str(e)}")

    yield project


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def project_data():
    """Sample data for creating a project."""
    project_name = f"Test Project {uuid4()}"
    data = {
        "project_info": {
            "name": project_name,
            "short_description": "test",
            "description": "test",
        },
        "xform_category": "buildings",
        "hashtags": "#FMTM",
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
    odk_credentials = {
        "odk_central_url": odk_central_url,
        "odk_central_user": odk_central_user,
        "odk_central_password": odk_central_password,
    }

    odk_creds_models = project_schemas.ODKCentralDecrypted(**odk_credentials)

    data.update(**odk_creds_models.model_dump())
    return data


# @pytest.fixture(scope="function")
# def get_ids(db, project):
#     user_id_query = text(f"SELECT id FROM {DbUser.__table__.name} LIMIT 1")
#     organisation_id_query = text(
#         f"SELECT id FROM {DbOrganisation.__table__.name} LIMIT 1"
#     )
#     project_id_query = text(f"SELECT id FROM {DbProject.__table__.name} LIMIT 1")

#     user_id = db.execute(user_id_query).scalar()
#     organisation_id = db.execute(organisation_id_query).scalar()
#     project_id = db.execute(project_id_query).scalar()

#     data = {
#         "user_id": user_id,
#         "organisation_id": organisation_id,
#         "project_id": project_id,
#     }
#     log.debug(f"get_ids return: {data}")
#     return data


@pytest.fixture(scope="function")
def client(app, db):
    """The FastAPI test server."""
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as c:
        yield c
