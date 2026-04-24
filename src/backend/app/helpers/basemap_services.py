"""Service helpers for basemap search and generation via OAM APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from litestar import status_codes as status
from litestar.exceptions import HTTPException

from app.config import settings
from app.i18n import _

REQUEST_TIMEOUT_SECONDS = 30
BBOX_COORDINATE_COUNT = 4
WORLD_LON_MIN = -180
WORLD_LON_MAX = 180
WORLD_LAT_MIN = -90
WORLD_LAT_MAX = 90


def _raise_remote_http_error(exc: httpx.HTTPStatusError, action: str) -> None:
    """Raise a consistent HTTPException for upstream HTTP failures."""
    response = exc.response
    detail = _("%(action)s failed with HTTP %(status_code)s.") % {
        "action": action,
        "status_code": response.status_code,
    }
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=detail,
    ) from exc


def _raise_remote_request_error(exc: httpx.HTTPError, action: str) -> None:
    """Raise a consistent HTTPException for upstream transport failures."""
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=_("%(action)s failed due to upstream connection error.")
        % {"action": action},
    ) from exc


def _validate_stac_bbox(bbox: list[float]) -> list[float]:
    """Validate bbox list format, ordering, and world bounds."""
    if len(bbox) != BBOX_COORDINATE_COUNT:
        raise ValueError("bbox must contain [xmin, ymin, xmax, ymax]")

    try:
        xmin, ymin, xmax, ymax = (float(v) for v in bbox)
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox values must be numeric") from exc

    if xmin >= xmax:
        raise ValueError("bbox xmin must be less than xmax")
    if ymin >= ymax:
        raise ValueError("bbox ymin must be less than ymax")

    if not (
        WORLD_LON_MIN <= xmin <= WORLD_LON_MAX
        and WORLD_LON_MIN <= xmax <= WORLD_LON_MAX
    ):
        raise ValueError("bbox longitude values must be between -180 and 180")
    if not (
        WORLD_LAT_MIN <= ymin <= WORLD_LAT_MAX
        and WORLD_LAT_MIN <= ymax <= WORLD_LAT_MAX
    ):
        raise ValueError("bbox latitude values must be between -90 and 90")

    return [xmin, ymin, xmax, ymax]


def _parse_stac_datetime(value: Any) -> datetime:
    """Parse STAC datetime values into UTC-aware datetimes for sorting."""
    text = str(value or "").strip()
    if not text:
        return datetime.min.replace(tzinfo=timezone.utc)

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stac_item_sort_key(item: dict[str, Any]) -> tuple[datetime, str]:
    """Sort extracted STAC items by recency then id for stable ordering."""
    dt = _parse_stac_datetime(item.get("end_datetime") or item.get("datetime"))
    feature_id = str(item.get("id") or "")
    return (dt, feature_id)


def _parse_mbtiles_size_bytes(assets: dict[str, Any]) -> int | None:
    """Parse MBTiles size from STAC asset metadata when available."""
    mbtiles_asset = assets.get("mbtiles") or {}
    file_meta = mbtiles_asset.get("file") or {}
    raw_size = file_meta.get("size")

    try:
        size_bytes = int(raw_size)
    except (TypeError, ValueError):
        return None

    if size_bytes < 0:
        return None

    return size_bytes


def _parse_optional_zoom_level(raw_value: object) -> int | None:
    """Parse optional zoom level metadata from STAC asset metadata."""
    try:
        zoom = int(raw_value)
    except (TypeError, ValueError):
        return None

    if zoom < 0:
        return None

    return zoom


def _extract_stac_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Extract UI-ready STAC item fields with safe fallbacks."""
    props = feature.get("properties") or {}
    assets = feature.get("assets") or {}
    mbtiles_asset = assets.get("mbtiles") or {}
    preview = None
    for key in ("thumbnail", "visual", "overview"):
        href = (assets.get(key) or {}).get("href")
        if href:
            preview = href
            break

    return {
        "id": feature.get("id"),
        "collection": feature.get("collection"),
        "datetime": props.get("datetime") or props.get("start_datetime"),
        "platform": props.get("platform"),
        "provider": props.get("provider"),
        "gsd": props.get("gsd"),
        "cloud_cover": props.get("eo:cloud_cover") or props.get("cloud_cover"),
        "preview_url": preview,
        "mbtiles_size_bytes": _parse_mbtiles_size_bytes(assets),
        "minzoom": _parse_optional_zoom_level(mbtiles_asset.get("minzoom")),
        "maxzoom": _parse_optional_zoom_level(mbtiles_asset.get("maxzoom")),
    }


