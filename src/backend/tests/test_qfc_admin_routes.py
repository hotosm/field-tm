"""Tests for QFieldCloud admin HTMX routes."""

import os
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.htmx.qfc_admin.qfc_admin_routes import (
    _resolve_login_qfc_url,
    add_collaborator,
    list_collaborators,
    remove_collaborator,
    update_collaborator,
)


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
    """POST /qfc-admin/login with invalid credentials returns error."""
    response = await client.post(
        "/qfc-admin/login",
        data={
            "qfc_url": os.getenv("QFIELDCLOUD_URL", "http://qfield-app:8000"),
            "qfc_username": "invalid-user",
            "qfc_password": "invalid-password",
        },
    )
    assert response.status_code == 200
    assert "Login failed" in response.text


def test_resolve_login_qfc_url_uses_configured_url_for_local_submitted_url(monkeypatch):
    """Local/dev submitted URLs should resolve to configured QFC instance URL."""
    monkeypatch.setattr(
        "app.qfield.qfield_crud.settings.QFIELDCLOUD_URL",
        "https://configured.qfield.example.com",
    )

    assert (
        _resolve_login_qfc_url("http://localhost:8000")
        == "https://configured.qfield.example.com/api/v1/"
    )


def test_resolve_login_qfc_url_keeps_non_local_submitted_url(monkeypatch):
    """Non-local submitted URLs should be preserved even if config is set."""
    monkeypatch.setattr(
        "app.qfield.qfield_crud.settings.QFIELDCLOUD_URL",
        "https://configured.qfield.example.com",
    )

    assert (
        _resolve_login_qfc_url("https://app.qfield.cloud/a/draperc/")
        == "https://app.qfield.cloud/api/v1/"
    )


@pytest.mark.asyncio
async def test_add_collaborator_invalid_session_returns_error(client):
    """Collaborator add should return a callout when URL/token are invalid."""
    response = await client.post(
        "/qfc-admin/projects/project-123/collaborators",
        data={
            "qfc_url": "http://invalid-qfc-host:8000/api/v1/",
            "qfc_token": "invalid-token",
            "qfc_username": "qfc-admin-user",
            "new_username": f"missing-{uuid4().hex[:8]}",
            "new_role": "editor",
        },
    )
    assert response.status_code == 200
    assert (
        "Failed to add collaborator" in response.text
        or "project &#x27;project-123&#x27; not found" in response.text
    )


class _FakeQfcClient:
    """Small synchronous fake for SDK calls run through run_in_executor."""

    def __init__(self):
        self.updated_roles = []
        self.removed_users = []

    def get_project_collaborators(self, project_id):
        return [{"collaborator": "existing-user", "role": "editor"}]

    def get_project(self, project_id):
        return {"id": project_id, "owner": "project-owner"}

    def patch_project_collaborators(self, project_id, username, role):
        self.updated_roles.append((project_id, username, role.value))

    def remove_project_collaborator(self, project_id, username):
        self.removed_users.append((project_id, username))


class _InlineLoop:
    """Executor shim that runs synchronous SDK fakes inline."""

    async def run_in_executor(self, _executor, func):
        return func()


@pytest.mark.asyncio
async def test_qfc_admin_add_collaborator_uses_submitted_token(monkeypatch):
    """QFC admin collaborator add should use the frontend login token."""
    fake_client = _FakeQfcClient()
    captured = {}

    def fake_qfc_client(url, token):
        captured["client_url"] = url
        captured["client_token"] = token
        return fake_client

    async def fake_add_collaborator(client, project_id, username, role):
        captured["add"] = {
            "client": client,
            "project_id": project_id,
            "username": username,
            "role": role.value,
        }

    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes._qfc_client",
        fake_qfc_client,
    )
    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes.get_running_loop",
        lambda: _InlineLoop(),
    )
    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes.add_qfc_project_collaborator",
        fake_add_collaborator,
    )

    response = await add_collaborator.fn(
        request=Mock(),
        project_id="project-123",
        data={
            "qfc_url": "https://qfc.example.com/api/v1/",
            "qfc_token": "frontend-token",
            "qfc_username": "qfc-admin-user",
            "new_username": "new-user",
            "new_role": "editor",
        },
    )

    assert response.status_code in (None, 200)
    assert captured["client_url"] == "https://qfc.example.com/api/v1/"
    assert captured["client_token"] == "frontend-token"
    assert fake_client.username == "qfc-admin-user"
    assert captured["add"] == {
        "client": fake_client,
        "project_id": "project-123",
        "username": "new-user",
        "role": "editor",
    }


