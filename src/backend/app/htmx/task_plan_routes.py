"""Tasks step HTMX routes: upload a task plan, use the whole area, re-sync."""

import json
import logging

from litestar import post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectStatus
from app.i18n import _
from app.projects.project_services import (
    ServiceError,
    save_task_areas,
    sync_odk_tasks,
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


@post(path="/projects/{project_id:int}/task-plan/sync", dependencies=_MANAGER)
async def sync_task_plan(project_id: int, current_user: ProjectUserDict) -> Response:
    """Push the current task plan to a published ODK project."""
    project = current_user["project"]
    if (
        project.field_mapping_app != FieldMappingApp.ODK
        or project.status != ProjectStatus.PUBLISHED
        or not project.external_project_id
    ):
        return html_error_response(
            _("Only published ODK projects can be re-synced."),
            status.HTTP_400_BAD_REQUEST,
        )
    try:
        await sync_odk_tasks(
            project, project.get_odk_credentials(), project.external_project_id
        )
    except Exception as e:
        log.exception("Task re-sync failed for project %s: %s", project_id, e)
        return html_error_response(
            _("Could not update the tasks in ODK Central. Please try again."),
            status.HTTP_502_BAD_GATEWAY,
        )
    return Response(
        content=callout("success", _("Tasks updated in ODK Central.")),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


ROUTE_HANDLERS = [upload_task_plan, use_whole_area, sync_task_plan]
