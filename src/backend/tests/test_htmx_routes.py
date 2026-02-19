"""Tests for HTMX routes."""

from unittest.mock import AsyncMock, patch

from litestar import status_codes as status

from app.htmx.setup_step_routes import _build_odk_finalize_success_html
from app.projects.project_services import ODKFinalizeResult

# We patch where project_crud is used/defined.
# htmx_routes imports `from app.projects import project_crud`
# so we patch `app.projects.project_crud.get_project_qrcode`


async def test_create_project_htmx(client, stub_project_data):
    """Test project creation via HTMX."""
    # The route expects form data
    response = await client.post(
        "/projects/create",
        data=stub_project_data,
        headers={"HX-Request": "true"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "HX-Redirect" in response.headers
    location = response.headers["HX-Redirect"]
    assert "/htmxprojects/" in location


async def test_project_qrcode_htmx(client, project):
    """Test QR code generation via HTMX."""
    # Mock get_project_qrcode to avoid calling ODK/QField
    with patch(
        "app.projects.project_crud.get_project_qrcode", new_callable=AsyncMock
    ) as mock_get_qrcode:
        mock_get_qrcode.return_value = "data:image/png;base64,mocked_qr_code"

        response = await client.get(
            f"/project-qrcode-htmx?project_id={project.id}",
            headers={"HX-Request": "true"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "data:image/png;base64,mocked_qr_code" in response.text
        assert "Scan QR Code" in response.text

        mock_get_qrcode.assert_called_once()
        # Simple call check is a good start for integration test


async def test_project_qrcode_htmx_not_found(client):
    """Test QR code generation for non-existent project."""
    response = await client.get(
        "/project-qrcode-htmx?project_id=999999", headers={"HX-Request": "true"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_build_odk_finalize_success_html_includes_manager_and_qr():
    """Test ODK finalize response includes manager credentials and QR markup."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="fmtm-manager@example.org",
        manager_password="StrongPass123!",
    )
    qr_data = "data:image/png;base64,mocked_qr"

    html = _build_odk_finalize_success_html(result, qr_data)

    assert "Manager Access (ODK Central UI)" in html
    assert "fmtm-manager@example.org" in html
    assert "StrongPass123!" in html
    assert "ODK Collect App User Access" in html
    assert qr_data in html
