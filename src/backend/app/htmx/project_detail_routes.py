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

"""Project detail and QR code HTMX routes."""

import json
import logging
from contextlib import suppress

from litestar import delete, get
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import (
    get_optional_auth_user,
    get_user_is_admin,
    get_user_sub,
    login_required,
)
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import check_access, ensure_project_viewable, project_manager
from app.central import central_crud
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectRole
from app.db.models import DbProject
from app.errors import (
    DownstreamDeleteError,
    NotFoundError,
    ServiceError,
)
from app.i18n import _
from app.projects import project_crud
from app.projects.project_services import (
    delete_project_with_downstream,
)
from app.qfield.qfield_crud import export_qfield_project_geojson
from app.qfield.qfield_utils import strip_qfc_api_suffix

from .htmx_helpers import callout
from .setup_steps.setup_step_responses import (
    authorized_project_or_response,
    html_error_response,
    hx_redirect_response,
)

log = logging.getLogger(__name__)


def _app_name(project: DbProject) -> str:
    """Return a plain-text app name from the enum-like project field."""
    if hasattr(project.field_mapping_app, "value"):
        return project.field_mapping_app.value
    return str(project.field_mapping_app)


def _can_delete_project(auth_user: object | None, project: DbProject) -> bool:
    """Allow deletion by global admins or the original project creator."""
    if auth_user is None:
        return False
    if get_user_is_admin(auth_user):
        return True
    with suppress(Exception):
        return get_user_sub(auth_user) == project.created_by_sub
    return False


async def _is_project_manager(
    db: AsyncConnection, auth_user: object | None, project: DbProject
) -> bool:
    """Whether the viewer may use the manager-only parts of the project page."""
    if auth_user is None:
        return False
    return bool(
        await check_access(
            auth_user, db, project_id=project.id, role=ProjectRole.PROJECT_MANAGER
        )
    )


@get(
    path="/projects/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def project_details(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int,
    auth_user: object | None = None,
) -> HTMXTemplate:
    """Render project details page."""
    try:
        project = await DbProject.one(db, project_id)
        await ensure_project_viewable(db, project, auth_user)
        is_manager = await _is_project_manager(db, auth_user, project)
        form_templates = []
        if is_manager and not project.xlsform_content:
            form_templates = await central_crud.get_form_list(db)
        return HTMXTemplate(
            template_name="project_details.html",
            context={
                "project": project,
                "is_manager": is_manager,
                "form_templates_json": json.dumps(form_templates),
                "can_delete_project": _can_delete_project(auth_user, project),
            },
        )
    except KeyError:
        # Project not found
        return HTMXTemplate(
            template_name="project_details.html",
            context={
                "project": None,
                "is_manager": False,
                "form_templates_json": "[]",
                "can_delete_project": False,
            },
        )


@delete(
    path="/projects/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
    status_code=status.HTTP_200_OK,
)
async def delete_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int,
    auth_user: object | None = None,
) -> Response:
    """Delete a project after deleting the downstream ODK/QField project."""
    try:
        project = await DbProject.one(db, project_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Project (%(project_id)s) not found.")
            % {"project_id": project_id},
        ) from exc

    if not _can_delete_project(auth_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("Only the project manager can delete this project."),
        )

    try:
        await delete_project_with_downstream(db, project_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except DownstreamDeleteError as exc:
        return Response(
            content=callout("danger", exc.message),
            media_type="text/html",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    await db.commit()
    return hx_redirect_response("/projects")


@get(
    path="/project-qrcode-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def project_qrcode_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int = Parameter(),
    username: str = Parameter(default="fieldtm_user"),
    auth_user: object | None = None,
) -> HTMXTemplate | Response:
    """Generate and return QR code for a published project.

    Gated by the same rule as the project detail page that embeds it: anyone
    may load a public project, private projects require a project role.
    """
    try:
        project = await DbProject.one(db, project_id)
    except KeyError:
        return Response(
            content=callout("danger", _("Project not found.")),
            media_type="text/html",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    await ensure_project_viewable(db, project, auth_user)

    try:
        qr_data = await project_crud.get_project_qr_data(db, project_id, username)
        app_name = _app_name(project)
        qr_download_name = f"{project.project_name}_{app_name}_{project_id}"
        open_app_url = None
        qfc_signup_url = None
        if (
            project.field_mapping_app == FieldMappingApp.QFIELD
            and project.external_project_id
        ):
            open_app_url = f"qfield://cloud?project={project.external_project_id}"
            qfc_base = strip_qfc_api_suffix(project.external_project_instance_url or "")
            qfc_signup_url = f"{qfc_base}/accounts/signup/" if qfc_base else None
        return HTMXTemplate(
            template_name="partials/project_details/fragments/qr_panel.html",
            context={
                "qr_data": qr_data,
                "qr_download_name": qr_download_name,
                "app_name": app_name,
                "open_app_url": open_app_url,
                "qfc_signup_url": qfc_signup_url,
            },
        )

    except ServiceError as e:
        return Response(
            content=callout(
                "danger",
                _("Error: %(error_msg)s") % {"error_msg": e.message},
            ),
            media_type="text/html",
            status_code=e.status_code,
        )


def _safe_export_filename(project: DbProject) -> str:
    """Build a safe filename stem for the exported GeoJSON download."""
    raw_name = (project.project_name or f"project-{project.id}").strip()
    cleaned = "".join(
        c if c.isalnum() or c in ("-", "_", ".") else "_" for c in raw_name
    )
    cleaned = cleaned.strip("._-") or f"project-{project.id}"
    return f"{cleaned}_export.geojson"


@get(
    path="/projects/{project_id:int}/export/geojson",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def export_project_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    """Trigger a QFieldCloud package, .gpkg --> GeoJSON, then download."""
    project, not_found_response = authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return html_error_response(
            _("GeoJSON export is only available for QField projects."),
            status.HTTP_400_BAD_REQUEST,
        )
    if not project.external_project_id:
        return html_error_response(
            _("This project is not yet linked to a QFieldCloud project."),
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        feature_collection = await export_qfield_project_geojson(db, project)
    except ServiceError as exc:
        return html_error_response(exc.message, exc.status_code)
    except Exception as exc:
        log.exception("GeoJSON export failed for project %s: %s", project_id, exc)
        return html_error_response(
            _("Failed to export GeoJSON: %(error)s") % {"error": exc},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    filename = _safe_export_filename(project)
    return Response(
        content=json.dumps(feature_collection),
        media_type="application/geo+json",
        status_code=status.HTTP_200_OK,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
