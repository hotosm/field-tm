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
"""Tests for organisation routes."""

from unittest.mock import patch

import pytest

from app.db.enums import HTTPStatus
from app.db.models import DbOrganisationManagers


async def test_create_organisation(client, organisation_data, organisation_logo):
    """Test creating an organisation."""
    with patch(
        "app.organisations.organisation_crud.send_organisation_approval_request",
        return_value=None,
    ):
        response = await client.post(
            "/organisation",
            data=organisation_data,
            files={"logo": organisation_logo},
        )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == organisation_data["name"]
    assert data["slug"] == organisation_data["slug"]
    assert data["description"] == organisation_data["description"]

    response = await client.post(
        "/organisation",
        data=organisation_data,
    )
    assert response.status_code == HTTPStatus.CONFLICT


async def test_list_unapproved_organisations(client, new_organisation):
    """Test fetching unapproved organisations."""
    response = await client.get(
        "organisation/unapproved",
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert any(org["id"] == new_organisation.id for org in data)


async def test_approve_organisation(client, db, new_organisation):
    """Test approving an organisation."""
    # Bypass the background task
    with patch(
        "app.organisations.organisation_crud.send_approval_message",
        return_value=None,
    ):
        response = await client.post(
            f"/organisation/approve?org_id={new_organisation.id}"
        )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["approved"] is True
    assert (
        await DbOrganisationManagers.get(
            db, org_id=new_organisation.id, user_sub=new_organisation.created_by
        )
        is not None
    )


async def test_get_organisations(client, new_organisation):
    """Test get list of organisations."""
    response = await client.get(
        "/organisation",
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert any(org["id"] == new_organisation.id for org in data)


async def test_get_my_organisations(client, new_organisation):
    """Test fetching organisations created by the current user."""
    response = await client.get(
        "organisation/my-organisations",
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


async def test_delete_unapproved_organisation(client, new_organisation):
    """Test deleting an organisation."""
    response = await client.delete(f"/organisation/unapproved/{new_organisation.id}")
    assert response.status_code == HTTPStatus.NO_CONTENT


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
