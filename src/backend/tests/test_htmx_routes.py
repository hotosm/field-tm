from unittest.mock import AsyncMock, patch

from litestar import status_codes as status

# We don't import project_crud here directly for patching usually, but we patch where it is used or defined.
# Since htmx_routes imports it as `from app.projects import project_crud`
# We should patch `app.projects.project_crud.get_project_qrcode`


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
        # Verify arguments if needed, but simple call check is good start for integration test


async def test_project_qrcode_htmx_not_found(client):
    """Test QR code generation for non-existent project."""
    response = await client.get(
        "/project-qrcode-htmx?project_id=999999", headers={"HX-Request": "true"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
