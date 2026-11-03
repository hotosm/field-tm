"""Tasks step HTMX routes: upload a task plan, use the whole area, re-sync."""

import json
import logging

from litestar import get, post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.plugins.htmx import HTMXTemplate
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectStatus
from app.errors import (
    ServiceError,
)
from app.i18n import _
from app.projects.project_services import (
    resync_tasks,
    save_task_areas,
    tasks_geometry_changed,
)
from app.projects.task_plan import save_task_plan

from .htmx_helpers import callout
from .setup_steps.setup_step_responses import (
    html_error_response,
    hx_redirect_response,
    service_error_response,
)

log = logging.getLogger(__name__)

_MANAGER = {
    "db": Provide(db_conn),
    "auth_user": Provide(login_required),
    "current_user": Provide(project_manager),
}


@post(
    path="/projects/{project_id:int}/task-plan/upload",
    dependencies=_MANAGER,
    request_max_body_size=50 * 1024 * 1024,
)
async def upload_task_plan(
    db: AsyncConnection,
    project_id: int,
    current_user: ProjectUserDict,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
) -> Response:
    """Save an uploaded task plan GeoJSON (e.g. from the standalone planner)."""
    try:
        plan = json.loads(await data.read())
    except (UnicodeDecodeError, ValueError):
        return html_error_response(
            _("The file is not valid GeoJSON."), status.HTTP_400_BAD_REQUEST
        )
    try:
        await save_task_plan(db, project_id, plan)
    except ServiceError as e:
        return service_error_response(e)
    return hx_redirect_response(f"/projects/{project_id}")


@post(path="/projects/{project_id:int}/task-plan/whole-area", dependencies=_MANAGER)
async def use_whole_area(
    db: AsyncConnection, project_id: int, current_user: ProjectUserDict
) -> Response:
    """Replace the task plan with a single task covering the project area."""
    await save_task_areas(db, project_id, {})
    return hx_redirect_response(f"/projects/{project_id}")


def _sync_error(project) -> Response | None:
    """Return an error response unless the project can be re-synced."""
    if (
        project.field_mapping_app in (FieldMappingApp.ODK, FieldMappingApp.QFIELD)
        and project.status == ProjectStatus.PUBLISHED
        and project.external_project_id
    ):
        return None
    return html_error_response(
        _("Only published ODK and QField projects can be re-synced."),
        status.HTTP_400_BAD_REQUEST,
    )


@get(path="/projects/{project_id:int}/task-plan/sync", dependencies=_MANAGER)
async def confirm_sync_task_plan(
    project_id: int, current_user: ProjectUserDict
) -> HTMXTemplate | Response:
    """Show the re-sync warning, stronger if task areas changed."""
    project = current_user["project"]
    if error := _sync_error(project):
        return error
    return HTMXTemplate(
        template_name="partials/project_details/fragments/task_sync_confirm.html",
        context={
            "project": project,
            "geometry_changed": tasks_geometry_changed(project),
        },
    )


@post(path="/projects/{project_id:int}/task-plan/sync", dependencies=_MANAGER)
async def sync_task_plan(
    db: AsyncConnection,
    project_id: int,
    current_user: ProjectUserDict,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Push the current task plan to a published ODK or QField project."""
    project = current_user["project"]
    if error := _sync_error(project):
        return error
    app_name = (
        "ODK Central"
        if project.field_mapping_app == FieldMappingApp.ODK
        else "QFieldCloud"
    )
    try:
        await resync_tasks(db, project, reset_confirmed=bool(data.get("reset")))
    except ServiceError as e:
        return service_error_response(e)
    except Exception as e:
        log.exception("Task re-sync failed for project %s: %s", project_id, e)
        return html_error_response(
            _("Could not update the tasks in %(app)s. Please try again.")
            % {"app": app_name},
            status.HTTP_502_BAD_GATEWAY,
        )
    return Response(
        content=callout("success", _("Tasks updated in %(app)s.") % {"app": app_name}),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


ROUTE_HANDLERS = [
    upload_task_plan,
    use_whole_area,
    confirm_sync_task_plan,
    sync_task_plan,
]
