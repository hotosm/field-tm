"""Unit tests for basemap service helpers."""

from __future__ import annotations

from unittest.mock import Mock

import httpx
import pytest
from litestar import status_codes as status
from litestar.exceptions import HTTPException

from app.helpers import basemap_services


class _DummyAsyncClient:
    """Minimal async client stub for monkeypatching httpx.AsyncClient."""

    def __init__(self, response=None, post_exc=None, get_exc=None):
        self._response = response
        self._post_exc = post_exc
        self._get_exc = get_exc
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        self.calls.append(("POST", args[0] if args else "", kwargs))
        if self._post_exc:
            raise self._post_exc
        return self._response

    async def get(self, *args, **kwargs):
        self.calls.append(("GET", args[0] if args else "", kwargs))
        if self._get_exc:
            raise self._get_exc
        return self._response


def test_extract_stac_feature_prefers_thumbnail_preview():
    """Feature extraction should prefer the thumbnail preview asset."""
    feature = {
        "id": "item-1",
        "collection": "oam",
        "properties": {
            "datetime": "2026-01-01T00:00:00Z",
            "platform": "sat",
            "provider": "provider-a",
            "gsd": 0.5,
            "eo:cloud_cover": 5,
        },
        "assets": {
            "thumbnail": {"href": "https://preview/thumb.jpg"},
            "visual": {"href": "https://preview/visual.jpg"},
        },
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["id"] == "item-1"
    assert item["datetime"] == "2026-01-01T00:00:00Z"
    assert item["preview_url"] == "https://preview/thumb.jpg"
    assert item["cloud_cover"] == 5


def test_extract_stac_feature_falls_back_to_start_datetime_and_cloud_cover_alias():
    """Feature extraction should use fallback datetime and cloud-cover fields."""
    feature = {
        "id": "item-2",
        "collection": "oam",
        "properties": {
            "start_datetime": "2026-02-01T00:00:00Z",
            "cloud_cover": 12,
        },
        "assets": {"overview": {"href": "https://preview/overview.jpg"}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["datetime"] == "2026-02-01T00:00:00Z"
    assert item["cloud_cover"] == 12
    assert item["preview_url"] == "https://preview/overview.jpg"


def test_extract_stac_feature_parses_mbtiles_size_bytes():
    """Feature extraction should parse MBTiles size bytes from asset metadata."""
    feature = {
        "id": "item-size",
        "collection": "oam",
        "properties": {},
        "assets": {"mbtiles": {"file": {"size": 10485760}}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["mbtiles_size_bytes"] == 10485760


def test_extract_stac_feature_includes_zoom_levels_when_valid():
    """Feature extraction should include valid min and max zoom metadata."""
    feature = {
        "id": "item-zoom-valid",
        "collection": "oam",
        "properties": {},
        "assets": {
            "mbtiles": {
                "minzoom": 8,
                "maxzoom": 16,
            }
        },
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["minzoom"] == 8
    assert item["maxzoom"] == 16


def test_extract_stac_feature_parses_numeric_string_zoom_levels():
    """Feature extraction should parse numeric zoom levels provided as strings."""
    feature = {
        "id": "item-zoom-string",
        "collection": "oam",
        "properties": {},
        "assets": {
            "mbtiles": {
                "minzoom": "10",
                "maxzoom": "14",
            }
        },
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["minzoom"] == 10
    assert item["maxzoom"] == 14


def test_extract_stac_feature_uses_none_for_invalid_mbtiles_size_bytes():
    """Feature extraction should ignore invalid MBTiles size metadata."""
    feature = {
        "id": "item-size-invalid",
        "collection": "oam",
        "properties": {},
        "assets": {"mbtiles": {"file": {"size": "not-a-number"}}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["mbtiles_size_bytes"] is None


@pytest.mark.parametrize("raw_zoom", [None, "", "abc", -1])
def test_extract_stac_feature_uses_none_for_invalid_or_missing_minzoom(raw_zoom):
    """Feature extraction should ignore invalid or missing minzoom values."""
    feature = {
        "id": "item-minzoom-invalid",
        "collection": "oam",
        "properties": {},
        "assets": {"mbtiles": {"minzoom": raw_zoom}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["minzoom"] is None


@pytest.mark.parametrize("raw_zoom", [None, "", "bad", -4])
def test_extract_stac_feature_uses_none_for_invalid_or_missing_maxzoom(raw_zoom):
    """Feature extraction should ignore invalid or missing maxzoom values."""
    feature = {
        "id": "item-maxzoom-invalid",
        "collection": "oam",
        "properties": {},
        "assets": {"mbtiles": {"maxzoom": raw_zoom}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["maxzoom"] is None


@pytest.mark.parametrize(
    "raw_size",
    [None, "", -1],
)
def test_extract_stac_feature_uses_none_for_missing_or_negative_mbtiles_size_bytes(
    raw_size,
):
    """Feature extraction should ignore missing or negative MBTiles sizes."""
    feature = {
        "id": "item-size-none",
        "collection": "oam",
        "properties": {},
        "assets": {"mbtiles": {"file": {"size": raw_size}}},
    }

    item = basemap_services._extract_stac_feature(feature)

    assert item["mbtiles_size_bytes"] is None


def test_parse_tilepack_status_429_maps_to_generating():
    """Rate-limited tilepack responses should stay in generating state."""
    status_value, download_url = basemap_services._parse_tilepack_status(429, {})

    assert status_value == "generating"
    assert download_url is None


def test_parse_tilepack_status_raises_for_upstream_http_failure():
    """Tilepack parsing should map upstream HTTP failures to a gateway error."""
    with pytest.raises(HTTPException) as exc:
        basemap_services._parse_tilepack_status(500, {"status": "failed"})

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.parametrize(
    "bbox",
    [
        [0, 0, 1],
        [10, 10, 5, 20],
        [10, 10, 20, 5],
        ["a", 0, 1, 2],
        [181, 0, 182, 1],
        [0, -95, 1, 10],
    ],
)
async def test_search_oam_imagery_rejects_invalid_bbox(bbox):
    """Imagery search should reject malformed or out-of-range bounding boxes."""
    with pytest.raises(ValueError):
        await basemap_services.search_oam_imagery(bbox)


async def test_search_oam_imagery_success(monkeypatch):
    """Imagery search should filter, normalize, and sort matching OAM items."""
    payload = {
        "features": [
            {
                "id": "new",
                "collection": "openaerialmap",
                "properties": {"datetime": "2026-03-01T00:00:00Z"},
                "assets": {},
            },
            {
                "id": "old",
                "collection": "openaerialmap",
                "properties": {"datetime": "2026-01-01T00:00:00Z"},
                "assets": {},
            },
            {
                "id": " non-oam-1 ",
                "collection": "other",
                "properties": {"datetime": "2027-01-01T00:00:00Z"},
                "assets": {},
            },
            {
                "id": "   ",
                "collection": "openaerialmap",
                "properties": {"datetime": "2028-01-01T00:00:00Z"},
                "assets": {},
            },
        ]
    }

    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value=payload)

    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: _DummyAsyncClient(response=response),
    )

    items = await basemap_services.search_oam_imagery([85.0, 27.0, 86.0, 28.0])

    assert [item["id"] for item in items] == ["new", "old"]


async def test_search_oam_imagery_maps_http_status_error(monkeypatch):
    """Imagery search should map upstream status failures to HTTP exceptions."""
    req = httpx.Request("POST", "https://example.test/search")
    resp = httpx.Response(503, request=req)
    status_error = httpx.HTTPStatusError("bad gateway", request=req, response=resp)

    response = Mock()
    response.raise_for_status = Mock(side_effect=status_error)

    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: _DummyAsyncClient(response=response),
    )

    with pytest.raises(HTTPException) as exc:
        await basemap_services.search_oam_imagery([85.0, 27.0, 86.0, 28.0])

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY


async def test_search_oam_imagery_maps_transport_error(monkeypatch):
    """Imagery search should map transport failures to HTTP exceptions."""
    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: _DummyAsyncClient(post_exc=httpx.ConnectError("boom")),
    )

    with pytest.raises(HTTPException) as exc:
        await basemap_services.search_oam_imagery([85.0, 27.0, 86.0, 28.0])

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY


async def test_trigger_tilepack_generation_ready(monkeypatch):
    """Tilepack generation should return ready status with a download URL."""
    response = Mock(status_code=200, content=b"{}")
    response.json = Mock(return_value={"url": "https://tiles/x.mbtiles"})
    client = _DummyAsyncClient(response=response)

    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: client,
    )

    status_value, download_url = await basemap_services.trigger_tilepack_generation(
        "item"
    )

    assert status_value == "ready"
    assert download_url == "https://tiles/x.mbtiles"
    assert client.calls == [
        (
            "POST",
            "https://packager.imagery.hotosm.org/tilepacks/item?format=mbtiles",
            {},
        )
    ]


async def test_check_tilepack_status_generating(monkeypatch):
    """Tilepack status should return generating while the pack is pending."""
    response = Mock(status_code=202, content=b"{}")
    response.json = Mock(return_value={})
    client = _DummyAsyncClient(response=response)

    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: client,
    )

    status_value, download_url = await basemap_services.check_tilepack_status("item")

    assert status_value == "generating"
    assert download_url is None
    assert client.calls == [
        (
            "POST",
            "https://packager.imagery.hotosm.org/tilepacks/item?format=mbtiles",
            {},
        )
    ]


async def test_check_tilepack_status_raises_on_upstream_4xx(monkeypatch):
    """Tilepack status should raise when the upstream API returns a 4xx error."""
    response = Mock(status_code=404, content=b"{}")
    response.json = Mock(return_value={"status": "failed"})

    monkeypatch.setattr(
        basemap_services.httpx,
        "AsyncClient",
        lambda **_kwargs: _DummyAsyncClient(response=response),
    )

    with pytest.raises(HTTPException) as exc:
        await basemap_services.check_tilepack_status("item")

    assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY
