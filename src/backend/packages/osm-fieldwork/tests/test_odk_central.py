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


def test_delete_appuser(appuser, appuser_details, project_details):
    """Create a QR Code for an appuser."""
    response = appuser.delete(
        project_details.get("id"),
        appuser_details.get("id"),
    )
    assert response.ok
    assert response.json().get("success") == True


# def test_update_role(appuser, project_details, appuser_details, xform_details):
#     """Test updating appuser role."""
#     response = appuser.updateRole(
#         projectId=project_details.get("id"), xform=xform_details.get("id"), actorId=appuser_details.get("id")
#     )
#     assert response.ok


# def test_grant_access(appuser, project_details, appuser_details, xform_details):
#     """Create granting appuser access to a form."""
#     response = appuser.grantAccess(
#         projectId=project_details.get("id"), xform=xform_details.get("id"), actorId=appuser_details.get("id")
#     )
#     assert response.ok


def test_create_qrcode(appuser, appuser_details):
    """Create a QR Code for an appuser."""
    qrcode = appuser.createQRCode(
        odk_id=1,
        project_name="test project",
        appuser_token=appuser_details.get("token"),
        basemap="osm",
        osm_username="svchotosm",
        # save_qrcode = False,
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


def test_create_form_delete(project, odk_form):
    """Create form and delete."""
    odk_id, xform = odk_form
    test_xform = test_data_dir / "buildings.xml"

    form_name = xform.createForm(odk_id, str(test_xform))
    assert form_name == "test_form"

    assert len(project.listForms(odk_id)) == 1

    success = xform.deleteForm(odk_id, form_name)
    assert success

    assert len(project.listForms(odk_id)) == 0


def test_create_form_and_publish(project, odk_form_cleanup):
    """Create form and publish."""
    odk_id, form_name, xform = odk_form_cleanup

    response_code = xform.publishForm(odk_id, form_name)
    assert response_code == 200
    assert xform.published == True


def test_create_form_and_publish_immediately(project, odk_form):
    """Create form and publish immediately."""
    odk_id, xform = odk_form
    test_xform = test_data_dir / "buildings.xml"

    form_name = xform.createForm(odk_id, str(test_xform), publish=True)
    assert form_name == "test_form"
    assert xform.published == True

    success = xform.deleteForm(odk_id, form_name)
    assert success

    assert len(project.listForms(odk_id)) == 0


def test_create_form_draft(project, odk_form_cleanup):
    """Create form draft from existing form."""
    odk_id, original_form_name, xform = odk_form_cleanup
    test_xform = test_data_dir / "buildings.xml"

    # Check original form is not draft
    assert xform.draft == False

    # Publish original form
    response_code = xform.publishForm(odk_id, original_form_name)
    assert response_code == 200
    assert xform.published == True

    # Create draft from original form (sleep 1s first for version increment)
    draft_form_name = xform.createForm(odk_id, str(test_xform), original_form_name)
    assert draft_form_name == original_form_name
    assert xform.draft == True

    # Delete the newly created draft
    success = xform.deleteForm(odk_id, draft_form_name)
    assert success

    # Create another draft from original form
    draft_form_name = xform.createForm(odk_id, str(test_xform), original_form_name)
    assert draft_form_name == original_form_name
    assert xform.draft == True

    # Publish newly created version of form
    response_code = xform.publishForm(odk_id, draft_form_name)
    assert response_code == 200
    assert xform.published == True
    assert xform.draft == False

    assert len(project.listForms(odk_id)) == 1


def test_upload_media_filepath(project, odk_form__with_attachment_cleanup):
    """Create form and upload media."""
    odk_id, original_form_name, xform = odk_form__with_attachment_cleanup

    # Upload media from filepath
    result = xform.uploadMedia(
        odk_id,
        "test_form_geojson",
        str(test_data_dir / "osm_buildings.geojson"),
    )
    assert result.status_code == 200


def test_upload_media_bytesio_publish(project, odk_form__with_attachment_cleanup):
    """Create form and upload media."""
    odk_id, original_form_name, xform = odk_form__with_attachment_cleanup

    # Upload media as object
    with open(test_data_dir / "osm_buildings.geojson", "rb") as geojson:
        geojson_bytesio = BytesIO(geojson.read())
    result = xform.uploadMedia(odk_id, "test_form_geojson", geojson_bytesio, filename="osm_buildings.geojson")
    assert result.status_code == 200


def test_form_fields_no_form(odk_form_cleanup):
    """Attempt usage of form_fields when form does not exist."""
    odk_id, form_name, xform = odk_form_cleanup
    xform.deleteForm(odk_id, form_name)
    with pytest.raises(requests.exceptions.HTTPError):
        xform.formFields(odk_id, "test_form")
    # NOTE here we create the form again... so cleanup doesn't fail
    test_xform = test_data_dir / "buildings.xml"
    xform.createForm(odk_id, str(test_xform))


def test_form_fields(odk_form_cleanup):
    """Test form fields for created form."""
    odk_id, form_name, xform = odk_form_cleanup

    # Get form fields
    form_fields = xform.formFields(odk_id, form_name)
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
    with pytest.raises(ConnectionError, match="Failed to connect to Central. Is the URL valid?"):
        OdkCentral("https://somerandominvalidurl546456546.xyz", "test@hotosm.org", "Password1234")

    with pytest.raises(ConnectionError, match="ODK credentials are invalid, or may have changed. Please update them."):
        OdkCentral("http://central:8383", "thisuser@notexist.org", "Password1234")


async def test_invalid_connection_async():
    """Test case when connection to Central fails, async code."""
    with pytest.raises(ConnectionError, match="Failed to connect to Central. Is the URL valid?"):
        async with OdkCentralAsync("https://somerandominvalidurl546456546.xyz", "test@hotosm.org", "Password1234"):
            pass

    with pytest.raises(ConnectionError, match="ODK credentials are invalid, or may have changed. Please update them."):
        async with OdkCentralAsync("http://central:8383", "thisuser@notexist.org", "Password1234"):
            pass
