"""HTMX route for setup-step GeoJSON validation."""

# ruff: noqa: D103

import json
import logging

import httpx
from geojson_aoi import parse_aoi
from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.config import settings
from app.db.database import db_conn
from app.helpers.geometry_utils import AREA_LIMIT_KM2, AREA_WARN_KM2, geojson_area_km2
from app.i18n import _

from ..setup_steps.setup_step_responses import (
    json_error_response as _json_error_response,
)
from ..setup_steps.setup_step_responses import (
    unexpected_error_message as _unexpected_error_message,
)

log = logging.getLogger(__name__)

TM_AOI_REQUEST_TIMEOUT_SECONDS = 30


def _tasking_manager_aoi_url(project_id: int) -> str:
    return (
        f"{str(settings.TASKING_MANAGER_API_URL).rstrip('/')}"
        f"/projects/{project_id}/queries/aoi/?as_file=false"
    )


async def _fetch_tasking_manager_aoi(
    tm_url: str, project_id: int
) -> httpx.Response | Response:
    try:
        async with httpx.AsyncClient(timeout=TM_AOI_REQUEST_TIMEOUT_SECONDS) as client:
            tm_response = await client.get(
                tm_url, headers={"accept": "application/json"}
            )
    except httpx.HTTPError as exc:
        log.error(f"Failed to reach Tasking Manager API: {exc}", exc_info=True)
        return _json_error_response(
            _("Could not reach Tasking Manager. Please try again later."), 502
        )

    if tm_response.status_code == status.HTTP_404_NOT_FOUND:
        return _json_error_response(
            _("Tasking Manager project %(id)s was not found.") % {"id": project_id},
            404,
        )
    if tm_response.status_code >= status.HTTP_400_BAD_REQUEST:
        return _json_error_response(
            _("Tasking Manager returned an error (HTTP %(status)s).")
            % {"status": tm_response.status_code},
            502,
        )

    return tm_response


def _parse_tasking_manager_aoi_response(tm_response: httpx.Response) -> dict | Response:
    try:
        tm_geojson = tm_response.json()
    except ValueError:
        return _json_error_response(
            _("Tasking Manager returned an invalid response."), 502
        )

    try:
        merged_featcol = parse_aoi(settings.FTM_DB_URL, tm_geojson, merge=False)
    except ValueError as exc:
        return _json_error_response(str(exc), 422)

    if not merged_featcol.get("features", []):
        return _json_error_response(
            _("Tasking Manager project AOI did not contain any polygon geometries."),
            422,
        )

    return (
        merged_featcol["features"][0]
        if len(merged_featcol.get("features", [])) == 1
        else merged_featcol
    )


async def _normalize_geojson_response_body(
    db: AsyncConnection, result_geojson: dict
) -> dict:
    geometry = (
        result_geojson.get("geometry")
        if result_geojson.get("type") == "Feature"
        else result_geojson
    )
    area_km2 = round(await geojson_area_km2(db, geometry), 2)

    warning = None
    if area_km2 > AREA_LIMIT_KM2:
        warning = _(
            "Area is %(area_km2)s km², which exceeds the %(area_limit)s km² limit. "
            "Please reduce your project area."
        ) % {"area_km2": area_km2, "area_limit": AREA_LIMIT_KM2}
    elif area_km2 > AREA_WARN_KM2:
        warning = _(
            "Area is %(area_km2)s km². Large areas (>%(area_warn)s km²) may take "
            "longer to process."
        ) % {"area_km2": area_km2, "area_warn": AREA_WARN_KM2}

    return {"geojson": result_geojson, "area_km2": area_km2, "warning": warning}


@post(
    path="/validate-geojson",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def validate_geojson(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.JSON),
) -> Response:
    try:
        geojson_input = data.get("geojson")
        merge_geometries = data.get("merge_geometries", False)

        if not geojson_input:
            return _json_error_response(_("GeoJSON is required"), 400)

        merged_featcol = parse_aoi(
            settings.FTM_DB_URL,
            geojson_input,
            merge=bool(merge_geometries),
        )

        if not merged_featcol.get("features", []):
            return _json_error_response(
                _("No polygon geometries found. Project area must be a polygon."),
                422,
            )

        result_geojson = (
            merged_featcol["features"][0]
            if len(merged_featcol.get("features", [])) == 1
            else merged_featcol
        )

        return Response(
            content=json.dumps(
                await _normalize_geojson_response_body(db, result_geojson)
            ),
            media_type="application/json",
            status_code=200,
        )

    except HTTPException as e:
        return _json_error_response(str(e.detail), e.status_code)
    except ValueError as e:
        return _json_error_response(str(e), 422)
    except Exception as e:
        log.error(f"Error validating GeoJSON: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else _unexpected_error_message()
        return _json_error_response(error_msg, 500)


@get(
    path="/tasking-manager-aoi/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def load_tasking_manager_aoi(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    project_id: int,
) -> Response:
    if project_id <= 0:
        return _json_error_response(
            _("Tasking Manager project ID must be a positive integer."), 400
        )

    tm_response = await _fetch_tasking_manager_aoi(
        _tasking_manager_aoi_url(project_id), project_id
    )
    if isinstance(tm_response, Response):
        return tm_response

    result_geojson = _parse_tasking_manager_aoi_response(tm_response)
    if isinstance(result_geojson, Response):
        return result_geojson

    return Response(
        content=json.dumps(await _normalize_geojson_response_body(db, result_geojson)),
        media_type="application/json",
        status_code=200,
    )


ROUTE_HANDLERS = [
    validate_geojson,
    load_tasking_manager_aoi,
]
