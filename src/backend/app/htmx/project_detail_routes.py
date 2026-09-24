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
from html import escape

from litestar import delete, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response
from psycopg import AsyncConnection
from qfieldcloud_sdk.sdk import ProjectCollaboratorRole

from app.auth.auth_deps import (
    get_optional_auth_user,
    get_user_is_admin,
    get_user_sub,
    login_required,
)
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import check_access, project_manager
from app.central import central_crud
from app.config import decrypt_value
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, ProjectRole
from app.db.models import DbProject
from app.i18n import _
from app.projects import project_crud
from app.projects.project_services import (
    DownstreamDeleteError,
    NotFoundError,
    delete_project_with_downstream,
)
from app.qfield.qfield_crud import (
    add_qfc_project_collaborator,
    export_qfield_project_geojson,
)
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_utils import is_default_qfc_instance_url

from .htmx_helpers import callout as _callout
from .setup_steps.setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)
from .setup_steps.setup_step_responses import (
    html_error_response as _html_error_response,
)
from .setup_steps.setup_step_responses import (
    hx_redirect_response as _hx_redirect_response,
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


def _mapper_credentials_html(project: DbProject) -> str:
    """Render QField mapper credentials when they are available."""
    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return ""

    mapper_username = project.external_project_username
    mapper_password = None
    if project.external_project_password_encrypted:
        with suppress(Exception):
            mapper_password = decrypt_value(project.external_project_password_encrypted)

    if not (mapper_username and mapper_password):
        return ""

    return f"""
            <div class="ftm-qr-panel__mapper-creds" style="
                margin-top: 16px;
                padding: 12px 16px;
                background: #f5f5f5;
                border-radius: 8px;
            ">
                <h4 style="margin: 0 0 8px 0; font-size: 0.95em;">
                    {_("Mapper Login (QFieldCloud)")}
                </h4>
                <p style="margin: 0; font-size: 0.9em;">
                    <strong>{_("Username:")}</strong> <code>{mapper_username}</code>
                </p>
                <p style="margin: 4px 0 0 0; font-size: 0.9em;">
                    <strong>{_("Password:")}</strong> <code>{mapper_password}</code>
                </p>
                <p style="margin: 8px 0 0 0; font-size: 0.8em; color: #666;">
                    {_("Scan the QR code, then enter these credentials in QField.")}
                </p>
            </div>"""


def _qrcode_panel_html(
    qr_code_data_url: str,
    qr_download_name: str,
    app_name: str,
    mapper_creds_html: str,
    open_app_url: str | None = None,
) -> str:
    """Build the QR code HTML payload."""
    scan_qr_code = _("Scan QR Code")
    scan_description = _(
        "Use %(app_name)s to scan this QR code and load the project."
    ) % {"app_name": app_name}
    project_qr_code = _("Project QR Code")
    download_qr_code = _("Download QR Code")
    open_button_html = ""
    if open_app_url:
        open_in_app = _("Open in %(app_name)s") % {"app_name": app_name}
        open_hint = _("If %(app_name)s is installed on this device.") % {
            "app_name": app_name
        }
        open_button_html = f"""
                <wa-button
                    href="{open_app_url}"
                    variant="brand"
                >
                    {open_in_app}
                </wa-button>
                <p style="margin: 6px 0 12px 0; font-size: 0.8em; color: #666;">
                    {open_hint}
                </p>
        """
    return f"""
        <div class="ftm-qr-panel">
            <h3 class="ftm-qr-panel__title">{scan_qr_code}</h3>
            <p class="ftm-qr-panel__description">
                {scan_description}
            </p>
            <div class="ftm-qr-panel__image-wrap">
                <img
                    src="{qr_code_data_url}"
                    alt="{project_qr_code}"
                    class="ftm-qr-panel__image"
                />
            </div>
            <div>
                {open_button_html}
                <wa-button
                    onclick="downloadQRCode('{qr_code_data_url}', '{qr_download_name}')"
                    variant="default"
                >
                    {download_qr_code}
                </wa-button>
            </div>
            {mapper_creds_html}
        </div>
        <script>
            if (typeof window.downloadQRCode !== "function") {{
                window.downloadQRCode = function downloadQRCode(dataUrl, filename) {{
                    const link = document.createElement("a");
                    link.href = dataUrl;
                    link.download = filename + ".png";
                    link.click();
                }};
            }}
        </script>
        """


def _friendly_qr_error(exc: Exception) -> str:
    """Map low-level QR generation failures to a user-friendly message."""
    raw = str(exc).lower()
    if any(
        kw in raw
        for kw in (
            "connection",
            "connect",
            "refused",
            "timeout",
            "unreachable",
            "network",
        )
    ):
        return _(
            "Cannot reach the mapping server. "
            "Check that ODK Central or QFieldCloud is running."
        )
    if any(kw in raw for kw in ("500", "server error", "internal")):
        return _("The mapping server returned an error. Check its logs for details.")
    if any(kw in raw for kw in ("401", "403", "unauthorized", "forbidden")):
        return _(
            "Authentication failed connecting to the mapping server. "
            "Check the configured credentials."
        )
    return _("An unexpected error occurred while generating the QR code.")


def _show_qfc_collaborator_form(project: DbProject) -> bool:
    """Whether to show the QFieldCloud collaborator form on project details."""
    return (
        project.field_mapping_app == FieldMappingApp.QFIELD
        and bool(project.external_project_id)
        and is_default_qfc_instance_url(project.external_project_instance_url)
    )


async def _show_assignment_panel(
    db: AsyncConnection, auth_user: object | None, project: DbProject
) -> bool:
    """Whether the viewer may see the manager-gated task assignment panel.

    Mirrors the project_manager gate on the panel routes so non-managers
    viewing a published project never trigger the lazy load (the global
    htmx config would swap the 4xx auth error into the panel slot).
    """
    if auth_user is None:
        return False
    with suppress(Exception):
        return bool(
            await check_access(
                auth_user,
                db,
                project_id=project.id,
                role=ProjectRole.PROJECT_ADMIN,
            )
        )
    return False


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
        form_templates = []
        if not project.xlsform_content:
            form_templates = await central_crud.get_form_list(db)
        return HTMXTemplate(
            template_name="project_details.html",
            context={
                "project": project,
                "form_templates_json": json.dumps(form_templates),
                "can_delete_project": _can_delete_project(auth_user, project),
                "show_qfc_collaborator_form": _show_qfc_collaborator_form(project),
                "show_assignment_panel": await _show_assignment_panel(
                    db, auth_user, project
                ),
            },
        )
    except KeyError:
        # Project not found
        return HTMXTemplate(
            template_name="project_details.html",
            context={
                "project": None,
                "form_templates_json": "[]",
                "can_delete_project": False,
                "show_qfc_collaborator_form": False,
                "show_assignment_panel": False,
            },
        )


@delete(
    path="/projects/{project_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
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
            content=_callout("danger", exc.message),
            media_type="text/html",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    await db.commit()
    return _hx_redirect_response("/projects")


@get(
    path="/project-qrcode-htmx",
    dependencies={
        "db": Provide(db_conn),
    },
)
async def project_qrcode_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int = Parameter(),
    username: str = Parameter(default="fieldtm_user"),
) -> Response:
    """Generate and return QR code for a published project."""
    try:
        project = await DbProject.one(db, project_id)
    except KeyError:
        return Response(
            content=_callout("danger", _("Project not found.")),
            media_type="text/html",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        # Use CRUD function to generate QR code
        qr_code_data_url = await project_crud.get_project_qrcode(
            db, project_id, username
        )
        app_name = _app_name(project)
        qr_download_name = f"{project.project_name}_{app_name}_{project_id}"
        open_app_url = None
        if (
            project.field_mapping_app == FieldMappingApp.QFIELD
            and project.external_project_id
        ):
            open_app_url = f"qfield://cloud?project={project.external_project_id}"
        html_content = _qrcode_panel_html(
            qr_code_data_url,
            qr_download_name,
            app_name,
            _mapper_credentials_html(project),
            open_app_url=open_app_url,
        )
        return Response(
            content=html_content,
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as e:
        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        return Response(
            content=_callout(
                "danger",
                _("Error: %(error_msg)s") % {"error_msg": error_msg},
            ),
            media_type="text/html",
            status_code=e.status_code,
        )


def _parse_collaborator_usernames(raw: str) -> list[str]:
    """Parse a comma-separated list of QFieldCloud usernames."""
    seen: set[str] = set()
    usernames: list[str] = []
    for piece in (raw or "").split(","):
        name = piece.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        usernames.append(name)
    return usernames


def _render_collaborator_result(
    project_id: int,
    *,
    added: list[str],
    failed: list[tuple[str, str]],
) -> str:
    """Build the post-submit result panel for the collaborator form."""
    blocks: list[str] = []
    if added:
        names = ", ".join(added)
        success_msg = _(
            "Added the following user(s) as project editors: %(names)s."
        ) % {"names": names}
        blocks.append(_callout("success", success_msg))
    for username, reason in failed:
        msg = _("Could not add '%(username)s': %(reason)s") % {
            "username": username,
            "reason": reason,
        }
        blocks.append(_callout("danger", msg))

    add_more_label = escape(_("Add more collaborators"), quote=True)
    refresh_button = (
        f'<wa-button type="button" variant="default" size="small" '
        f'hx-get="/projects/{project_id}/qfc-collaborator-form" '
        f'hx-target="#qfc-collaborator-section" hx-swap="outerHTML" '
        f'style="margin-top:8px">{add_more_label}</wa-button>'
    )
    inner = "".join(blocks) + refresh_button
    return f'<div id="qfc-collaborator-section">{inner}</div>'


def _render_collaborator_form(project_id: int, *, error_msg: str | None = None) -> str:
    """Render the QFieldCloud collaborator form on the project details page."""
    heading = escape(_("Invite QFieldCloud collaborators"), quote=True)
    step_intro = escape(
        _(
            "Mappers must have an account on QFieldCloud before you can give "
            "them access to this project."
        ),
        quote=True,
    )
    step_create = _(
        "Have each mapper create a free account at "
        '<a href="https://app.qfield.cloud" target="_blank" rel="noopener" '
        'class="ftm-link--brand">app.qfield.cloud</a>.'
    )
    step_enter = escape(
        _(
            "Enter their QFieldCloud usernames below (comma-separated for "
            "multiple users) and click submit. They will be added as editors "
            "and can log in to QField to start mapping."
        ),
        quote=True,
    )
    placeholder = escape(_("e.g. alice, bob, charlie"), quote=True)
    submit_label = escape(_("Add collaborators"), quote=True)

    error_html = (
        f'<div style="margin-bottom:8px">{_callout("danger", error_msg)}</div>'
        if error_msg
        else ""
    )

    return (
        f'<div id="qfc-collaborator-section" class="ftm-qfc-collab">'
        f'<div class="ftm-qfc-collab__panel">'
        f'<h3 class="ftm-qfc-collab__title">{heading}</h3>'
        f'<ol class="ftm-qfc-collab__steps">'
        f"<li>{step_intro}</li>"
        f"<li>{step_create}</li>"
        f"<li>{step_enter}</li>"
        f"</ol>"
        f"{error_html}"
        f'<form hx-post="/projects/{project_id}/qfc-collaborators" '
        f'hx-target="#qfc-collaborator-section" hx-swap="outerHTML" '
        f'class="ftm-qfc-collab__form">'
        f'<wa-input name="qfc_usernames" placeholder="{placeholder}" required '
        f'class="ftm-qfc-collab__input"></wa-input>'
        f'<wa-button type="submit" variant="brand">{submit_label}</wa-button>'
        f"</form>"
        f"</div>"
        f"</div>"
    )


@get(
    path="/projects/{project_id:int}/qfc-collaborator-form",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def qfc_collaborator_form_htmx(
    request: HTMXRequest,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    """Re-render the QFieldCloud collaborator form (e.g. after submit)."""
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    if not _show_qfc_collaborator_form(project):
        return Response(
            content='<div id="qfc-collaborator-section"></div>',
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    return Response(
        content=_render_collaborator_form(project_id),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


@post(
    path="/projects/{project_id:int}/qfc-collaborators",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def add_qfc_collaborators_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Add one or more QFieldCloud users as editors on the given project."""
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    usernames = _parse_collaborator_usernames(data.get("qfc_usernames") or "")
    if not usernames:
        return Response(
            content=_render_collaborator_form(
                project_id, error_msg=_("Enter at least one QFieldCloud username.")
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    project = await DbProject.one(db, project_id)
    qfc_project_id = project.external_project_id
    if not qfc_project_id:
        return _html_error_response(
            _("QFieldCloud project ID not found for this project."),
            status.HTTP_400_BAD_REQUEST,
        )
    if not is_default_qfc_instance_url(project.external_project_instance_url):
        return _html_error_response(
            _(
                "This project was created on a custom QFieldCloud instance. "
                "Use the QFieldCloud Admin tab to manage collaborators."
            ),
            status.HTTP_400_BAD_REQUEST,
        )

    added: list[str] = []
    failed: list[tuple[str, str]] = []
    async with qfield_client() as client:
        for username in usernames:
            try:
                await add_qfc_project_collaborator(
                    client,
                    str(qfc_project_id),
                    username,
                    ProjectCollaboratorRole.EDITOR,
                )
            except HTTPException as exc:
                failed.append((username, str(exc.detail)))
            except Exception as exc:
                log.warning("QFC add collaborator failed for '%s': %s", username, exc)
                failed.append((username, str(exc)))
            else:
                added.append(username)

    return Response(
        content=_render_collaborator_result(project_id, added=added, failed=failed),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
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
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return _html_error_response(
            _("GeoJSON export is only available for QField projects."),
            status.HTTP_400_BAD_REQUEST,
        )
    if not project.external_project_id:
        return _html_error_response(
            _("This project is not yet linked to a QFieldCloud project."),
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        feature_collection = await export_qfield_project_geojson(db, project)
    except HTTPException as exc:
        return _html_error_response(str(exc.detail), exc.status_code)
    except Exception as exc:
        log.exception("GeoJSON export failed for project %s: %s", project_id, exc)
        return _html_error_response(
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
