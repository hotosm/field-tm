# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
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
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionality of OdkCentral.py and OdkCentralAsync.py."""

from io import BytesIO
from pathlib import Path

import pytest
import requests
import segno

from osm_fieldwork.OdkCentral import OdkCentral
from osm_fieldwork.OdkCentralAsync import OdkCentral as OdkCentralAsync

test_data_dir = Path(__file__).parent / "test_data"


def test_delete_appuser(pyodk_client, appuser_details, project_details):
    """Delete appuser using pyodk-authenticated session."""
    response = pyodk_client.session.delete(
        f"{pyodk_client.session.base_url}/v1/projects/"
        f"{project_details['id']}/app-users/{appuser_details['id']}"
    )
    assert response.ok
    assert response.json().get("success") is True


def test_create_qrcode(appuser, appuser_details):
    """Create a QR code for an appuser token."""
    qrcode = appuser.createQRCode(
        odk_id=1,
        project_name="test project",
        appuser_token=appuser_details.get("token"),
        basemap="osm",
        osm_username="svchotosm",
    )
    assert isinstance(qrcode, segno.QRCode)

    qrcode = appuser.createQRCode(
        odk_id=1,
        project_name="test project",
        appuser_token=appuser_details.get("token"),
        basemap="osm",
        osm_username="svchotosm",
        save_qrcode=True,
    )
    qrcode_file = Path("test project.png")
    assert qrcode_file.exists()
    qrcode_file.unlink()


def test_create_form_delete(pyodk_client, odk_form_cleanup):
    """Create form and delete using pyodk APIs."""
    odk_id, form_name = odk_form_cleanup

    forms = [form.model_dump() for form in pyodk_client.forms.list(project_id=odk_id)]
    assert any(form.get("xmlFormId") == form_name for form in forms)

    response = pyodk_client.session.delete(
        f"{pyodk_client.session.base_url}/v1/projects/{odk_id}/forms/{form_name}"
    )
    assert response.status_code in (200, 204)

    forms = [form.model_dump() for form in pyodk_client.forms.list(project_id=odk_id)]
    assert all(form.get("xmlFormId") != form_name for form in forms)


def test_create_form_and_publish(pyodk_client, odk_form_cleanup):
    """Create form and verify it is available to submissions (published/open)."""
    odk_id, form_name = odk_form_cleanup
    form = pyodk_client.forms.get(form_id=form_name, project_id=odk_id)
    assert form.xmlFormId == form_name
    assert form.state in {"open", "closing", "closed"}


def test_create_form_update_version(pyodk_client, odk_form_cleanup):
    """Update form definition using pyodk.forms.update and verify version changed."""
    odk_id, form_name = odk_form_cleanup
    form_before = pyodk_client.forms.get(form_id=form_name, project_id=odk_id)

    test_xform = test_data_dir / "buildings.xml"
    with open(test_xform, "r", encoding="utf-8") as fh:
        xml = fh.read()
    new_xml = xml.replace('version="v1"', 'version="v2"', 1)

    pyodk_client.forms.update(
        form_id=form_name,
        project_id=odk_id,
        definition=new_xml,
    )
    form_after = pyodk_client.forms.get(form_id=form_name, project_id=odk_id)

    assert form_before.version != form_after.version


def test_upload_media_filepath(odk_form__with_attachment_cleanup):
    """Upload media from filepath via legacy utility (still unique)."""
    odk_id, _form_name, xform = odk_form__with_attachment_cleanup
    result = xform.uploadMedia(
        odk_id,
        "test_form_geojson",
        str(test_data_dir / "osm_buildings.geojson"),
    )
    assert result.status_code == 200


def test_upload_media_bytesio_publish(odk_form__with_attachment_cleanup):
    """Upload media using bytes object via legacy utility."""
    odk_id, _form_name, xform = odk_form__with_attachment_cleanup
    with open(test_data_dir / "osm_buildings.geojson", "rb") as geojson:
        geojson_bytesio = BytesIO(geojson.read())
    result = xform.uploadMedia(
        odk_id,
        "test_form_geojson",
        geojson_bytesio,
        filename="osm_buildings.geojson",
    )
    assert result.status_code == 200


def test_form_fields_no_form(pyodk_client, project_details):
    """Attempt form-fields request when form does not exist."""
    odk_id = project_details["id"]
    response = pyodk_client.session.get(
        f"{pyodk_client.session.base_url}/v1/projects/{odk_id}/forms/test_form/fields"
        "?odata=true"
    )
    with pytest.raises(requests.exceptions.HTTPError):
        response.raise_for_status()


def test_form_fields(pyodk_client, odk_form_cleanup):
    """Test form fields for created form."""
    odk_id, form_name = odk_form_cleanup

    response = pyodk_client.session.get(
        f"{pyodk_client.session.base_url}/v1/projects/{odk_id}/forms/{form_name}/fields"
        "?odata=true"
    )
    response.raise_for_status()
    form_fields = response.json()

    field_names = {field["name"] for field in form_fields}
    test_field_names = {"xlocation", "status", "survey_questions"}
    missing_fields = test_field_names - field_names
    assert not missing_fields, f"Missing form fields: {missing_fields}"

    field_dict = {field["name"]: field for field in form_fields}
    assert field_dict.get("digitisation_problem") == {
        "path": "/verification/digitisation_problem",
        "name": "digitisation_problem",
        "type": "string",
        "binary": None,
        "selectMultiple": None,
    }, f"Mismatch or missing 'digitisation_problem': {field_dict.get('digitisation_problem')}"
    assert field_dict.get("instructions") == {
        "path": "/instructions",
        "name": "instructions",
        "type": "string",
        "binary": None,
        "selectMultiple": None,
    }, f"Mismatch or missing 'instructions': {field_dict.get('instructions')}"


def test_invalid_connection_sync():
    """Test case when connection to Central fails, sync code."""
    with pytest.raises(
        ConnectionError,
        match="Failed to connect to Central. Is the URL valid?",
    ):
        OdkCentral("https://somerandominvalidurl546456546.xyz", "test@hotosm.org", "Password1234")

    with pytest.raises(
        ConnectionError,
        match="ODK credentials are invalid, or may have changed. Please update them.",
    ):
        OdkCentral("http://central:8383", "thisuser@notexist.org", "Password1234")


async def test_invalid_connection_async():
    """Test case when connection to Central fails, async code."""
    with pytest.raises(
        ConnectionError,
        match="Failed to connect to Central. Is the URL valid?",
    ):
        async with OdkCentralAsync("https://somerandominvalidurl546456546.xyz", "test@hotosm.org", "Password1234"):
            pass

    with pytest.raises(
        ConnectionError,
        match="ODK credentials are invalid, or may have changed. Please update them.",
    ):
        async with OdkCentralAsync("http://central:8383", "thisuser@notexist.org", "Password1234"):
            pass
