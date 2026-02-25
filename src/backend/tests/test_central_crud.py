"""Tests for ODK Central CRUD operations."""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from litestar.exceptions import HTTPException

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.config import encrypt_value
from app.db.models import DbProject


class DummyResponse:
    """Fake HTTP response for testing."""

    def __init__(self, payload: dict | list):
        """Initialize with a JSON payload."""
        self._payload = payload

    def json(self):
        """Return the stored payload."""
        return self._payload

    def raise_for_status(self):
        """No-op status check."""
        return None


class DummySession:
    """Fake HTTP session recording calls."""

    def __init__(self):
        """Initialize with empty call log."""
        self.post_calls = []

    def get(self, path: str):
        """Handle GET requests with canned responses."""
        if path == "roles":
            return DummyResponse([{"id": 7, "name": "Project Manager"}])
        raise AssertionError(f"Unexpected GET path: {path}")

    def post(self, path: str, json: dict | None = None):
        """Handle POST requests with canned responses."""
        self.post_calls.append((path, json))
        if path == "users":
            return DummyResponse({"id": 1234})
        if path == "projects/17/assignments/7/1234":
            return DummyResponse({"success": True})
        raise AssertionError(f"Unexpected POST path: {path}")


class DummyClient:
    """Fake ODK client wrapping a DummySession."""

    def __init__(self):
        """Initialize with a DummySession."""
        self.session = DummySession()


@pytest.mark.asyncio
async def test_create_project_manager_user_success():
    """Create a project manager user and assign it to one project."""
    fake_client = DummyClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@example.org",
        external_project_password="password",
    )

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=17,
            project_name="My Test Project",
            odk_credentials=creds,
        )

    assert username.startswith("fmtm-manager-17-")
    assert username.endswith("@fieldtm.local")
    assert len(password) == 20
    assert fake_client.session.post_calls[0][0] == "users"
    assert fake_client.session.post_calls[1][0] == "projects/17/assignments/7/1234"


@pytest.mark.asyncio
async def test_create_project_manager_user_missing_role():
    """Fail when ODK does not return a Project Manager role."""

    class MissingRoleSession(DummySession):
        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 3, "name": "Project Viewer"}])
            raise AssertionError(f"Unexpected GET path: {path}")

    class MissingRoleClient(DummyClient):
        def __init__(self):
            self.session = MissingRoleSession()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield MissingRoleClient()

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        with pytest.raises(HTTPException) as exc_info:
            await central_crud.create_project_manager_user(
                project_odk_id=17,
                project_name="My Test Project",
                odk_credentials=None,
            )

    assert exc_info.value.status_code == 500
    assert "Project Manager" in str(exc_info.value.detail)


def test_get_odk_credentials_requires_complete_fields():
    """Project credentials should only resolve when all fields are present."""
    project = DbProject(external_project_instance_url="https://central.example.org")
    assert project.get_odk_credentials() is None

    project = DbProject(
        external_project_instance_url="https://central.example.org",
        external_project_username="manager@example.org",
        external_project_password_encrypted=encrypt_value("password"),
    )
    creds = project.get_odk_credentials()
    assert creds is not None
    assert creds.external_project_username == "manager@example.org"


@pytest.mark.asyncio
async def test_create_odk_project_uses_relative_projects_path():
    """Create project should post to relative 'projects' path (no duplicated /v1)."""

    class CreateSession:
        def __init__(self):
            self.post_calls = []

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            response = DummyResponse({"id": 77, "name": "Field-TM Test"})
            response.ok = True
            response.text = ""
            return response

    class CreateClient:
        def __init__(self):
            self.session = CreateSession()

    fake_client = CreateClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        result = await central_crud.create_odk_project("Test")

    assert result["id"] == 77
    assert fake_client.session.post_calls[0][0] == "projects"
    assert fake_client.session.post_calls[0][1] == {"name": "Field-TM Test"}


@pytest.mark.asyncio
async def test_delete_odk_project_uses_relative_projects_path():
    """Delete project should use relative 'projects/{id}' path."""

    class DeleteResponse:
        def raise_for_status(self):
            return None

    class DeleteSession:
        def __init__(self):
            self.delete_calls = []

        def delete(self, path: str):
            self.delete_calls.append(path)
            return DeleteResponse()

    class DeleteClient:
        def __init__(self):
            self.session = DeleteSession()

    fake_client = DeleteClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        response = await central_crud.delete_odk_project(42)

    assert fake_client.session.delete_calls == ["projects/42"]
    assert response is not None
