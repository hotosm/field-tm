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

import json
import os
import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time
from xml.etree import ElementTree

import pytest
from pyodk.client import Client

from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm

test_data_dir = Path(__file__).parent / "test_data"


@dataclass
class PyODKTestConfig:
    base_url: str
    username: str
    password: str


def _create_project(client: Client, name: str) -> dict:
    base_url = str(client.session.base_url).rstrip("/")
    response = client.session.post(
        f"{base_url}/projects",
        json={"name": name},
    )
    response.raise_for_status()
    return response.json()


def _delete_project(client: Client, project_id: int) -> None:
    base_url = str(client.session.base_url).rstrip("/")
    response = client.session.delete(f"{base_url}/projects/{project_id}")
    # Central returns 404 if already removed; tolerate this in cleanup.
    if response.status_code not in (200, 204, 404):
        response.raise_for_status()


def _delete_form(client: Client, project_id: int, form_id: str) -> None:
    base_url = str(client.session.base_url).rstrip("/")
    response = client.session.delete(
        f"{base_url}/projects/{project_id}/forms/{form_id}"
    )
    if response.status_code not in (200, 204, 404):
        response.raise_for_status()


def _list_forms(client: Client, project_id: int) -> list[dict]:
    return [form.model_dump() for form in client.forms.list(project_id=project_id)]


@pytest.fixture(scope="session")
def pyodk_config() -> PyODKTestConfig:
    odk_central_url = os.getenv("ODK_CENTRAL_URL", "")
    odk_central_user = os.getenv("ODK_CENTRAL_USER", "")
    odk_central_password = os.getenv("ODK_CENTRAL_PASSWD", "")
    return PyODKTestConfig(
        base_url=odk_central_url,
        username=odk_central_user,
        password=odk_central_password,
    )


@pytest.fixture(scope="function")
def pyodk_client(pyodk_config):
    if not pyodk_config.base_url or not pyodk_config.username:
        pytest.skip("ODK_CENTRAL_URL and ODK_CENTRAL_USER are required for ODK tests.")

    with NamedTemporaryFile(mode="w", suffix=".toml", encoding="utf-8") as cfg:
        cfg.write("[central]\n")
        cfg.write(f"base_url = {json.dumps(pyodk_config.base_url)}\n")
        cfg.write(f"username = {json.dumps(pyodk_config.username)}\n")
        cfg.write(f"password = {json.dumps(pyodk_config.password)}\n")
        cfg.flush()
        with Client(config_path=cfg.name) as client:
            yield client


@pytest.fixture(scope="function")
def project_details(pyodk_client):
    project_name = f"test project {uuid.uuid4()}"
    details = _create_project(pyodk_client, project_name)
    try:
        yield details
    finally:
        _delete_project(pyodk_client, details["id"])


@pytest.fixture(scope="function")
def appuser(pyodk_config):
    """Legacy helper kept for QR code generation utility."""
    return OdkAppUser(pyodk_config.base_url, pyodk_config.username, pyodk_config.password)


@pytest.fixture(scope="function")
def appuser_details(pyodk_client, project_details):
    appuser_name = f"test_appuser_{uuid.uuid4()}"
    response = pyodk_client.session.post(
        f"projects/{project_details['id']}/app-users",
        json={"displayName": appuser_name},
    )
    response.raise_for_status()
    data = response.json()
    assert data.get("displayName") == appuser_name
    return data


def update_xform_version(xform_bytesio: BytesIO) -> tuple[str, BytesIO]:
    """Update the form version in XML."""
    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }
    tree = ElementTree.parse(xform_bytesio)
    root = tree.getroot()

    xml_data = root.findall(".//xforms:data[@version]", namespaces)
    new_version = str(int(time() * 1000))
    for dt in xml_data:
        dt.set("version", new_version)

    xform_new_version = BytesIO()
    tree.write(xform_new_version, encoding="utf-8", xml_declaration=True)
    xform_new_version.seek(0)
    return new_version, xform_new_version


@pytest.fixture(scope="function")
def odk_form(pyodk_client, pyodk_config, project_details):
    """Return project id + legacy OdkForm utility object."""
    odk_id = project_details["id"]
    xform = OdkForm(pyodk_config.base_url, pyodk_config.username, pyodk_config.password)
    return odk_id, xform


@pytest.fixture(scope="function")
def odk_form_cleanup(pyodk_client, project_details):
    """Create a form with pyodk and clean it up after test."""
    odk_id = project_details["id"]
    test_xform = test_data_dir / "buildings.xml"

    with open(test_xform, "rb") as xform_file:
        xform_bytesio = BytesIO(xform_file.read())
    _new_form_version, xform_bytesio_new_version = update_xform_version(xform_bytesio)

    with NamedTemporaryFile(suffix=".xml", mode="wb") as temp_file:
        temp_file.write(xform_bytesio_new_version.getvalue())
        temp_file.flush()
        form = pyodk_client.forms.create(definition=temp_file.name, project_id=odk_id)

    form_name = form.xmlFormId
    try:
        yield odk_id, form_name
    finally:
        _delete_form(pyodk_client, odk_id, form_name)


@pytest.fixture(scope="function")
def odk_form__with_attachment_cleanup(pyodk_client, pyodk_config, project_details):
    """Create geojson-upload form and return legacy utility for uploadMedia."""
    odk_id = project_details["id"]
    test_xform = test_data_dir / "buildings_geojson_upload.xml"

    form = pyodk_client.forms.create(definition=str(test_xform), project_id=odk_id)
    form_name = form.xmlFormId

    legacy_form = OdkForm(
        pyodk_config.base_url,
        pyodk_config.username,
        pyodk_config.password,
    )
    with open(test_xform, "rb") as fh:
        legacy_form.xml = fh.read()
    legacy_form.published = True

    try:
        yield odk_id, form_name, legacy_form
    finally:
        _delete_form(pyodk_client, odk_id, form_name)


@pytest.fixture(scope="function")
async def odk_submission(odk_form_cleanup, pyodk_client) -> tuple:
    """A submission for the project form."""
    xform_definition = test_data_dir / "buildings.xml"
    with open(xform_definition, "rb") as xform_file:
        xform_bytesio = BytesIO(xform_file.read())
    new_form_version, xform_bytesio_new_version = update_xform_version(xform_bytesio)

    odk_id, form_name = odk_form_cleanup

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

    with NamedTemporaryFile(suffix=".xml", mode="wb") as temp_file:
        temp_file.write(xform_bytesio_new_version.getvalue())
        temp_file.flush()
        pyodk_client.forms.update(
            form_name,
            project_id=odk_id,
            definition=temp_file.name,
        )

    pyodk_client.submissions.create(
        project_id=odk_id,
        form_id=form_name,
        xml=submission_xml,
        device_id=None,
        encoding="utf-8",
    )

    return odk_id, form_name, submission_id
