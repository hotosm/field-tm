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

import logging

from litestar import get
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.db.database import db_conn
from app.db.models import DbProject
from app.projects import project_crud

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


@get(
    path="/htmxprojects/{project_id:int}",
    dependencies={"db": Provide(db_conn)},
)
async def project_details(
    request: HTMXRequest,
    db: AsyncConnection,
    project_id: int,
) -> Template:
    """Render project details page."""
    try:
        project = await DbProject.one(db, project_id)
        return HTMXTemplate(
            template_name="project_details.html", context={"project": project}
        )
    except KeyError:
        # Project not found
        return HTMXTemplate(
            template_name="project_details.html", context={"project": None}
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
            content=_callout("danger", "Project not found."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Use CRUD function to generate QR code
        qr_code_data_url = await project_crud.get_project_qrcode(
            db, project_id, username
        )

        app_name = (
            project.field_mapping_app.value
            if hasattr(project.field_mapping_app, "value")
            else str(project.field_mapping_app)
        )

        qr_download_name = f"{project.project_name}_{app_name}_{project_id}"
        html_content = f"""
        <div class="ftm-qr-panel">
            <h3 class="ftm-qr-panel__title">Scan QR Code</h3>
            <p class="ftm-qr-panel__description">
                Use {app_name} to scan this QR code and load the project.
            </p>
            <div class="ftm-qr-panel__image-wrap">
                <img
                    src="{qr_code_data_url}"
                    alt="Project QR Code"
                    class="ftm-qr-panel__image"
                />
            </div>
            <div>
                <wa-button
                    onclick="downloadQRCode('{qr_code_data_url}', '{qr_download_name}')"
                    variant="default"
                >
                    Download QR Code
                </wa-button>
            </div>
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

        return Response(
            content=html_content,
            media_type="text/html",
            status_code=200,
        )

    except HTTPException as e:
        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=e.status_code,
        )
    except Exception as e:
        log.error(f"Error generating QR code via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )
