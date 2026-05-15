"""Shared basemap metadata parsing and formatting helpers."""

from litestar.plugins.htmx import HTMXRequest

BYTES_PER_UNIT = 1024
METADATA_BROWSER_URL_TEMPLATE = (
    "https://api.imagery.hotosm.org/browser/external/"
    "api.imagery.hotosm.org/stac/collections/openaerialmap/items/{stac_item_id}"
)


def format_bytes(value: int | None) -> str | None:
    """Format bytes into a compact human-readable display string."""
    if value is None or value < 0:
        return None

    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    unit_index = 0
    while size >= BYTES_PER_UNIT and unit_index < len(units) - 1:
        size /= BYTES_PER_UNIT
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"

    return f"{size:.1f} {units[unit_index]}"


def coerce_optional_int(raw_value: object) -> int | None:
    """Parse optional integer values from HTMX payloads."""
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text:
        return None

    try:
        parsed = int(text)
    except ValueError:
        return None

    if parsed < 0:
        return None

    return parsed


def format_zoom_range(minzoom: int | None, maxzoom: int | None) -> str | None:
    """Format optional min/max zoom values for compact display."""
    if minzoom is None and maxzoom is None:
        return None
    if minzoom is not None and maxzoom is not None:
        return f"{minzoom}-{maxzoom}"
    if minzoom is not None:
        return f"≥{minzoom}"
    return f"≤{maxzoom}"


async def request_param(request: HTMXRequest, key: str) -> object:
    """Get a request value from query params or form payload."""
    query_params = getattr(request, "query_params", None)
    if query_params is not None:
        query_value = query_params.get(key)
        if query_value is not None and query_value != "":
            return query_value

    form_loader = getattr(request, "form", None)
    if callable(form_loader):
        try:
            form_data = await form_loader()
            form_value = form_data.get(key)
            if form_value is not None and form_value != "":
                return form_value
        except Exception:
            return None

    return None


def basemap_metadata_url(stac_item_id: str | None) -> str | None:
    """Build a metadata browser URL for the given STAC item id."""
    if not stac_item_id:
        return None

    return METADATA_BROWSER_URL_TEMPLATE.format(stac_item_id=stac_item_id)


async def request_basemap_metadata(
    request: HTMXRequest,
) -> tuple[int | None, int | None, int | None]:
    """Extract optional basemap metadata persisted across HTMX fragment swaps."""
    basemap_size_bytes = coerce_optional_int(
        await request_param(request, "mbtiles_size_bytes")
    )
    basemap_minzoom = coerce_optional_int(
        await request_param(request, "mbtiles_minzoom")
    )
    basemap_maxzoom = coerce_optional_int(
        await request_param(request, "mbtiles_maxzoom")
    )
    return basemap_size_bytes, basemap_minzoom, basemap_maxzoom
