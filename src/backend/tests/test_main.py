"""Tests for app bootstrap helpers."""

import os

from app import main
from app.auth.auth_routes import auth_router
from app.central.central_routes import central_router
from app.config import AuthProvider, OtelSettings, Settings
from app.helpers.helper_routes import helper_router
from app.main import _configure_template_engine, build_login_app_url, create_app
from app.projects.project_routes import api_router
from app.projects.project_schemas import StubProjectIn
from app.qfield.qfield_routes import qfield_router


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


def test_otel_settings_exclude_static_urls(monkeypatch):
    """OpenTelemetry URL exclusions should include static asset child routes."""
    monkeypatch.delenv("OTEL_PYTHON_EXCLUDED_URLS", raising=False)

    otel_settings = OtelSettings(
        FTM_DOMAIN="localhost",
        LOG_LEVEL="INFO",
        ODK_CENTRAL_URL="",
    )

    excluded_urls = otel_settings.otel_python_excluded_urls

    assert "^/static/.*" in excluded_urls
    assert os.environ["OTEL_PYTHON_EXCLUDED_URLS"] == excluded_urls


def test_create_app_skips_auth_setup_when_provider_disabled(monkeypatch):
    """Disabled auth mode must not call setup_auth()."""
    monkeypatch.setattr(main.settings, "AUTH_PROVIDER", AuthProvider.DISABLED)

    def _raise_if_called():
        raise AssertionError("setup_auth must not be called when auth is disabled")

    monkeypatch.setattr(main, "setup_auth", _raise_if_called)

    app = create_app()
    assert app is not None


def test_api_routers_share_versioned_prefix_and_tag():
    """JSON API routers should live under /api/v1 and share one schema tag."""
    assert api_router.path == "/api/v1"
    assert api_router.tags == ["api"]

    assert auth_router.path == "/api/v1/auth"
    assert auth_router.tags == ["api"]

    assert central_router.path == "/api/v1/central"
    assert central_router.tags == ["api"]

    assert helper_router.path == "/api/v1/helpers"
    assert helper_router.tags == ["api"]

    assert qfield_router.path == "/api/v1/qfield"
    assert qfield_router.tags == ["api"]


def test_stub_project_internal_fields_are_persistable():
    """Server-populated fields must not be excluded from DB model dumps."""
    assert StubProjectIn.model_fields["location_str"].exclude is not True
    assert StubProjectIn.model_fields["slug"].exclude is not True
    assert StubProjectIn.model_fields["created_by_sub"].exclude is not True


def test_template_engine_config_handles_disabled_auth_without_hanko_urls(monkeypatch):
    """Disabled auth must not attempt to derive login URL from missing Hanko URL."""

    class _FakeInnerEngine:
        def __init__(self):
            self.globals = {}

        def add_extension(self, _extension):
            return None

        def install_gettext_callables(self, *_args):
            return None

    class _FakeTemplateEngine:
        def __init__(self):
            self.engine = _FakeInnerEngine()

    monkeypatch.setattr(main.settings, "AUTH_PROVIDER", AuthProvider.DISABLED)
    monkeypatch.setattr(main.settings, "HANKO_PUBLIC_URL", None)
    monkeypatch.setattr(main.settings, "HANKO_API_URL", None)
    monkeypatch.setattr(main.settings, "LOGIN_URL", None)

    engine = _FakeTemplateEngine()
    _configure_template_engine(engine)

    assert engine.engine.globals["hanko_public_url"] == ""
    assert engine.engine.globals["login_url"] == ""
    assert engine.engine.globals["auth_enabled"] is False
