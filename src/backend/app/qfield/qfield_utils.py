"""Shared QFieldCloud URL normalization helpers."""

from urllib.parse import urlsplit

from app.config import settings


def strip_qfc_api_suffix(url: str) -> str:
    """Return the canonical QFieldCloud origin without API path segments."""
    value = (url or "").strip()
    if not value:
        return ""

    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    return value.split("/api/v1")[0].rstrip("/")


def _origin(url: str) -> str:
    """Return a normalized scheme://host[:port] origin for URL comparisons."""
    base = strip_qfc_api_suffix(url)
    parsed = urlsplit(base)
    if not parsed.scheme or not parsed.netloc:
        return base.rstrip("/").lower()
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def normalise_qfc_url(url: str) -> str:
    """Return the canonical QFieldCloud API root with trailing slash."""
    base = strip_qfc_api_suffix(url)
    if not base:
        return ""
    return f"{base}/api/v1/"


def resolve_backend_qfc_url(url: str) -> str:
    """Prefer the internal QFieldCloud URL for local public hostnames."""
    candidate_url = normalise_qfc_url(url)
    internal_url = normalise_qfc_url(str(settings.QFIELDCLOUD_URL or ""))
    if not candidate_url or not internal_url:
        return candidate_url

    public_host = (urlsplit(candidate_url).hostname or "").lower()
    internal_host = (urlsplit(internal_url).hostname or "").lower()
    if not public_host or not internal_host or public_host == internal_host:
        return candidate_url

    if (
        public_host == "localhost"
        or public_host.endswith(".localhost")
        or public_host.endswith(".dev.test")
    ):
        return internal_url

    return candidate_url


def default_qfc_ui_base_url() -> str:
    """Return the configured default QFieldCloud UI base URL."""
    if settings.DEBUG:
        return (
            f"http://qfield.{settings.FTM_DOMAIN}:{settings.FTM_DEV_PORT}"
            if settings.FTM_DEV_PORT
            else f"http://qfield.{settings.FTM_DOMAIN}"
        )

    base = strip_qfc_api_suffix(str(settings.QFIELDCLOUD_URL or ""))
    if base:
        return base

    if settings.FTM_DOMAIN:
        return (
            f"http://qfield.{settings.FTM_DOMAIN}:{settings.FTM_DEV_PORT}"
            if settings.FTM_DEV_PORT
            else f"http://qfield.{settings.FTM_DOMAIN}"
        )
    return ""


def is_default_qfc_instance_url(url: str | None) -> bool:
    """Return True when ``url`` points at the configured default QFieldCloud."""
    if not url:
        return False

    candidate = _origin(url)
    default_origins = {
        _origin(str(settings.QFIELDCLOUD_URL or "")),
        _origin(default_qfc_ui_base_url()),
    }
    default_origins.discard("")
    return candidate in default_origins
