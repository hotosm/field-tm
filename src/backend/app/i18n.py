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
DOMAIN = "messages"
SUPPORTED_LOCALES = ["en", "fr", "es", "sw"]
DEFAULT_LOCALE = "en"

_translations_cache: dict[str, gettext.GNUTranslations | gettext.NullTranslations] = {}
_current_translations: ContextVar[
    gettext.GNUTranslations | gettext.NullTranslations | None
] = ContextVar("_current_translations", default=None)
_current_locale: ContextVar[str] = ContextVar("_current_locale", default=DEFAULT_LOCALE)


def get_translations(
    locale: str,
) -> gettext.GNUTranslations | gettext.NullTranslations:
    """Return cached translations for a locale, falling back to NullTranslations."""
    if locale not in _translations_cache:
        try:
            _translations_cache[locale] = gettext.translation(
                DOMAIN, localedir=str(LOCALE_DIR), languages=[locale]
            )
        except FileNotFoundError:
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
    if lang and lang in SUPPORTED_LOCALES:
        return lang

    cookie_lang = request.cookies.get("ftm_locale")
    if cookie_lang and cookie_lang in SUPPORTED_LOCALES:
        return cookie_lang

    accept = request.headers.get("Accept-Language", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code in SUPPORTED_LOCALES:
            return code

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
