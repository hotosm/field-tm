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
