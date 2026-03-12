"""Tests for app bootstrap helpers."""

from app.main import build_login_app_url


def test_build_login_app_url_appends_app_path():
    """Public Hanko root should resolve to the centralized login app path."""
    assert build_login_app_url("https://login.hotosm.org") == "https://login.hotosm.org/app"


def test_build_login_app_url_preserves_existing_app_path():
    """Configured login app URL should not gain a duplicate /app suffix."""
    assert build_login_app_url("https://login.hotosm.org/app") == "https://login.hotosm.org/app"


def test_build_login_app_url_preserves_query_string():
    """Any configured query parameters should be retained in the final URL."""
    assert (
        build_login_app_url("https://login.hotosm.org/base?foo=bar")
        == "https://login.hotosm.org/base/app?foo=bar"
    )
