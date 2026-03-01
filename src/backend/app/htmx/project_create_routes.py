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

"""Project creation and XLSForm upload HTMX routes."""

import ast
import json
import logging
from io import BytesIO

from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper
from app.central.central_routes import _validate_xlsform_extension
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, XLSFormType
from app.htmx.htmx_schemas import XLSFormUploadData
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    create_project_stub,
    process_xlsform,
)
from app.projects.project_services import (
    ValidationError as SvcValidationError,
)

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


_OUTLINE_JSON_ERROR = (
    "Project area must be valid JSON "
    "(GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection)."
)


def _first_form_value(value: object) -> str:
    """Normalize URL-encoded form values to a stripped string."""
    while isinstance(value, (list, tuple)):
        if not value:
            return ""
        value = next((item for item in value if item not in (None, "")), value[0])

    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    return str(value or "").strip()


def _parse_outline_payload(raw_value: object) -> dict:  # noqa: C901, PLR0911, PLR0912
    """Parse and normalize a GeoJSON outline payload from form data.

    Required for handling str, bytes, list wrapped values etc --> geojson.
    """
    if isinstance(raw_value, dict):
        return raw_value

    value: object = raw_value
    while isinstance(value, (list, tuple)):
        if not value:
            return {}
        value = next((item for item in value if item not in (None, "")), value[0])

    if isinstance(value, dict):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if value is None:
        return {}

    if isinstance(value, str):
        value_str = value.strip()
        if not value_str:
            return {}

        parsed: object | None = None
        try:
            parsed = json.loads(value_str)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(value_str)
            except (SyntaxError, ValueError):
                parsed = None
    else:
        try:
            parsed = json.loads(str(value))
        except (TypeError, ValueError):
            parsed = None

    if isinstance(parsed, dict):
        return parsed

    if isinstance(parsed, (list, tuple)) and len(parsed) == 1:
        return _parse_outline_payload(parsed[0])

    raise ValueError(_OUTLINE_JSON_ERROR)


@get(
    path="/new",
    dependencies={"db": Provide(db_conn)},
)
async def new_project(request: HTMXRequest, db: AsyncConnection) -> Template:
    """Render the new project creation form."""
    return HTMXTemplate(template_name="new_project.html")


