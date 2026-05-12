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

import logging

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
from app.db.database import db_conn
from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.helpers.basemap_services import (
    check_tilepack_status,
    search_oam_imagery,
    trigger_tilepack_generation,
)
from app.i18n import _
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_crud import _outline_to_bbox_str

from ..htmx_helpers import callout as _callout
from .basemap_attach_flow import (
    attach_precondition_response,
    enqueue_autostart_attach,
    start_basemap_attach,
)
from .basemap_formatting import (
    METADATA_BROWSER_URL_TEMPLATE,
    request_basemap_metadata,
)
from .basemap_fragments import (
    attach_status_fragment,
    basemap_template_context,
    generation_failure_response,
    progress_fragment,
    project_not_found_response,
    ready_fragment,
    search_failure_response,
    status_failure_response,
)

log = logging.getLogger(__name__)


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
        return project_not_found_response()

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
                **basemap_template_context(project),
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
        return search_failure_response()


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
        return project_not_found_response()

    try:
        (
            basemap_size_bytes,
            basemap_minzoom,
            basemap_maxzoom,
        ) = await request_basemap_metadata(request)

        current_item = project.basemap_stac_item_id
        current_status = project.basemap_status or ""

        if current_item == stac_item_id and current_status == "generating":
            refreshed_project = await DbProject.one(db, project_id)
            return progress_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )

        if current_item == stac_item_id and current_status == "ready":
            refreshed_project = await DbProject.one(db, project_id)
            return ready_fragment(
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
            ready_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
            if status_value == "ready"
            else progress_fragment(
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
        return generation_failure_response()


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
        return project_not_found_response()

    if not project.basemap_stac_item_id:
        return Response(
            content=_callout("warning", _("No basemap generation in progress.")),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    basemap_size_bytes: int | None = None
    basemap_minzoom: int | None = None
    basemap_maxzoom: int | None = None

    try:
        (
            basemap_size_bytes,
            basemap_minzoom,
            basemap_maxzoom,
        ) = await request_basemap_metadata(request)
        status_value, download_url = await check_tilepack_status(
            project.basemap_stac_item_id
        )

        resolved_url = download_url or project.basemap_url
        is_ready_with_url = status_value == "ready" and bool(resolved_url)

        await DbProject.update(
            db,
            project_id,
            ProjectUpdate(
                basemap_status=status_value,
                basemap_url=resolved_url,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
        )
        await db.commit()

        # If the simple-project autostart was waiting for the tilepack to be
        # ready, queue the attach now that the URL is available.
        if (
            is_ready_with_url
            and (project.basemap_attach_status or "") == "pending_autostart"
        ):
            await enqueue_autostart_attach(db, project_id, resolved_url)

        refreshed_project = await DbProject.one(db, project_id)
        return (
            ready_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
            if is_ready_with_url
            else progress_fragment(
                refreshed_project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
        )
    except Exception:
        log.exception("Basemap status refresh failed for project %s", project_id)
        if project.basemap_status == "generating":
            return progress_fragment(
                project,
                basemap_size_bytes=basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            )
        return status_failure_response()


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
        return project_not_found_response()

    precondition_response = await attach_precondition_response(db, project)
    if precondition_response is not None:
        return precondition_response

    attach_status = project.basemap_attach_status or "idle"
    if attach_status == "in_progress":
        return progress_fragment(project, progress_scope="attach")

    if attach_status == "ready":
        return attach_status_fragment(project)

    return await start_basemap_attach(db, project_id, project.basemap_url)


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
        return project_not_found_response()

    refreshed_project = await DbProject.one(db, project_id)
    return attach_status_fragment(refreshed_project)


ROUTE_HANDLERS = [
    basemap_search_htmx,
    basemap_generate_htmx,
    basemap_status_htmx,
    basemap_attach_htmx,
    basemap_attach_status_htmx,
]
