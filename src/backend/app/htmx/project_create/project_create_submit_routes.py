"""HTMX routes for project-create submissions."""

# ruff: noqa: D103

import json
import logging

from litestar import post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import get_user_sub, login_required
from app.db.database import db_conn
from app.i18n import _
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    create_project_stub,
    derive_simple_project_metadata,
)
from app.projects.project_services import ValidationError as SvcValidationError

from ..setup_steps.setup_step_responses import (
    hx_redirect_response as _hx_redirect_response,
)
from ..setup_steps.setup_step_responses import (
    unexpected_error_response as _unexpected_error_response,
)
from .project_create_basemap_orchestration import (
    autostart_basemap_for_simple_project as _autostart_basemap_for_simple_project,
)
from .project_create_parsing import outline_json_error as _outline_json_error
from .project_create_parsing import parse_outline_payload as _parse_outline_payload
from .project_create_parsing import (
    parse_project_create_form as _parse_project_create_form,
)
from .project_create_parsing import project_form_error as _project_form_error
from .project_create_simple_flow import (
    create_simple_project_stub as _create_simple_project_stub,
)
from .project_create_simple_flow import (
    finalize_simple_project_creation as _finalize_simple_project_creation,
)

log = logging.getLogger(__name__)


def _validation_error_response(message: str) -> Response:
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
    return Response(
        content=_project_form_error(message),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


def _conflict_error_response(message: str) -> Response:
    hx_trigger = json.dumps({"duplicateProjectName": message})
    return Response(
        content=_project_form_error(message),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={"HX-Trigger": hx_trigger},
    )


def _service_error_response(message: str) -> Response:
    return Response(
        content=_project_form_error(message),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


@post(
    path="/projects/create",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    try:
        try:
            project_name, description, field_mapping_app, hashtags, outline = (
                _parse_project_create_form(data)
            )
        except ValueError:
            return Response(
                content=_project_form_error(_outline_json_error()),
                media_type="text/html",
                status_code=status.HTTP_200_OK,
            )

        project = await create_project_stub(
            db=db,
            project_name=project_name,
            field_mapping_app=field_mapping_app,
            description=description,
            outline=outline,
            hashtags=hashtags,
            user_sub=get_user_sub(auth_user),
        )
        await db.commit()

        return _hx_redirect_response(f"/projects/{project.id}")
    except SvcValidationError as e:
        return _validation_error_response(e.message)
    except ConflictError as e:
        return _conflict_error_response(e.message)
    except ServiceError as e:
        return _service_error_response(e.message)
    except Exception as e:
        log.error(
            f"Error creating project via HTMX: {e}",
            exc_info=True,
        )
        return _unexpected_error_response(
            _("An unexpected error occurred. Please try again.")
        )


@post(
    path="/projects/create-simple",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_simple_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    try:
        try:
            outline = _parse_outline_payload(data.get("outline", ""))
        except ValueError:
            return Response(
                content=_project_form_error(_outline_json_error()),
                media_type="text/html",
                status_code=status.HTTP_200_OK,
            )

        (
            project_name,
            description,
            hashtags,
            _location_str,
        ) = await derive_simple_project_metadata(db=db, outline=outline)
        project = await _create_simple_project_stub(
            db=db,
            auth_user=auth_user,
            project_name=project_name,
            description=description,
            outline=outline,
            hashtags=hashtags,
        )
        _, headers = await _finalize_simple_project_creation(
            db=db,
            project_id=project.id,
            outline=outline,
            autostart_callback=_autostart_basemap_for_simple_project,
        )

        return _hx_redirect_response(f"/projects/{project.id}", headers=headers)
    except SvcValidationError as e:
        return _validation_error_response(e.message)
    except ConflictError as e:
        return _conflict_error_response(e.message)
    except ServiceError as e:
        return _service_error_response(e.message)
    except Exception as e:
        log.error(
            f"Error creating simple project via HTMX: {e}",
            exc_info=True,
        )
        return _unexpected_error_response(
            _("An unexpected error occurred. Please try again.")
        )


ROUTE_HANDLERS = [
    create_project_htmx,
    create_simple_project_htmx,
]
