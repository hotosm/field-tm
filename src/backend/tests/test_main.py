"""Tests for app bootstrap helpers."""

from app.config import AuthProvider, Settings
from app.main import build_login_app_url


def test_build_login_app_url_appends_app_path():
    """Public Hanko root should resolve to the centralized login app path."""
    assert (
        build_login_app_url("https://login.hotosm.org")
        == "https://login.hotosm.org/app"
    )


def test_build_login_app_url_preserves_existing_app_path():
    """Configured login app URL should not gain a duplicate /app suffix."""
    assert (
        build_login_app_url("https://login.hotosm.org/app")
        == "https://login.hotosm.org/app"
    )


def test_build_login_app_url_preserves_query_string():
    """Any configured query parameters should be retained in the final URL."""
    assert (
        build_login_app_url("https://login.hotosm.org/base?foo=bar")
        == "https://login.hotosm.org/base/app?foo=bar"
    )


def test_settings_hotosm_provider_sets_centralized_login_url():
    """HOTOSM provider should auto-configure the centralized login app URL."""
    settings = Settings(
        FTM_DOMAIN="localhost",
        ENCRYPTION_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        OSM_CLIENT_ID="test",
        OSM_CLIENT_SECRET="test",
        OSM_SECRET_KEY="test",
        AUTH_PROVIDER=AuthProvider.HOTOSM,
    )

    assert settings.HANKO_API_URL == "https://login.hotosm.org"
    assert settings.LOGIN_URL == "https://login.hotosm.org/app"


def test_settings_disabled_provider_keeps_auth_urls_optional():
    """Disabled auth should not require or auto-populate Hanko URLs."""
    settings = Settings(
        FTM_DOMAIN="localhost",
        ENCRYPTION_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        OSM_CLIENT_ID="test",
        OSM_CLIENT_SECRET="test",
        OSM_SECRET_KEY="test",
        AUTH_PROVIDER=AuthProvider.DISABLED,
    )

    assert settings.HANKO_API_URL is None
    assert settings.LOGIN_URL is None
