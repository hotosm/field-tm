"""Internationalization (i18n) support using Python stdlib gettext.

Provides per-request locale resolution and async-safe translation
functions for use in both Jinja2 templates and Python route handlers.

Babel is used only at build time for message extraction/compilation.
At runtime, only the stdlib `gettext` module is needed.
"""

import gettext
import logging
from contextvars import ContextVar
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs

from litestar import Request
from litestar.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger(__name__)

LOCALE_DIR = Path(__file__).parent / "locales"
DOMAIN = "field_tm"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = [
    "en",
    "am",
    "ar",
    "bn",
    "cs",
    "es",
    "fr",
    "ha",
    "hi",
    "id",
    "ig",
    "it",
    "ja",
    "ne",
    "om",
    "pt",
    "pt_br",
    "ru",
    "sw",
    "ta",
    "te",
    "th",
    "tl",
    "tr",
    "ur",
    "vi",
    "yo",
    "zh",
]
RTL_LOCALES = frozenset({"ar", "ur"})

LOCALE_LABELS = {
    "en": "English",
    "am": "አማርኛ",
    "ar": "العربية",
    "bn": "বাংলা",
    "cs": "Čeština",
    "es": "Español",
    "fr": "Français",
    "ha": "Hausa",
    "hi": "हिन्दी",
    "id": "Bahasa Indonesia",
    "ig": "Igbo",
    "it": "Italiano",
    "ja": "日本語",
    "ne": "नेपाली",
    "om": "Afaan Oromoo",
    "pt": "Português",
    "pt_br": "Português (Brasil)",
    "ru": "Русский",
    "sw": "Kiswahili",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "th": "ไทย",
    "tl": "Filipino / Tagalog",
    "tr": "Türkçe",
    "ur": "اردو",
    "vi": "Tiếng Việt",
    "yo": "Yorùbá",
    "zh": "中文",
}

_translations_cache: dict[str, gettext.GNUTranslations | gettext.NullTranslations] = {}
_current_translations: ContextVar[
    gettext.GNUTranslations | gettext.NullTranslations | None
] = ContextVar("_current_translations", default=None)
_current_locale: ContextVar[str] = ContextVar("_current_locale", default=DEFAULT_LOCALE)


def normalize_locale_code(locale: str) -> str:
    """Normalize locale codes for internal matching."""
    return locale.strip().lower().replace("-", "_")


def match_supported_locale(locale: str) -> str | None:
    """Match an input locale to the closest supported locale."""
    normalized_locale = normalize_locale_code(locale)
    if normalized_locale in SUPPORTED_LOCALES:
        return normalized_locale

    base_language = normalized_locale.split("_", 1)[0]
    if base_language in SUPPORTED_LOCALES:
        return base_language

    return None


def _parse_quality(params: list[str]) -> float:
    """Extract the q= quality value from Accept-Language parameters."""
    for param in params:
        key, separator, value = param.partition("=")
        if key.strip().lower() != "q" or separator != "=":
            continue
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 1.0


def get_preferred_locale(accept_language: str) -> str | None:
    """Resolve the best supported locale from an Accept-Language header."""
    preferred_locales: list[tuple[float, int, str]] = []

    for index, part in enumerate(accept_language.split(",")):
        language_range = part.strip()
        if not language_range:
            continue

        locale, *params = (value.strip() for value in language_range.split(";"))
        if not locale or locale == "*":
            continue

        preferred_locales.append((_parse_quality(params), index, locale))

    for _quality, _index, locale in sorted(
        preferred_locales, key=lambda item: (-item[0], item[1])
    ):
        matched_locale = match_supported_locale(locale)
        if matched_locale:
            return matched_locale

    return None


def get_translations(
    locale: str,
) -> gettext.GNUTranslations | gettext.NullTranslations:
    """Return cached translations for a locale, falling back to NullTranslations."""
    if locale not in _translations_cache:
        normalized_locale = locale.replace("-", "_")
        mo_path = LOCALE_DIR / normalized_locale / "LC_MESSAGES" / f"{DOMAIN}.mo"
        try:
            with mo_path.open("rb") as mo_file:
                _translations_cache[locale] = gettext.GNUTranslations(mo_file)
        except FileNotFoundError:
            if locale != DEFAULT_LOCALE:
                log.debug(
                    "No .mo file found for locale '%s', using NullTranslations", locale
                )
            _translations_cache[locale] = gettext.NullTranslations()
    return _translations_cache[locale]


def resolve_locale(request: Request) -> str:
    """Determine the best locale for the current request.

    Priority: ?lang= query param > ftm_locale cookie > Accept-Language header > default.
    """
    lang = request.query_params.get("lang")
    matched_query_locale = match_supported_locale(lang) if lang else None
    if matched_query_locale:
        return matched_query_locale

    cookie_lang = request.cookies.get("ftm_locale")
    matched_cookie_locale = match_supported_locale(cookie_lang) if cookie_lang else None
    if matched_cookie_locale:
        return matched_cookie_locale

    accept = request.headers.get("Accept-Language", "")
    preferred_locale = get_preferred_locale(accept)
    if preferred_locale:
        return preferred_locale

    return DEFAULT_LOCALE


# -- Callables installed on the Jinja2 Environment (read from ContextVar) --


def gettext_func(message: str) -> str:
    """Translate a message using the current request's locale."""
    trans = _current_translations.get()
    return trans.gettext(message) if trans else message


def _(message: str) -> str:
    """Short gettext alias for Python code and Babel extraction."""
    return gettext_func(message)


def ngettext_func(singular: str, plural: str, n: int) -> str:
    """Translate a singular/plural message using the current request's locale."""
    trans = _current_translations.get()
    return (
        trans.ngettext(singular, plural, n)
        if trans
        else (singular if n == 1 else plural)
    )


# -- Litestar before_request hook --


async def set_locale_before_request(request: Request) -> None:
    """Before-request hook: resolve locale and set context vars."""
    locale = resolve_locale(request)
    _current_locale.set(locale)
    _current_translations.set(get_translations(locale))


# -- ASGI middleware to persist locale cookie --


def create_locale_cookie_middleware(app: ASGIApp) -> ASGIApp:
    """ASGI middleware that sets a ftm_locale cookie when ?lang= is used."""

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        # Check if ?lang= is in the query string
        qs = scope.get("query_string", b"").decode("latin-1")
        params = parse_qs(qs)
        lang_values = params.get("lang", [])
        lang = lang_values[0] if lang_values else None

        if not lang or lang not in SUPPORTED_LOCALES:
            await app(scope, receive, send)
            return

        # Inject Set-Cookie header into the response
        cookie: SimpleCookie = SimpleCookie()
        cookie["ftm_locale"] = lang
        cookie["ftm_locale"]["path"] = "/"
        cookie["ftm_locale"]["max-age"] = str(365 * 24 * 3600)
        cookie["ftm_locale"]["samesite"] = "Lax"
        cookie_header = cookie["ftm_locale"].OutputString().encode("latin-1")

        async def send_with_cookie(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"set-cookie", cookie_header))
                message["headers"] = headers
            await send(message)

        await app(scope, receive, send_with_cookie)

    return middleware


def get_current_locale() -> str:
    """Return the current request's resolved locale (for use as a Jinja global)."""
    return _current_locale.get()


def get_current_dir() -> str:
    """Return 'rtl' for right-to-left locales, 'ltr' otherwise."""
    return "rtl" if _current_locale.get() in RTL_LOCALES else "ltr"