@pytest.mark.asyncio
async def test_qfc_admin_update_collaborator_uses_submitted_token(monkeypatch):
    """QFC admin collaborator update should use the frontend login token."""
    fake_client = _FakeQfcClient()
    captured = {}

    def fake_qfc_client(url, token):
        captured["client_url"] = url
        captured["client_token"] = token
        return fake_client

    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes._qfc_client",
        fake_qfc_client,
    )
    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes.get_running_loop",
        lambda: _InlineLoop(),
    )

    response = await update_collaborator.fn(
        request=Mock(),
        project_id="project-123",
        username="existing-user",
        data={
            "qfc_url": "https://qfc.example.com/api/v1/",
            "qfc_token": "frontend-token",
            "qfc_username": "qfc-admin-user",
            "role": "manager",
        },
    )

    assert response.status_code in (None, 200)
    assert captured["client_url"] == "https://qfc.example.com/api/v1/"
    assert captured["client_token"] == "frontend-token"
    assert fake_client.username == "qfc-admin-user"
    assert fake_client.updated_roles == [("project-123", "existing-user", "manager")]


@pytest.mark.asyncio
async def test_qfc_admin_remove_collaborator_uses_submitted_token(monkeypatch):
    """QFC admin collaborator removal should use the frontend login token."""
    fake_client = _FakeQfcClient()
    captured = {}

    def fake_qfc_client(url, token):
        captured["client_url"] = url
        captured["client_token"] = token
        return fake_client

    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes._qfc_client",
        fake_qfc_client,
    )
    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes.get_running_loop",
        lambda: _InlineLoop(),
    )

    response = await remove_collaborator.fn(
        request=Mock(),
        project_id="project-123",
        username="existing-user",
        data={
            "qfc_url": "https://qfc.example.com/api/v1/",
            "qfc_token": "frontend-token",
            "qfc_username": "qfc-admin-user",
        },
    )

    assert response.status_code in (None, 200)
    assert captured["client_url"] == "https://qfc.example.com/api/v1/"
    assert captured["client_token"] == "frontend-token"
    assert fake_client.username == "qfc-admin-user"
    assert fake_client.removed_users == [("project-123", "existing-user")]


@pytest.mark.asyncio
async def test_qfc_admin_list_collaborators_preserves_submitted_qfc_user(monkeypatch):
    """QFC admin collaborator forms should keep the frontend login username."""
    fake_client = _FakeQfcClient()
    captured = {}

    def fake_qfc_client(url, token):
        captured["client_url"] = url
        captured["client_token"] = token
        return fake_client

    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes._qfc_client",
        fake_qfc_client,
    )
    monkeypatch.setattr(
        "app.htmx.qfc_admin.qfc_admin_routes.get_running_loop",
        lambda: _InlineLoop(),
    )

    response = await list_collaborators.fn(
        request=Mock(),
        project_id="project-123",
        qfc_url="https://qfc.example.com/api/v1/",
        qfc_token="frontend-token",
        qfc_username="qfc-admin-user",
    )

    assert response.status_code in (None, 200)
    assert captured["client_url"] == "https://qfc.example.com/api/v1/"
    assert captured["client_token"] == "frontend-token"
    assert 'name="qfc_username" value="qfc-admin-user"' in response.content
    assert "project_owner" not in response.content


@pytest.mark.asyncio
async def test_qfc_admin_list_collaborators_requires_token():
    """QFC admin collaborator listing should fail without frontend token state."""
    response = await list_collaborators.fn(
        request=Mock(),
        project_id="project-123",
        qfc_url="",
        qfc_token="",
        qfc_username="",
    )

    assert response.status_code in (None, 200)
    assert "Session expired" in response.content
