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
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.auth.auth_deps import (
    get_optional_auth_user,
    get_user_is_admin,
    get_user_sub,
)
from app.central import central_crud
from app.config import decrypt_value
from app.db.database import db_conn
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.i18n import _
from app.projects import project_crud
from app.projects.project_services import (
    DownstreamDeleteError,
    NotFoundError,
    delete_project_with_downstream,
)

from .htmx_helpers import callout as _callout

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
) -> str:
    """Build the QR code HTML payload."""
    scan_qr_code = _("Scan QR Code")
    scan_description = _(
        "Use %(app_name)s to scan this QR code and load the project."
    ) % {"app_name": app_name}
    project_qr_code = _("Project QR Code")
    download_qr_code = _("Download QR Code")
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
) -> Template:
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
    return Response(
        content="",
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={"HX-Redirect": "/projects"},
    )


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
        html_content = _qrcode_panel_html(
            qr_code_data_url,
            qr_download_name,
            app_name,
            _mapper_credentials_html(project),
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
    except Exception as e:
        log.error(f"Error generating QR code via HTMX: {e}", exc_info=True)
        return Response(
            content=_callout("warning", _friendly_qr_error(e)),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
