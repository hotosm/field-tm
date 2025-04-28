# Copyright (c) Humanitarian OpenStreetMap Team
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

import os
import uuid
from pathlib import Path
from io import BytesIO
from xml.etree import ElementTree
from tempfile import NamedTemporaryFile
from time import time

import pytest
from pyodk._utils.config import CentralConfig
from pyodk.client import Client

from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from osm_fieldwork.OdkCentralAsync import OdkDataset

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
#         "email": "admin@hotosm.org",
#         "password": "Password1234"
#     })
#     return response.json().get("token")


@pytest.fixture(scope="session")
def project():
    """Get persistent ODK Central requests session."""
    return OdkProject("https://odkcentral:8443", "admin@hotosm.org", "Password1234")


@pytest.fixture(scope="session")
def project_details(project):
    """Get persistent ODK Central requests session."""
    return project.createProject("test project")


@pytest.fixture(scope="function")
def appuser():
    """Get appuser for a project."""
    return OdkAppUser(
        url="https://odkcentral:8443",
        user="admin@hotosm.org",
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
        url="https://odkcentral:8443",
        user="admin@hotosm.org",
        passwd="Password1234",
    )
    return odk_id, form


def update_xform_version(xform_bytesio: BytesIO) -> tuple[str, BytesIO]:
    """Update the form version in XML."""
    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }
    # Get the form version from the XML
    tree = ElementTree.parse(xform_bytesio)
    root = tree.getroot()

    xml_data = root.findall(".//xforms:data[@version]", namespaces)
    new_version = str(int(time()))
    for dt in xml_data:
        dt.set("version", new_version)

    # Write updated XML back into BytesIO
    xform_new_version = BytesIO()
    tree.write(xform_new_version, encoding="utf-8", xml_declaration=True)

    # Reset the position for next operations
    xform_new_version.seek(0)
    return new_version, xform_new_version


@pytest.fixture(scope="function")
def odk_form_cleanup(odk_form):
    """Get xform for project, with automatic cleanup after."""
    odk_id, xform = odk_form
    test_xform = test_data_dir / "buildings.xml"

    # Modify the form version so we can publish form if same id existed previously
    with open(test_xform, "rb") as xform_file:
        xform_bytesio = BytesIO(xform_file.read())
    new_form_version, xform_bytesio_new_version = update_xform_version(xform_bytesio)

    form_name = xform.createForm(odk_id, xform_bytesio_new_version)
    assert form_name == "test_form"

    # Before yield is used in tests
    yield odk_id, form_name, xform
    # After yield is test cleanup

    success = xform.deleteForm(odk_id, form_name)
    assert success


@pytest.fixture(scope="function")
def odk_form__with_attachment_cleanup(odk_form):
    """Get xform for project, with automatic cleanup after."""
    odk_id, xform = odk_form
    test_xform = test_data_dir / "buildings_geojson_upload.xml"

    form_name = xform.createForm(odk_id, str(test_xform))
    assert form_name == "test_form_geojson"

    # Publish form first
    response_code = xform.publishForm(odk_id, form_name)
    assert response_code == 200
    assert xform.published == True

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
        url="https://odkcentral:8443",
        user="admin@hotosm.org",
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
def pyodk_config() -> CentralConfig:
    odk_central_url = os.getenv("ODK_CENTRAL_URL")
    odk_central_user = os.getenv("ODK_CENTRAL_USER")
    odk_central_password = os.getenv("ODK_CENTRAL_PASSWD", "")
    return CentralConfig(
        base_url=odk_central_url,
        username=odk_central_user,
        password=odk_central_password,
    )


@pytest.fixture(scope="function")
async def odk_submission(odk_form_cleanup, pyodk_config) -> tuple:
    """A submission for the project form."""
    xform_xls_definition = test_data_dir / "buildings.xml"
    # Modify the form version so we can publish form if same id existed previously
    with open(xform_xls_definition, "rb") as xform_file:
        xform_bytesio = BytesIO(xform_file.read())
    new_form_version, xform_bytesio_new_version = update_xform_version(xform_bytesio)

    odk_id, form_name, xform = odk_form_cleanup

    # NOTE this submission does not select an existing entity, but creates a new feature
    submission_id = str(uuid.uuid4())
    submission_xml = f"""
        <data id="{form_name}" version="{new_form_version}">
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

    with Client(pyodk_config) as client:
        # Update the form to ensure we know the version number for submission
        # for some reason osm_fieldwork.OdkForm.create does not set the version number
        with NamedTemporaryFile(suffix=".xml", mode='wb') as temp_file:
            temp_file.write(xform_bytesio_new_version.getvalue())
            temp_file.flush()  # Ensure data is written to disk before using it
            client.forms.update(form_name, project_id=odk_id, definition=temp_file.name)

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
        url="https://odkcentral:8443",
        user="admin@hotosm.org",
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