def _tilepack_endpoint(stac_item_id: str) -> str:
    """Build the documented tilepack endpoint for a STAC item."""
    base_url = settings.OAM_TILEPACK_URL.rstrip("/")
    return f"{base_url}/tilepacks/{stac_item_id}?format=mbtiles"


def _parse_tilepack_status(
    status_code: int, payload: dict[str, Any]
) -> tuple[str, str | None]:
    """Map tilepack API response to internal status and optional URL."""
    direct_url = payload.get("url") or payload.get("download_url")
    state = str(payload.get("status") or payload.get("state") or "").lower()

    if status_code == status.HTTP_200_OK:
        return "ready", direct_url
    if status_code == status.HTTP_202_ACCEPTED:
        return "generating", None
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "generating", None

    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_("Tilepack API returned HTTP %(status_code)s.")
            % {"status_code": status_code},
        )

    if state in {"ready", "completed", "success"}:
        return "ready", direct_url
    if state in {"queued", "running", "processing", "generating"}:
        return "generating", None

    return "failed", None


async def search_oam_imagery(bbox: list[float]) -> list[dict[str, Any]]:
    """Search OAM STAC imagery intersecting the project bbox."""
    validated_bbox = _validate_stac_bbox(bbox)
    endpoint = f"{settings.OAM_STAC_URL.rstrip('/')}/search"
    body = {
        "bbox": validated_bbox,
        "limit": 20,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=body)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _raise_remote_http_error(exc, "OAM imagery search")
    except httpx.HTTPError as exc:
        _raise_remote_request_error(exc, "OAM imagery search")

    payload = response.json()
    features = payload.get("features") or []
    items: list[dict[str, Any]] = []
    for feature in features:
        item = _extract_stac_feature(feature)
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            continue
        # FIXME can't stac-fastapi filter by the collection in advance?
        if item.get("collection") != "openaerialmap":
            # The OAM API also catalogues maxar etc
            continue
        item["id"] = item_id
        items.append(item)

    items.sort(key=_stac_item_sort_key, reverse=True)
    return items


async def trigger_tilepack_generation(stac_item_id: str) -> tuple[str, str | None]:
    """Trigger tilepack generation for a STAC item."""
    endpoint = _tilepack_endpoint(stac_item_id)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint)
    except httpx.HTTPError as exc:
        _raise_remote_request_error(exc, "Tilepack generation trigger")

    payload = response.json() if response.content else {}
    return _parse_tilepack_status(response.status_code, payload)


async def check_tilepack_status(stac_item_id: str) -> tuple[str, str | None]:
    """Check tilepack generation status for a STAC item."""
    endpoint = _tilepack_endpoint(stac_item_id)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(endpoint)
    except httpx.HTTPError as exc:
        _raise_remote_request_error(exc, "Tilepack status check")

    payload: dict[str, Any] = {}
    if response.content:
        try:
            parsed = response.json()
        except ValueError:
            parsed = {}
        if isinstance(parsed, dict):
            payload = parsed

    return _parse_tilepack_status(response.status_code, payload)


__all__ = [
    "search_oam_imagery",
    "trigger_tilepack_generation",
    "check_tilepack_status",
    "_extract_stac_feature",
    "_parse_tilepack_status",
]
