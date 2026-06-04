"""HTMX routes for setup-step data extract workflow."""

# ruff: noqa: D103

from litestar import get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import mapper
from app.db.database import db_conn

from .setup_step_extract_handlers import (
    handle_accept_data_extract,
    handle_collect_new_data_only,
    handle_discard_data_extract,
    handle_download_osm_data,
    handle_preview_geojson,
    handle_submit_geojson_data_extract,
    handle_upload_geojson,
)
from .setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)


@post(
    path="/download-osm-data-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def download_osm_data_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    osm_category: str = Parameter(default="buildings"),
    geom_type: str = Parameter(default="POLYGON"),
    centroid: bool = Parameter(default=False),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_download_osm_data(
        db, project_id, osm_category, geom_type, centroid
    )


@post(
    path="/upload-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_upload_geojson(db, data, project_id)


@get(
    path="/preview-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def preview_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_preview_geojson(db, project_id)


@post(
    path="/collect-new-data-only-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def collect_new_data_only_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_collect_new_data_only(db, project_id)


@post(
    path="/submit-geojson-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def submit_geojson_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_submit_geojson_data_extract(db, project_id, data or {})


@post(
    path="/accept-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def accept_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_accept_data_extract(db, project_id)


@post(
    path="/discard-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def discard_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response
    return await handle_discard_data_extract(db, project_id)


ROUTE_HANDLERS = [
    download_osm_data_htmx,
    upload_geojson_htmx,
    preview_geojson_htmx,
    collect_new_data_only_htmx,
    submit_geojson_data_extract_htmx,
    accept_data_extract_htmx,
    discard_data_extract_htmx,
]
