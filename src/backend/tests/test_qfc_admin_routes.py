"""Integration tests for QFieldCloud admin HTMX routes without mocks."""

import os
from uuid import uuid4

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


@pytest.mark.asyncio
async def test_add_collaborator_invalid_session_returns_error(client):
    """Collaborator add should return a callout when URL/token are invalid."""
    response = await client.post(
        "/qfc-admin/projects/project-123/collaborators",
        data={
            "qfc_url": "http://invalid-qfc-host:8000/api/v1/",
            "qfc_token": "invalid-token",
            "new_username": f"missing-{uuid4().hex[:8]}",
            "new_role": "editor",
            "project_owner": "HOTOSM",
        },
    )
    assert response.status_code == 200
    assert (
        "Failed to add collaborator" in response.text
        or "project 'project-123' not found" in response.text
    )
