"""HTMX routes for project-create submissions."""

# ruff: noqa: D103

import json
import logging
from datetime import datetime, timezone

from litestar import get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.auth.auth_deps import get_user_sub, login_required
from app.db.database import db_conn
from app.db.models import DbProject
from app.helpers.background_tasks import spawn as _spawn_bg_task
from app.i18n import _, get_current_locale
from app.projects import project_schemas
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
    run_simple_project_creation_background as _run_simple_project_creation_background,
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
        await DbProject.update(
            db,
            project.id,
            project_schemas.ProjectUpdate(
                creation_status="in_progress",
                creation_error=None,
                creation_updated_at=datetime.now(timezone.utc),
            ),
        )
        await db.commit()

        _spawn_bg_task(
            _run_simple_project_creation_background(
                project.id,
                outline,
                get_current_locale(),
            ),
            name=f"simple-project-create:{project.id}",
        )

        return _hx_redirect_response(f"/projects/{project.id}/creating")
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


@get(
    path="/projects/{project_id:int}/creating",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def project_creating_page(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    project_id: int,
) -> Template | Response:
    """Full-page placeholder while async creation finalizes in the background."""
    project = await DbProject.one(db, project_id)
    if project and project.creation_status == "ready":
        return _hx_redirect_response(
            f"/projects/{project_id}",
            status_code=status.HTTP_303_SEE_OTHER,
            header_name="Location",
        )
    return HTMXTemplate(
        template_name="new_project_simple_creating.html",
        context={"project": project},
    )


@get(
    path="/projects/{project_id:int}/creation-status",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def project_creation_status(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    project_id: int,
) -> Template | Response:
    """Polling fragment for /projects/{id}/creating; redirects when ready."""
    project = await DbProject.one(db, project_id)
    if project and project.creation_status == "ready":
        return _hx_redirect_response(f"/projects/{project_id}")
    return HTMXTemplate(
        template_name="partials/new_project/creating_fragment.html",
        context={"project": project},
    )


ROUTE_HANDLERS = [
    create_project_htmx,
    create_simple_project_htmx,
    project_creating_page,
    project_creation_status,
]
