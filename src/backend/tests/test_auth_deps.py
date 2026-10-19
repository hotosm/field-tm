"""Tests for authentication dependency helpers."""

from types import SimpleNamespace

from app.auth import auth_deps
from app.auth.auth_deps import get_local_admin_auth_user, get_user_sub
from app.config import AuthProvider, settings


def test_local_admin_auth_user_preserves_custom_sub_with_bundled_auth(monkeypatch):
    """Bundled auth must not rewrite the internal local admin subject."""
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    local_admin = get_local_admin_auth_user()

    assert local_admin.sub == "custom|1"
    assert get_user_sub(local_admin) == "custom|1"


def test_local_admin_auth_user_preserves_disabled_auth_sub(monkeypatch):
    """Disabled auth keeps the historical custom local admin subject."""
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.DISABLED)

    local_admin = get_local_admin_auth_user()

    assert local_admin.sub == "custom|1"
    assert get_user_sub(local_admin) == "custom|1"


def test_get_user_sub_reprefixes_external_subject_with_bundled_auth(monkeypatch):
    """Non-local provider subjects still normalize to the active auth provider."""
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    assert get_user_sub(SimpleNamespace(sub="osm|123")) == "fieldtm|123"


async def test_debug_does_not_bypass_auth(monkeypatch):
    """DEBUG must never grant the local admin; only AUTH_PROVIDER=disabled does."""
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    async def _no_session(_request):
        return None

    monkeypatch.setattr(auth_deps, "get_current_user_optional", _no_session)

    assert await auth_deps.get_optional_auth_user(object()) is None
