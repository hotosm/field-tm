"""Tests for ODK Central dependency URL resolution."""

from unittest.mock import patch

from app.central.central_deps import _resolve_odk_creds
from app.central.central_schemas import ODKCentral


def test_resolve_odk_creds_prefers_internal_url_for_local_public_hostname():
    """Backend ODK clients should use the internal URL for local proxy hosts."""
    creds = ODKCentral(
        external_project_instance_url="http://odk.fmtm.localhost:7050",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with patch("app.central.central_deps.settings") as mock_settings:
        mock_settings.ODK_CENTRAL_URL = "http://odkcentral:8383"
        resolved = _resolve_odk_creds(creds)

    assert resolved.external_project_instance_url == "http://odkcentral:8383"
    assert resolved.external_project_username == creds.external_project_username
    assert resolved.external_project_password == creds.external_project_password


def test_resolve_odk_creds_keeps_remote_custom_url():
    """A real remote custom ODK URL should remain unchanged."""
    creds = ODKCentral(
        external_project_instance_url="https://example-odk.trycloudflare.com",
        external_project_username="admin@example.org",
        external_project_password="secret",
    )

    with patch("app.central.central_deps.settings") as mock_settings:
        mock_settings.ODK_CENTRAL_URL = "http://odkcentral:8383"
        resolved = _resolve_odk_creds(creds)

    assert resolved is creds
