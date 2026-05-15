"""HTMX routes for project-create XLSForm endpoints."""

# ruff: noqa: D103, PLR0911

import logging

from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import mapper
from app.db.database import db_conn
from app.htmx.htmx_schemas import XLSFormUploadData
from app.i18n import _
from app.projects.project_services import ServiceError, process_xlsform
from app.projects.project_services import ValidationError as SvcValidationError

from ..htmx_helpers import callout as _callout
from ..setup_steps.setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)
from ..setup_steps.setup_step_responses import (
    service_error_response as _service_error_response,
)
from ..setup_steps.setup_step_responses import (
    unexpected_error_response as _unexpected_error_response,
)
from .project_create_parsing import to_bool_form_value as _to_bool_form_value
from .project_create_templates import (
    get_template_xlsform_bytes as _get_template_xlsform_bytes,
)
from .project_create_templates import (
    resolve_uploaded_xlsform_bytes as _resolve_uploaded_xlsform_bytes,
)

log = logging.getLogger(__name__)


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
    xlsx_bytes = await _get_template_xlsform_bytes(form_id, db)

    if not xlsx_bytes:
        return Response(
            content="Template XLSForm not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=template_{form_id}.xlsx"
        },
    )


@post(
    path="/upload-xlsform-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_xlsform_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: XLSFormUploadData = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    project_id = project.id

    need_verification_fields_bool = _to_bool_form_value(
        data.need_verification_fields, default=True
    )
    include_photo_upload_bool = _to_bool_form_value(
        data.include_photo_upload, default=True
    )
    mandatory_photo_upload_bool = _to_bool_form_value(
        data.mandatory_photo_upload, default=False
    )
    use_odk_collect_bool = _to_bool_form_value(data.use_odk_collect, default=False)
    default_language_explicit = _to_bool_form_value(
        data.default_language_explicit, default=False
    )
    default_language = data.default_language if default_language_explicit else None

    try:
        xlsform_bytes, error_response = await _resolve_uploaded_xlsform_bytes(data, db)
        if error_response:
            return error_response

        await process_xlsform(
            db=db,
            project_id=project_id,
            xlsform_bytes=xlsform_bytes,
            need_verification_fields=need_verification_fields_bool,
            include_photo_upload=include_photo_upload_bool,
            mandatory_photo_upload=mandatory_photo_upload_bool,
            use_odk_collect=use_odk_collect_bool,
            default_language=default_language,
        )

        return Response(
            content=_callout(
                "success",
                _("Form validated and uploaded successfully! Reloading page..."),
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return _service_error_response(e)
    except ServiceError as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(f"Error uploading XLSForm via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


ROUTE_HANDLERS = [
    get_template_xlsform,
    upload_xlsform_htmx,
]
