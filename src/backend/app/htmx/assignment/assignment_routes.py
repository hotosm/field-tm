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

"""Task assignment HTMX routes.

Manager-facing panel for assigning task areas to mappers in advance.
Assignments are stored as ``assigned_to`` / ``assigned_group`` feature
properties inside the existing ``projects.task_areas_geojson`` JSONB;
task ``status`` is owned by the field apps and is never written here.
"""

import json
import logging
from asyncio import get_running_loop
from functools import partial

from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager
from app.db.database import db_conn
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.helpers.geometry_utils import stamp_missing_task_ids
from app.i18n import _
from app.projects.project_services import (
    ServiceError,
    save_task_assignments,
)
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_utils import is_default_qfc_instance_url

from ..setup_steps.setup_step_parsing import (
    parse_json_payload as _parse_json_payload,
)
from ..setup_steps.setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)
from ..setup_steps.setup_step_responses import (
    html_error_response as _html_error_response,
)
from ..setup_steps.setup_step_responses import (
    json_error_response as _json_error_response,
)
from ..setup_steps.setup_step_responses import (
    service_error_response as _service_error_response,
)
from ..setup_steps.setup_step_responses import (
    unexpected_error_response as _unexpected_error_response,
)

log = logging.getLogger(__name__)


def _task_features(task_areas: dict | None) -> list[dict]:
    """Return the stored task area features (empty for the {} sentinel).

    Stored task_id is authoritative (stamped by save_task_areas); stamp in
    memory only for legacy rows saved before ids were persisted, mirroring
    _build_task_entities, so the panel always works with integer ids.
    """
    if not isinstance(task_areas, dict):
        return []
    features = task_areas.get("features")
    if not isinstance(features, list):
        return []
    if features:
        stamp_missing_task_ids(task_areas)
    return features


def _summary_rows(task_areas: dict | None) -> list[dict]:
    """Build summary table rows from stored task area properties."""
    rows = []
    for feature in _task_features(task_areas):
        properties = feature.get("properties") or {}
        rows.append(
            {
                "task_id": properties.get("task_id"),
                "assigned_to": properties.get("assigned_to", ""),
                "assigned_group": properties.get("assigned_group", ""),
                "building_count": properties.get("building_count"),
            }
        )
    rows.sort(key=lambda row: (row["task_id"] is None, row["task_id"]))
    return rows


def _panel_context(
    project: DbProject, assignee_suggestions: list[str] | None = None
) -> dict:
    """Shared template context for the panel and summary fragments."""
    task_areas = project.task_areas_geojson
    summary_rows = _summary_rows(task_areas)
    return {
        "project_id": project.id,
        "has_task_areas": bool(summary_rows),
        "summary_rows": summary_rows,
        "has_building_counts": any(
            row["building_count"] is not None for row in summary_rows
        ),
        "assignee_suggestions": assignee_suggestions or [],
    }


async def _qfc_assignee_suggestions(project: DbProject) -> list[str]:
    """Best-effort QFC collaborator names for the assignee datalist.

    Only QField projects on the default QFieldCloud instance have a
    collaborator list to suggest from (the same source the collaborator
    form manages); those are the only names that can auto-match in the
    QField plugin. ODK projects stay free-text-only. Failures are
    non-fatal - the panel works with an empty datalist.
    """
    if (
        project.field_mapping_app != FieldMappingApp.QFIELD
        or not project.external_project_id
        or not is_default_qfc_instance_url(project.external_project_instance_url)
    ):
        return []
    try:
        loop = get_running_loop()
        async with qfield_client() as client:
            collaborators = await loop.run_in_executor(
                None,
                partial(
                    client.get_project_collaborators,
                    str(project.external_project_id),
                ),
            )
        return sorted(
            {
                str(collab.get("collaborator"))
                for collab in collaborators
                if collab.get("collaborator")
            },
            key=str.lower,
        )
    except Exception as e:
        log.warning(
            "Could not fetch QFC collaborators for project %s: %s", project.id, e
        )
        return []


@get(
    path="/projects/{project_id:int}/assignments-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def assignment_panel_htmx(
    request: HTMXRequest,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response | Template:
    """Render the lazy-loaded task assignment panel fragment."""
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    assignee_suggestions = await _qfc_assignee_suggestions(project)
    return Template(
        template_name="partials/project_details/fragments/assignment_panel.html",
        context=_panel_context(project, assignee_suggestions),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


@get(
    path="/projects/{project_id:int}/assignments/geojson",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def assignment_geojson(
    request: HTMXRequest,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    """Return the task areas FeatureCollection with assignment properties.

    Consumed by fetch() in the assignment panel JS module, so errors are
    JSON rather than swapped HTML fragments.
    """
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return _json_error_response(
            _("Project not found or access denied."),
            status.HTTP_404_NOT_FOUND,
        )

    features = _task_features(project.task_areas_geojson)
    if not features:
        return _json_error_response(
            _("No task areas to assign. Split the project area into tasks first."),
            status.HTTP_404_NOT_FOUND,
        )

    merged_features = []
    for feature in features:
        properties = dict(feature.get("properties") or {})
        properties.setdefault("assigned_to", "")
        properties.setdefault("assigned_group", "")
        merged_features.append({**feature, "properties": properties})
    feature_collection = {"type": "FeatureCollection", "features": merged_features}

    return Response(
        content=json.dumps(feature_collection),
        media_type="application/geo+json",
        status_code=status.HTTP_200_OK,
    )


@post(
    path="/projects/{project_id:int}/assignments",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def save_assignments_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response | Template:
    """Validate and persist task assignment edits, then refresh the summary."""
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        assignments_str = data.get("assignments", "")
        if not assignments_str:
            return _html_error_response(_("No assignments data provided."), 400)

        # No HTML-unescape: the payload is set by JS via JSON.stringify and
        # never entity-encoded, so unescaping would corrupt legitimate
        # values (an assignee typed as "Bob &amp; Co" must store verbatim).
        assignments, error_response = _parse_json_payload(
            assignments_str,
            _("Invalid assignments data format."),
            "Error parsing assignments JSON",
            unescape=False,
        )
        if error_response:
            return error_response

        updated_count = await save_task_assignments(
            db=db,
            project_id=project_id,
            assignments=assignments,
        )

        refreshed_project = await DbProject.one(db, project_id)
        return Template(
            template_name=(
                "partials/project_details/fragments/assignment_summary.html"
            ),
            context={
                **_panel_context(refreshed_project),
                "saved_message": _("✓ Assignments saved"),
            },
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers={
                "Vary": "HX-Request",
                "HX-Trigger": json.dumps(
                    {
                        "assignment:saved": {
                            "projectId": project_id,
                            "updated": updated_count,
                        }
                    }
                ),
            },
        )

    except ServiceError as e:
        return _service_error_response(e)
    except Exception as e:
        # Log the detail server-side only; the rendered fragment gets the
        # generic message so internals (driver errors etc.) never reach
        # the client.
        log.error(f"Error saving assignments via HTMX: {e}", exc_info=True)
        return _unexpected_error_response()


ROUTE_HANDLERS = [
    assignment_panel_htmx,
    assignment_geojson,
    save_assignments_htmx,
]
