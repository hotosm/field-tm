"""HTMX routes for setup-step project finalization workflow."""

# ruff: noqa: D103

import logging
from html import escape

from litestar import post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection
from qfieldcloud_sdk.sdk import ProjectCollaboratorRole

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager
from app.central.central_schemas import ODKCentral
from app.db.database import db_conn
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.i18n import _
from app.projects.project_services import (
    ServiceError,
    finalize_odk_project,
    finalize_qfield_project,
)
from app.projects.project_services import ValidationError as SvcValidationError
from app.qfield.qfield_crud import add_qfc_project_collaborator
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud
from app.qfield.qfield_utils import is_default_qfc_instance_url

from ..htmx_helpers import callout as _callout
from ..setup_steps.setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)
from ..setup_steps.setup_step_responses import (
    build_odk_finalize_success_html as _build_odk_finalize_success_html,
)
from ..setup_steps.setup_step_responses import (
    build_qfield_finalize_success_html as _build_qfield_finalize_success_html,
)
from ..setup_steps.setup_step_responses import (
    finalize_error_response as _finalize_error_response,
)
from ..setup_steps.setup_step_responses import (
    html_error_response as _html_error_response,
)

log = logging.getLogger(__name__)


@post(
    path="/create-project-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    project_type = project.field_mapping_app
    if project_type == FieldMappingApp.ODK:
        return await create_project_odk_htmx.fn(
            request=request,
            db=db,
            current_user=current_user,
            auth_user=auth_user,
            project_id=project_id,
            data=data,
        )
    if project_type == FieldMappingApp.QFIELD:
        return await create_project_qfield_htmx.fn(
            request=request,
            db=db,
            current_user=current_user,
            auth_user=auth_user,
            project_id=project_id,
            data=data,
        )

    return _html_error_response(
        _("Project mapping app is not configured for finalisation."),
        status.HTTP_400_BAD_REQUEST,
    )


@post(
    path="/create-project-odk-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_odk_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        custom_odk_creds = None
        external_url = data.get("external_project_instance_url", "").strip()
        external_username = data.get("external_project_username", "").strip()
        external_password = data.get("external_project_password", "").strip()

        any_custom = any([external_url, external_username, external_password])
        all_custom = all([external_url, external_username, external_password])

        if any_custom and not all_custom:
            custom_creds_msg = _(
                "Provide ODK URL, username, and password (all 3), or leave "
                "them all blank to use server defaults."
            )
            return Response(
                content=_callout("warning", custom_creds_msg),
                media_type="text/html",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if all_custom:
            custom_odk_creds = ODKCentral(
                external_project_instance_url=external_url,
                external_project_username=external_username,
                external_project_password=external_password,
            )

        odk_result = await finalize_odk_project(
            db=db, project_id=project_id, custom_odk_creds=custom_odk_creds
        )

        return _build_odk_finalize_success_html(odk_result, project_id=project_id)
    except ServiceError as e:
        status_code = (
            status.HTTP_400_BAD_REQUEST
            if isinstance(e, SvcValidationError)
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return _finalize_error_response(e.message, status_code)
    except Exception as e:
        log.error(f"Error creating ODK project via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else e
        return _finalize_error_response(
            error_msg, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@post(
    path="/create-project-qfield-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_qfield_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        custom_qfield_creds = None
        qfield_url_param = data.get("qfield_cloud_url", "").strip()
        qfield_user = data.get("qfield_cloud_user", "").strip()
        qfield_password = data.get("qfield_cloud_password", "").strip()
        qfield_org = data.get("qfield_cloud_org", "").strip() or None

        if qfield_url_param and qfield_user and qfield_password:
            custom_qfield_creds = QFieldCloud(
                qfield_cloud_url=qfield_url_param,
                qfield_cloud_user=qfield_user,
                qfield_cloud_password=qfield_password,
                qfield_cloud_org=qfield_org,
            )
        qfield_result = await finalize_qfield_project(
            db=db, project_id=project_id, custom_qfield_creds=custom_qfield_creds
        )

        return _build_qfield_finalize_success_html(qfield_result, project_id=project_id)
    except SvcValidationError as e:
        return _finalize_error_response(e.message, status.HTTP_400_BAD_REQUEST)
    except ServiceError as e:
        return _finalize_error_response(
            e.message, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except HTTPException as e:
        return _finalize_error_response(e.detail, e.status_code)
    except Exception as e:
        log.error(f"Error creating QField project via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else e
        return _finalize_error_response(
            error_msg, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _render_collaborator_form(project_id: int, error_msg: str | None = None) -> str:
    collaborator_prompt = escape(
        _("Enter your username to add yourself as a project collaborator (editor)."),
        quote=True,
    )
    title = escape(_("Already have an account on QFieldCloud?"), quote=True)
    username_placeholder = escape(_("QFieldCloud username"), quote=True)
    submit_label = escape(_("Add collaborator"), quote=True)
    error_html = (
        f'<div style="margin-bottom:8px">{_callout("danger", error_msg)}</div>'
        if error_msg
        else ""
    )
    return (
        f'<div id="qfc-collaborator-box" '
        f'style="margin-top:12px;padding:16px;background-color:#f5f5f5;'
        f'border-radius:8px">'
        f"{error_html}"
        f'<form hx-post="/create-project-htmx/{project_id}/qfc-collaborator" '
        f'hx-target="#qfc-collaborator-box" hx-swap="outerHTML" '
        f'style="display:flex;flex-direction:column;gap:8px">'
        f'<h4 style="margin:0">{title}</h4>'
        f'<p style="margin:0;color:#666">{collaborator_prompt}</p>'
        f'<div style="display:flex;gap:8px;align-items:flex-end">'
        f'<wa-input name="qfc_username" placeholder="{username_placeholder}" '
        f'required style="flex:1"></wa-input>'
        f'<wa-button type="submit" variant="brand">'
        f"{submit_label}</wa-button>"
        f"</div></form></div>"
    )


def _custom_qfc_collaborator_error() -> str:
    return _(
        "This project was created on a custom QFieldCloud instance. "
        "Use the QFieldCloud Admin tab to manage collaborators."
    )


@post(
    path="/create-project-htmx/{project_id:int}/qfc-collaborator",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def add_qfc_collaborator_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    username = (data.get("qfc_username") or "").strip()
    if not username:
        return Response(
            content=_render_collaborator_form(project_id, _("Username is required.")),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    project = await DbProject.one(db, project_id)
    qfc_project_id = project.external_project_id
    error_response = None
    if not qfc_project_id:
        error_response = _html_error_response(
            _("QFieldCloud project ID not found for this project."),
            status.HTTP_400_BAD_REQUEST,
        )
    elif not is_default_qfc_instance_url(project.external_project_instance_url):
        error_response = _html_error_response(
            _custom_qfc_collaborator_error(),
            status.HTTP_400_BAD_REQUEST,
        )
    if error_response:
        return error_response

    try:
        async with qfield_client() as client:
            await add_qfc_project_collaborator(
                client,
                str(qfc_project_id),
                username,
                ProjectCollaboratorRole.EDITOR,
            )
    except HTTPException as exc:
        return Response(
            content=_render_collaborator_form(project_id, str(exc.detail)),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        log.warning("QFC add collaborator (post-finalize) failed: %s", exc)
        return Response(
            content=_render_collaborator_form(
                project_id,
                _("Failed to add collaborator: %(exc)s") % {"exc": exc},
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    success_msg = _(
        "Added '%(username)s' as an editor. "
        "Visit the QFieldCloud Admin tab to add more collaborators "
        "or manage the project."
    ) % {"username": username}
    return Response(
        content=_callout("success", success_msg),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


ROUTE_HANDLERS = [
    create_project_htmx,
    create_project_odk_htmx,
    create_project_qfield_htmx,
    add_qfc_collaborator_htmx,
]
