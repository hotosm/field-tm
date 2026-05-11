"""Helpers for setup-step extract HTMX routes."""

import json
import logging

from litestar import status_codes as status
from litestar.response import Response
from psycopg import AsyncConnection

from app.db.models import DbProject
from app.i18n import _

from ..htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


async def get_submitted_geojson_data(
    db: AsyncConnection,
    project_id: int,
    data: dict,
) -> tuple[dict | None, Response | None]:
    """Load submitted GeoJSON from payload or fallback to project value."""
    if "geojson-data" not in data:
        log.debug("No geojson-data in request, falling back to database")
        project_db = await DbProject.one(db, project_id)
        return project_db.data_extract_geojson, None

    try:
        geojson_str = data["geojson-data"]
        geojson_len = len(geojson_str) if geojson_str else 0
        log.debug("Received geojson-data, length: %s", geojson_len)
        geojson_data = json.loads(geojson_str)
        parsed_feature_count = len(geojson_data.get("features", []))
        log.debug("Successfully parsed GeoJSON with %s features", parsed_feature_count)
        return geojson_data, None
    except json.JSONDecodeError as exc:
        log.error("Failed to parse GeoJSON from request: %s", exc)
        return None, Response(
            content=_callout(
                "danger",
                _("Invalid GeoJSON data in request. Please try uploading again."),
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except (TypeError, KeyError) as exc:
        log.error("Error accessing geojson-data from request: %s", exc)
        return None, Response(
            content=_callout("danger", _("Error reading GeoJSON data from request.")),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
