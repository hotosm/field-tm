"""Tests for locale resolution helpers."""

from types import SimpleNamespace

from app.i18n import (
    DEFAULT_LOCALE,
    RTL_LOCALES,
    _current_locale,
    get_current_dir,
    get_preferred_locale,
    resolve_locale,
)


def make_request(
    query_params: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
):
    """Create a minimal request-like object for locale resolution tests."""
    return SimpleNamespace(
        query_params=query_params or {},
        cookies=cookies or {},
        headers=headers or {},
    )


def test_resolve_locale_prefers_query_param_over_cookie_and_browser_language():
    """Explicit language selection should beat cookie and browser defaults."""
    request = make_request(
        query_params={"lang": "fr"},
        cookies={"ftm_locale": "es"},
        headers={"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"},
    )

    assert resolve_locale(request) == "fr"


def test_resolve_locale_prefers_cookie_over_browser_language():
    """Manual cookie override should beat browser language detection."""
    request = make_request(
        cookies={"ftm_locale": "es"},
        headers={"Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8"},
    )

    assert resolve_locale(request) == "es"


def test_get_preferred_locale_matches_supported_region_variant():
    """Browser locale variants should match supported underscore locales."""
    assert get_preferred_locale("pt-BR,pt;q=0.9,en;q=0.8") == "pt_br"


def test_get_preferred_locale_uses_quality_ordering():
    """Higher quality supported locales should win over earlier lower-ranked ones."""
    assert get_preferred_locale("es;q=0.4,fr;q=0.9,en;q=0.8") == "fr"


def test_resolve_locale_falls_back_to_english_for_unsupported_browser_locale():
    """Unsupported browser locales should fall back to the default locale."""
    request = make_request(headers={"Accept-Language": "de-DE,de;q=0.9"})

    assert resolve_locale(request) == DEFAULT_LOCALE


def test_get_current_dir_returns_rtl_for_arabic():
    """Arabic locale should produce dir='rtl'."""
    token = _current_locale.set("ar")
    try:
        assert get_current_dir() == "rtl"
    finally:
        _current_locale.reset(token)


def test_get_current_dir_returns_ltr_for_english():
    """English locale should produce dir='ltr'."""
    token = _current_locale.set("en")
    try:
        assert get_current_dir() == "ltr"
    finally:
        _current_locale.reset(token)


def test_rtl_locales_are_subset_of_supported():
    """All RTL locales must be in the supported locales list."""
    from app.i18n import SUPPORTED_LOCALES

    for locale in RTL_LOCALES:
        assert locale in SUPPORTED_LOCALES, (
            f"{locale} is RTL but not in SUPPORTED_LOCALES"
        )
