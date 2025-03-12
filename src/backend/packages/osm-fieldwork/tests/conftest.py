# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm-fieldwork.
#
#     osm-fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm-fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Configuration and fixtures for PyTest."""

import logging
import sys
import uuid
from pathlib import Path

import pytest
from pyodk.client import Client

from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from osm_fieldwork.OdkCentralAsync import OdkDataset

logging.basicConfig(
    level="DEBUG",
    format=("%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s | %(funcName)s:%(lineno)d | %(message)s"),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

odk_config_file = str(Path(__file__).parent / ".pyodk_config.toml")
test_data_dir = Path(__file__).parent / "test_data"


# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy_utils import create_database, database_exists


# engine = create_engine("postgres://")
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base.metadata.create_all(bind=engine)


# def pytest_configure(config):
#     """Configure pytest runs."""
#     # Stop sqlalchemy logs
#     sqlalchemy_log = logging.getLogger("sqlalchemy")
#     sqlalchemy_log.propagate = False


# @pytest.fixture(scope="session")
# def db_engine():
#     """The SQLAlchemy database engine to init."""
#     engine = create_engine(settings.FMTM_DB_URL.unicode_string())
#     if not database_exists:
#         create_database(engine.url)

#     Base.metadata.create_all(bind=engine)
#     yield engine


# @pytest.fixture(scope="function")
# def db(db_engine):
#     """Database session using db_engine."""
#     connection = db_engine.connect()

#     # begin a non-ORM transaction
#     connection.begin()

#     # bind an individual Session to the connection
#     db = TestingSessionLocal(bind=connection)

#     yield db

#     db.rollback()
#     connection.close()


# @pytest.fixture(scope="function")
# def token():
#     """Get persistent ODK Central requests session."""
#     response = requests.post("http://central:8383/v1/sessions", json={
#         "email": "test@hotosm.org",
#         "password": "Password1234"
#     })
#     return response.json().get("token")


@pytest.fixture(scope="session")
def project():
    """Get persistent ODK Central requests session."""
    return OdkProject("https://proxy", "test@hotosm.org", "Password1234")


@pytest.fixture(scope="session")
def project_details(project):
    """Get persistent ODK Central requests session."""
    return project.createProject("test project")


@pytest.fixture(scope="function")
def appuser():
    """Get appuser for a project."""
    return OdkAppUser(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )


@pytest.fixture(scope="function")
def appuser_details(appuser, project_details):
    """Get appuser for a project."""
    appuser_name = f"test_appuser_{uuid.uuid4()}"
    response = appuser.create(project_details.get("id"), appuser_name)

    assert response.get("displayName") == appuser_name

    return response


@pytest.fixture(scope="function")
def odk_form(project_details) -> tuple:
    """Get appuser for a project."""
    odk_id = project_details.get("id")
    form = OdkForm(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )
    return odk_id, form


@pytest.fixture(scope="function")
def odk_form_cleanup(odk_form):
    """Get xform for project, with automatic cleanup after."""
    odk_id, xform = odk_form
    test_xform = test_data_dir / "buildings.xml"

    form_name = xform.createForm(odk_id, str(test_xform))
    assert form_name == "test_form"

    # Before yield is used in tests
    yield odk_id, form_name, xform
    # After yield is test cleanup

    success = xform.deleteForm(odk_id, form_name)
    assert success


@pytest.fixture(scope="session")
async def odk_dataset(project_details) -> tuple:
    """Get dataset (entity list) for a project."""
    odk_id = project_details.get("id")
    dataset = OdkDataset(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )

    # Create the dataset
    async with dataset as odk_dataset:
        created_dataset = await odk_dataset.createDataset(
            odk_id,
            "features",
            [
                "geometry",
                "project_id",
                "task_id",
                "osm_id",
                "tags",
                "version",
                "changeset",
                "timestamp",
                "status",
            ],
        )
        assert created_dataset.get("name") == "features"
        assert sorted(created_dataset.get("properties", [])) == sorted(
            [
                "geometry",
                "project_id",
                "task_id",
                "osm_id",
                "tags",
                "version",
                "changeset",
                "timestamp",
                "status",
            ]
        )

    return odk_id, dataset


@pytest.fixture(scope="session")
async def odk_dataset_cleanup(odk_dataset):
    """Get Dataset for project, with automatic cleanup after."""
    odk_id, dataset = odk_dataset

    dataset_name = "features"
    async with dataset as odk_dataset:
        entity_json = await odk_dataset.createEntity(odk_id, dataset_name, "test entity", {"osm_id": "1", "geometry": "test"})
    entity_uuid = entity_json.get("uuid")

    # Before yield is used in tests
    yield odk_id, dataset_name, entity_uuid, dataset
    # After yield is test cleanup

    async with dataset as odk_dataset:
        entity_deleted = await odk_dataset.deleteEntity(odk_id, dataset_name, entity_uuid)
        assert entity_deleted


@pytest.fixture(scope="function")
async def odk_submission(odk_form_cleanup) -> tuple:
    """A submission for the project form."""
    xform_xls_definition = test_data_dir / "buildings.xml"
    odk_id, form_name, xform = odk_form_cleanup

    # NOTE this submission does not select an existing entity, but creates a new feature
    submission_id = str(uuid.uuid4())
    submission_xml = f"""
        <data id="{form_name}" version="v1">
        <meta>
            <instanceID>{submission_id}</instanceID>
        </meta>
        <start>2024-11-15T12:28:23.641Z</start>
        <end>2024-11-15T12:29:00.876Z</end>
        <today>2024-11-15</today>
        <phonenumber/>
        <deviceid>collect:OOYOOcNu8uOA2G4b</deviceid>
        <username>testuser</username>
        <instructions/>
        <warmup/>
        <feature/>
        <null/>
        <new_feature>12.750577838121643 -24.776785714285722 0.0 0.0</new_feature>
        <xid/>
        <xlocation>12.750577838121643 -24.776785714285722 0.0 0.0</xlocation>
        <task_id/>
        <status>2</status>
        <survey_questions>
            <buildings>
            <category>housing</category>
            <name/>
            <building_material/>
            <building_levels/>
            <housing/>
            <provider/>
            </buildings>
            <details>
            <power/>
            <water/>
            <age/>
            <building_prefab/>
            <building_floor/>
            <building_roof/>
            <condition/>
            <access_roof/>
            <levels_underground/>
            </details>
            <comment/>
        </survey_questions>
        <verification>
            <digitisation_correct>yes</digitisation_correct>
            <image>1.jpg</image>
            <image2>2.jpg</image2>
            <image3>3.jpg</image3>
        </verification>
        </data>
    """

    with Client(config_path=odk_config_file) as client:
        # Update the form to ensure we know the version number for submission
        # for some reason osm_fieldwork.OdkForm.create does not set the version number
        client.forms.update(form_name, project_id=odk_id, definition=xform_xls_definition)
        client.submissions.create(
            project_id=odk_id,
            form_id=form_name,
            xml=submission_xml,
            device_id=None,
            encoding="utf-8",
        )

    return odk_id, form_name


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup projects and forms after all tests (session)."""
    project = OdkProject(
        url="https://proxy",
        user="test@hotosm.org",
        passwd="Password1234",
    )

    for item in project.listProjects():
        project_id = item.get("id")
        project.deleteProject(project_id)


# @pytest.fixture(scope="function")
# def xform_details(xform, project_details):
#     """Get appuser for a project."""
#     xlsform = xls2xform_convert(buildings)
#     response = xform.createForm(
#         projectId=project_details.get("id"),
#         filespec=xlsform,
#         xform="1",
#     )