async def _get_template_xlsform_bytes(
    form_id: int,
    db: AsyncConnection,
) -> bytes | None:
    """Get template XLSForm bytes by ID from database or osm-fieldwork.

    Returns the bytes if found, None otherwise.
    """
    # First try to get from database
    sql = """
        SELECT title, xls
        FROM template_xlsforms
        WHERE id = %(form_id)s;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"form_id": form_id})
        result = await cur.fetchone()

    if not result:
        return None

    # If XLSForm bytes exist in database, return them
    if result.get("xls"):
        return result["xls"]

    # If not in database, try to get from osm-fieldwork by title
    form_title = result.get("title")
    if form_title:
        try:
            # Map title to XLSFormType enum value
            form_type = None
            for xls_type in XLSFormType:
                if xls_type.value == form_title:
                    form_type = xls_type
                    break

            if form_type:
                form_filename = form_type.name
                form_path = f"{xlsforms_path}/{form_filename}.yaml"
                xlsx_bytes = convert_to_xlsform(str(form_path))
                if xlsx_bytes:
                    return xlsx_bytes
        except Exception as e:
            log.error(f"Error converting YAML to XLSForm: {e}", exc_info=True)

    return None


@get(
    "/template-xlsform/{form_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def get_template_xlsform(
    form_id: int,
    db: AsyncConnection,
) -> Response:
    """Get template XLSForm bytes by ID from database or osm-fieldwork."""
    xlsx_bytes = await _get_template_xlsform_bytes(form_id, db)

    if not xlsx_bytes:
        return Response(
            content="Template XLSForm not found",
            status_code=404,
        )

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=template_{form_id}.xlsx"
        },
    )


@post(
    path="/projects/create",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_project_htmx(  # noqa: C901
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Create a project via HTMX form submission."""
    try:

        def _normalize_field_mapping_app(value: object) -> str:
            if isinstance(value, FieldMappingApp):
                return value.value
            value_str = str(value or "").strip()
            if not value_str:
                return ""
            if "." in value_str:
                value_str = value_str.split(".")[-1]
            normalized = value_str.upper()
            if normalized == "QFIELD":
                return FieldMappingApp.QFIELD.value
            if normalized == "ODK":
                return FieldMappingApp.ODK.value
            return value_str

        project_name = _first_form_value(data.get("project_name", ""))
        description = _first_form_value(data.get("description", ""))
        field_mapping_app = _normalize_field_mapping_app(
            _first_form_value(data.get("field_mapping_app", ""))
        )
        hashtags_str = _first_form_value(data.get("hashtags", ""))

        try:
            outline = _parse_outline_payload(data.get("outline", ""))
        except ValueError:
            return Response(
                content=(
                    '<div id="form-error"'
                    ' style="margin-bottom: 16px;'
                    ' display: block;">'
                    '<wa-callout variant="danger">'
                    '<span id="form-error-message">'
                    f"{_OUTLINE_JSON_ERROR}"
                    "</span></wa-callout></div>"
                ),
                media_type="text/html",
                status_code=400,
            )

        hashtags = (
            [tag.strip() for tag in hashtags_str.split(",") if tag.strip()]
            if hashtags_str
            else []
        )

        project = await create_project_stub(
            db=db,
            project_name=project_name,
            field_mapping_app=field_mapping_app,
            description=description,
            outline=outline,
            hashtags=hashtags,
            user_sub=auth_user.sub,
        )
        await db.commit()

        return Response(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/htmxprojects/{project.id}"},
        )
    except SvcValidationError as e:
        message = e.message
        headers = {}
        if "Description is required" in message:
            headers.update(
                {
                    "HX-Retarget": "#description-error",
                    "HX-Reswap": "innerHTML",
                }
            )
        if "Area of Interest" in message or "too large" in message:
            headers["HX-Trigger"] = json.dumps({"missingOutline": message})
        err_div = (
            '<div id="form-error"'
            ' style="margin-bottom: 16px;'
            ' display: block;">'
            '<wa-callout variant="danger">'
            '<span id="form-error-message">'
            f"{message}"
            "</span></wa-callout></div>"
        )
        return Response(
            content=err_div,
            media_type="text/html",
            status_code=400,
            headers=headers,
        )
    except ConflictError as e:
        err_div = (
            '<div id="form-error"'
            ' style="margin-bottom: 16px;'
            ' display: block;">'
            '<wa-callout variant="danger">'
            '<span id="form-error-message">'
            f"{e.message}"
            "</span></wa-callout></div>"
        )
        hx_trigger = json.dumps({"duplicateProjectName": e.message})
        return Response(
            content=err_div,
            media_type="text/html",
            status_code=status.HTTP_409_CONFLICT,
            headers={"HX-Trigger": hx_trigger},
        )
    except ServiceError as e:
        err_div = (
            '<div id="form-error"'
            ' style="margin-bottom: 16px;'
            ' display: block;">'
            '<wa-callout variant="danger">'
            '<span id="form-error-message">'
            f"{e.message}"
            "</span></wa-callout></div>"
        )
        return Response(
            content=err_div,
            media_type="text/html",
            status_code=400,
        )
    except Exception as e:
        log.error(
            f"Error creating project via HTMX: {e}",
            exc_info=True,
        )
        err_div = (
            '<div id="form-error"'
            ' style="margin-bottom: 16px;'
            ' display: block;">'
            '<wa-callout variant="danger">'
            '<span id="form-error-message">'
            "An unexpected error occurred."
            " Please try again."
            "</span></wa-callout></div>"
        )
        return Response(
            content=err_div,
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/upload-xlsform-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_xlsform_htmx(  # noqa: PLR0911, PLR0913
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: XLSFormUploadData = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    """Upload XLSForm via HTMX form submission."""
    project = current_user.get("project")
    if not project:
        return Response(
            content=_callout("danger", "Project not found."),
            media_type="text/html",
            status_code=404,
        )

    # Verify project_id matches the user's project for security
    if project.id != project_id:
        return Response(
            content=_callout(
                "danger",
                "Project ID mismatch. You do not have access to this project.",
            ),
            media_type="text/html",
            status_code=403,
        )

    # Use project.id from current_user (more secure)
    project_id = project.id

    # Extract form fields from schema with defaults
    xlsform_file = data.xlsform
    need_verification_fields = data.need_verification_fields or "true"
    mandatory_photo_upload = data.mandatory_photo_upload or "false"
    use_odk_collect = data.use_odk_collect or "false"
    default_language = data.default_language or "english"
    template_form_id = data.template_form_id or ""

    # Get form configuration options (convert string to bool)
    need_verification_fields_bool = (
        need_verification_fields.lower() == "true"
        if isinstance(need_verification_fields, str)
        else bool(need_verification_fields)
    )
    mandatory_photo_upload_bool = (
        mandatory_photo_upload.lower() == "true"
        if isinstance(mandatory_photo_upload, str)
        else bool(mandatory_photo_upload)
    )
    use_odk_collect_bool = (
        use_odk_collect.lower() == "true"
        if isinstance(use_odk_collect, str)
        else bool(use_odk_collect)
    )
    template_form_id_str = str(template_form_id) if template_form_id else ""

    try:
        # Handle template form selection
        if template_form_id_str:
            # Fetch template form bytes
            template_bytes = await _get_template_xlsform_bytes(
                int(template_form_id_str),
                db,
            )
            if not template_bytes:
                return Response(
                    content=_callout(
                        "danger",
                        "Failed to load template form.",
                    ),
                    media_type="text/html",
                    status_code=404,
                )

            # Create BytesIO from template bytes (template files are already validated)
            xlsform_bytes = BytesIO(template_bytes)
        else:
            # Handle custom file upload
            if not xlsform_file:
                return Response(
                    content=_callout(
                        "danger",
                        "Please select a form or upload a file.",
                    ),
                    media_type="text/html",
                    status_code=400,
                )
            # Validate and read file bytes
            xlsform_bytes = await _validate_xlsform_extension(xlsform_file)

        # Delegate to shared service function (used by both HTMX and API routes)
        await process_xlsform(
            db=db,
            project_id=project_id,
            xlsform_bytes=xlsform_bytes,
            need_verification_fields=need_verification_fields_bool,
            mandatory_photo_upload=mandatory_photo_upload_bool,
            use_odk_collect=use_odk_collect_bool,
            default_language=default_language,
        )

        # Return success response with HTMX redirect
        return Response(
            content=_callout(
                "success",
                "Form validated and uploaded successfully! Reloading page...",
            ),
            media_type="text/html",
            status_code=200,
            headers={
                "HX-Refresh": "true",  # Reload the page to show updated state
            },
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error uploading XLSForm via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )
