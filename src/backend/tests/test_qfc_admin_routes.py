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
"""Tests for QFieldCloud admin HTMX routes."""

from unittest.mock import MagicMock, patch

import pytest


async def test_qfc_admin_page_renders(client):
    """GET /qfc-admin should render the login form."""
    response = await client.get("/qfc-admin")
    assert response.status_code == 200
    body = response.text
    assert "QFieldCloud Admin" in body
    assert 'name="qfc_url"' in body
    assert 'name="qfc_username"' in body
    assert 'name="qfc_password"' in body


async def test_qfc_admin_page_prefills_url(client):
    """GET /qfc-admin?url=... should pre-fill the URL field."""
    response = await client.get(
        "/qfc-admin", params={"url": "https://qfc.example.com/api/v1/"}
    )
    assert response.status_code == 200
    # URL should be stripped of /api/v1/ suffix
    assert "https://qfc.example.com" in response.text


async def test_qfc_admin_login_missing_fields(client):
    """POST /qfc-admin/login with missing fields returns error."""
    response = await client.post(
        "/qfc-admin/login",
        data={"qfc_url": "", "qfc_username": "", "qfc_password": ""},
    )
    assert response.status_code == 200
    assert "All fields are required" in response.text


async def test_qfc_admin_login_bad_credentials(client):
    """POST /qfc-admin/login with bad credentials returns error."""
    # Mock the Client constructor + login to raise
    with patch("app.htmx.qfc_admin_routes.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.login.side_effect = Exception("Auth failed")
        mock_client_cls.return_value = mock_instance

        response = await client.post(
            "/qfc-admin/login",
            data={
                "qfc_url": "https://qfc.example.com",
                "qfc_username": "baduser",
                "qfc_password": "badpass",
            },
        )

    assert response.status_code == 200
    assert "Login failed" in response.text


async def test_qfc_admin_login_success(client):
    """Successful login should return the project management area."""
    mock_projects = [
        {
            "id": "abc-123",
            "name": "Test Project",
            "owner": "testorg",
            "description": "A test project",
            "is_public": True,
        },
    ]

    with patch("app.htmx.qfc_admin_routes.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.login.return_value = {"token": "fake-token-123"}
        mock_instance.token = "fake-token-123"
        mock_instance.list_projects.return_value = mock_projects
        mock_client_cls.return_value = mock_instance

        response = await client.post(
            "/qfc-admin/login",
            data={
                "qfc_url": "https://qfc.example.com",
                "qfc_username": "admin",
                "qfc_password": "secret",
            },
        )

    assert response.status_code == 200
    body = response.text
    assert "QFieldCloud Projects" in body
    assert "Test Project" in body
    assert "testorg" in body
    assert "Log Out" in body


async def test_qfc_admin_login_uses_configured_qfc_url_for_dev_requests(client):
    """Local-looking submitted URLs should use the configured QFC URL."""
    with (
        patch("app.htmx.qfc_admin_routes.settings") as mock_settings,
        patch("app.htmx.qfc_admin_routes.Client") as mock_client_cls,
    ):
        mock_settings.QFIELDCLOUD_URL = "http://qfield-app:8000"
        mock_instance = MagicMock()
        mock_instance.login.return_value = {"token": "fake-token-123"}
        mock_instance.token = "fake-token-123"
        mock_instance.list_projects.return_value = []
        mock_client_cls.return_value = mock_instance

        response = await client.post(
            "/qfc-admin/login",
            data={
                "qfc_url": "http://qfield.field.localhost:7050",
                "qfc_username": "admin",
                "qfc_password": "secret",
            },
        )

    assert response.status_code == 200
    mock_client_cls.assert_called_once_with(url="http://qfield-app:8000/api/v1/")


async def test_qfc_admin_login_no_projects(client):
    """Successful login with no projects shows empty state."""
    with patch("app.htmx.qfc_admin_routes.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.login.return_value = {"token": "fake-token-123"}
        mock_instance.token = "fake-token-123"
        mock_instance.list_projects.return_value = []
        mock_client_cls.return_value = mock_instance

        response = await client.post(
            "/qfc-admin/login",
            data={
                "qfc_url": "https://qfc.example.com",
                "qfc_username": "admin",
                "qfc_password": "secret",
            },
        )

    assert response.status_code == 200
    assert "No projects found" in response.text


async def test_add_collaborator_missing_user_returns_friendly_error(client):
    """Missing QFC users should return a user-friendly error message."""
    with patch("app.htmx.qfc_admin_routes._qfc_client") as mock_qfc_client:
        mock_client = MagicMock()
        mock_client.add_project_collaborator.side_effect = Exception(
            "User 'missing-user' does not exist"
        )
        mock_qfc_client.return_value = mock_client

        response = await client.post(
            "/qfc-admin/projects/project-123/collaborators",
            data={
                "qfc_url": "https://qfc.example.com/api/v1/",
                "qfc_token": "fake-token",
                "new_username": "missing-user",
                "new_role": "editor",
                "project_owner": "owner",
            },
        )

    assert response.status_code == 200
    assert "This user does not exist. Please create it first." in response.text


async def test_add_collaborator_org_permission_returns_friendly_error(client):
    """Org membership permission errors should stop before collaborator add."""
    with patch("app.htmx.qfc_admin_routes._qfc_client") as mock_qfc_client:
        mock_client = MagicMock()
        mock_client.get_organization_members.return_value = []
        mock_client.add_organization_member.side_effect = Exception(
            'Requested "http://qfield-app:8000/api/v1/members/HOTOSM/" '
            'and got "403 Forbidden": {"message": "Permission denied"}'
        )
        mock_qfc_client.return_value = mock_client

        response = await client.post(
            "/qfc-admin/projects/project-123/collaborators",
            data={
                "qfc_url": "https://qfc.example.com/api/v1/",
                "qfc_token": "fake-token",
                "new_username": "ftm_mapper_6",
                "new_role": "editor",
                "project_owner": "HOTOSM",
            },
        )

    assert response.status_code == 200
    assert (
        "The user must be added to that organization before they can be added "
        "as a collaborator." in response.text
    )
    mock_client.add_project_collaborator.assert_not_called()


if __name__ == "__main__":
    pytest.main()
