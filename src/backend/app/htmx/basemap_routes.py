# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#

"""Basemap HTMX routes."""

import asyncio
import logging
from datetime import datetime, timezone

from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager
from app.config import settings
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectStatus
from app.db.models import DbProject
from app.helpers.basemap_services import (
    check_tilepack_status,
    search_oam_imagery,
    trigger_tilepack_generation,
)
from app.i18n import _
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_crud import (
    _outline_to_bbox_str,
    attach_basemap_to_qfield_project,
    get_missing_basemap_attach_config,
)

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)
BYTES_PER_UNIT = 1024
METADATA_BROWSER_URL_TEMPLATE = (
    "https://api.imagery.hotosm.org/browser/external/"
    "api.imagery.hotosm.org/stac/collections/openaerialmap/items/{stac_item_id}"
)


def _project_not_found_response() -> Response:
    """Return a consistent 404 response when project context is missing."""
    return Response(
        content=_callout("danger", _("Project not found or access denied.")),
        media_type="text/html",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def _format_bytes(value: int | None) -> str | None:
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


def _coerce_optional_int(raw_value: object) -> int | None:
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


def _format_zoom_range(minzoom: int | None, maxzoom: int | None) -> str | None:
    """Format optional min/max zoom values for compact display."""
    if minzoom is None and maxzoom is None:
        return None
    if minzoom is not None and maxzoom is not None:
        return f"{minzoom}-{maxzoom}"
    if minzoom is not None:
        return f"≥{minzoom}"
    return f"≤{maxzoom}"


async def _request_param(request: HTMXRequest, key: str) -> object:
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


def _basemap_metadata_url(stac_item_id: str | None) -> str | None:
    """Build a metadata browser URL for the given STAC item id."""
    if not stac_item_id:
        return None

    return METADATA_BROWSER_URL_TEMPLATE.format(stac_item_id=stac_item_id)


def _basemap_template_context(
    project: DbProject,
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> dict:
    """Build a shared template context for basemap fragments."""
    resolved_minzoom = (
        project.basemap_minzoom if basemap_minzoom is None else basemap_minzoom
    )
    resolved_maxzoom = (
        project.basemap_maxzoom if basemap_maxzoom is None else basemap_maxzoom
    )
    return {
        "project": project,
        "is_qfield": project.field_mapping_app == FieldMappingApp.QFIELD,
        "is_odk": project.field_mapping_app == FieldMappingApp.ODK,
        "basemap_size_bytes": basemap_size_bytes,
        "basemap_minzoom": resolved_minzoom,
        "basemap_maxzoom": resolved_maxzoom,
        "basemap_zoom_display": _format_zoom_range(resolved_minzoom, resolved_maxzoom),
        "basemap_metadata_url": _basemap_metadata_url(project.basemap_stac_item_id),
    }


def _progress_fragment(
    project: DbProject,
    progress_scope: str = "generation",
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> Template:
    """Render progress fragment."""
    return Template(
        template_name="partials/project_details/fragments/basemap_progress.html",
        context={
            **_basemap_template_context(
                project,
                basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
            "progress_scope": progress_scope,
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def _ready_fragment(
    project: DbProject,
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> Template:
    """Render ready fragment."""
    return Template(
        template_name="partials/project_details/fragments/basemap_ready.html",
        context={
            **_basemap_template_context(
                project,
                basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
            "basemap_size_display": _format_bytes(basemap_size_bytes),
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def _attach_status_fragment(project: DbProject) -> Response | Template:
    """Render basemap attach status based on attach lifecycle state."""
    attach_status = project.basemap_attach_status or "idle"

    if attach_status == "in_progress":
        return _progress_fragment(project, progress_scope="attach")

    if attach_status == "ready":
        return Response(
            content=_callout(
                "success", _("Basemap attached to QField project successfully.")
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    if attach_status == "failed":
        return _progress_fragment(project, progress_scope="attach")

    return Response(
        content=_callout("neutral", _("Basemap attach has not started yet.")),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def _attach_error_text(exc: Exception) -> str:
    """Return a concise user-facing attach failure message."""
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else None
        return detail or _("Basemap attach failed. Please try again.")

    return _("Basemap attach failed. Please try again.")


def _search_failure_response() -> Response:
    """Return a sanitized search failure response."""
    return Response(
        content=_callout(
            "danger",
            _("Failed to search imagery right now. Please try again shortly."),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _generation_failure_response() -> Response:
    """Return a sanitized generation failure response."""
    return Response(
        content=_callout(
            "danger",
            _(
                "Failed to start basemap generation right now. "
                "Please try again shortly."
            ),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _status_failure_response() -> Response:
    """Return a sanitized status failure response."""
    return Response(
        content=_callout(
            "danger",
            _("Failed to refresh basemap status right now. Please try again shortly."),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def _request_basemap_metadata(
    request: HTMXRequest,
) -> tuple[int | None, int | None, int | None]:
    """Extract optional basemap metadata persisted across HTMX fragment swaps."""
    basemap_size_bytes = _coerce_optional_int(
        await _request_param(request, "mbtiles_size_bytes")
    )
    basemap_minzoom = _coerce_optional_int(
        await _request_param(request, "mbtiles_minzoom")
    )
    basemap_maxzoom = _coerce_optional_int(
        await _request_param(request, "mbtiles_maxzoom")
    )
    return basemap_size_bytes, basemap_minzoom, basemap_maxzoom


def _attach_precondition_response(project: DbProject) -> Response | None:
    """Return the first attach precondition failure response, if any."""
    if project.status != ProjectStatus.PUBLISHED:
        return Response(
            content=_callout(
                "warning", _("Basemap attach is available after publication.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return Response(
            content=_callout(
                "warning", _("Basemap attach is only available for QField projects.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.basemap_status != "ready":
        return Response(
            content=_callout(
                "warning",
                _("Basemap is not ready yet. Please wait for generation to complete."),
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not project.basemap_url:
        return Response(
            content=_callout(
                "warning", _("No generated basemap download URL is available yet.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    missing_config = get_missing_basemap_attach_config(project)
    if not missing_config:
        return None

    return Response(
        content=_callout(
            "warning",
            _(
                "QField basemap attach is not configured on this deployment. "
                "Missing %(config)s."
            )
            % {"config": ", ".join(missing_config)},
        ),
        media_type="text/html",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def _start_basemap_attach(
    db: AsyncConnection, project_id: int, basemap_url: str
) -> Template:
    """Mark attach as in progress, enqueue background work, and render progress."""
    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            basemap_attach_status="in_progress",
            basemap_attach_error=None,
            basemap_attach_updated_at=datetime.now(timezone.utc),
        ),
    )
    await db.commit()

    asyncio.create_task(_run_basemap_attach_background(project_id, basemap_url))

    refreshed_project = await DbProject.one(db, project_id)
    return _progress_fragment(refreshed_project, progress_scope="attach")


async def _run_basemap_attach_background(project_id: int, basemap_url: str) -> None:
    """Run heavy basemap attach flow in background and persist terminal state."""
    now = datetime.now(timezone.utc)

    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
            project = await DbProject.one(db, project_id)
            await attach_basemap_to_qfield_project(db, project, basemap_url)
            await DbProject.update(
                db,
                project_id,
                ProjectUpdate(
                    basemap_attach_status="ready",
                    basemap_attach_error=None,
                    basemap_attach_updated_at=now,
                ),
            )
            await db.commit()
    except Exception as exc:
        log.exception("Basemap attach failed for project %s", project_id)
        error_text = _attach_error_text(exc)
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
            await DbProject.update(
                db,
                project_id,
                ProjectUpdate(
                    basemap_attach_status="failed",
                    basemap_attach_error=error_text,
                    basemap_attach_updated_at=now,
                ),
            )
            await db.commit()


@post(
    path="/projects/{project_id:int}/basemap/search",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def basemap_search_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Template | Response:
    """Search OAM imagery intersecting the project AOI."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return _project_not_found_response()

    if project.status != ProjectStatus.PUBLISHED:
        return Response(
            content=_callout(
                "warning", _("Basemap tools are available after publication.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        bbox = [float(v) for v in _outline_to_bbox_str(project.outline).split(",")]
        items = await search_oam_imagery(bbox)
        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(basemap_status="searching"),
        )
        await db.commit()
        project = await DbProject.one(db, project_id)
        return Template(
            template_name="partials/project_details/fragments/basemap_search_results.html",
            context={
                **_basemap_template_context(project),
                "items": items,
                "metadata_url_template": METADATA_BROWSER_URL_TEMPLATE,
            },
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception:
        log.exception("Basemap search failed for project %s", project_id)
        return _search_failure_response()


@post(
    path="/projects/{project_id:int}/basemap/generate/{stac_item_id:str}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def basemap_generate_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    stac_item_id: str = Parameter(),
) -> Template | Response:
    """Start MBTiles generation for the selected STAC item."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return _project_not_found_response()

    try:
        (
            basemap_size_bytes,
            basemap_minzoom,
            basemap_maxzoom,
        ) = await _request_basemap_metadata(request)

        current_item = project.basemap_stac_item_id
        current_status = project.basemap_status or ""

        if current_item == stac_item_id and current_status == "generating":
            refreshed_project = await DbProject.one(db, project_id)
            return _progress_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )

        if current_item == stac_item_id and current_status == "ready":
            refreshed_project = await DbProject.one(db, project_id)
            return _ready_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )

        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(
                basemap_stac_item_id=stac_item_id,
                basemap_status="generating",
                basemap_url=None,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
                basemap_attach_status="idle",
                basemap_attach_error=None,
                basemap_attach_updated_at=None,
            ),
        )

        status_value, download_url = await trigger_tilepack_generation(stac_item_id)

        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(
                basemap_status=status_value,
                basemap_url=download_url,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
        )
        await db.commit()

        refreshed_project = await DbProject.one(db, project_id)
        return (
            _ready_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
            if status_value == "ready"
            else _progress_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
        )
    except Exception:
        log.exception("Basemap generation start failed for project %s", project_id)
        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(basemap_status="failed"),
        )
        await db.commit()
        return _generation_failure_response()


@get(
    path="/projects/{project_id:int}/basemap/status",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def basemap_status_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Template | Response:
    """Poll MBTiles generation status for the selected STAC item."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return _project_not_found_response()

    if not project.basemap_stac_item_id:
        return Response(
            content=_callout("warning", _("No basemap generation in progress.")),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        (
            basemap_size_bytes,
            basemap_minzoom,
            basemap_maxzoom,
        ) = await _request_basemap_metadata(request)
        status_value, download_url = await check_tilepack_status(
            project.basemap_stac_item_id
        )

        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(
                basemap_status=status_value,
                basemap_url=download_url or project.basemap_url,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
        )
        await db.commit()

        refreshed_project = await DbProject.one(db, project_id)
        return (
            _ready_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
            if status_value == "ready"
            else _progress_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
        )
    except Exception:
        log.exception("Basemap status refresh failed for project %s", project_id)
        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(basemap_status="failed"),
        )
        await db.commit()
        return _status_failure_response()


@post(
    path="/projects/{project_id:int}/basemap/attach",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def basemap_attach_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response | Template:
    """Attach the ready MBTiles basemap to an existing QField project."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return _project_not_found_response()

    precondition_response = _attach_precondition_response(project)
    if precondition_response is not None:
        return precondition_response

    attach_status = project.basemap_attach_status or "idle"
    if attach_status == "in_progress":
        return _progress_fragment(project, progress_scope="attach")

    if attach_status == "ready":
        return _attach_status_fragment(project)

    return await _start_basemap_attach(db, project_id, project.basemap_url)


@get(
    path="/projects/{project_id:int}/basemap/attach-status",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def basemap_attach_status_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response | Template:
    """Poll QField basemap attach status for a project."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return _project_not_found_response()

    refreshed_project = await DbProject.one(db, project_id)
    return _attach_status_fragment(refreshed_project)
