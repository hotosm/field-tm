"""HTMX routes for project-create page rendering."""

# ruff: noqa: D103

from litestar import get
from litestar import status_codes as status
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template

from app.auth.auth_deps import get_optional_auth_user
from app.config import AuthProvider, settings

from ..setup_steps.setup_step_responses import (
    hx_redirect_response as _hx_redirect_response,
)
from .project_create_parsing import login_prompt_path as _login_prompt_path


async def _redirect_to_login_if_needed(
    request: HTMXRequest, auth_user: object | None
) -> Response | None:
    if settings.AUTH_PROVIDER == AuthProvider.DISABLED or auth_user is not None:
        return None
    login_path = _login_prompt_path(str(request.url.path))
    if request.headers.get("HX-Request") == "true":
        return _hx_redirect_response(login_path)
    return _hx_redirect_response(
        login_path,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        header_name="Location",
    )


@get(
    path="/new",
    dependencies={
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def new_project(
    request: HTMXRequest, auth_user: object | None
) -> Template | Response:
    """Render standard project-create page or redirect unauthenticated users."""
    login_redirect = await _redirect_to_login_if_needed(request, auth_user)
    if login_redirect:
        return login_redirect
    return HTMXTemplate(template_name="new_project.html")


@get(
    path="/new/simple",
    dependencies={
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def new_project_simple(
    request: HTMXRequest, auth_user: object | None
) -> Template | Response:
    """Render simple project-create page or redirect unauthenticated users."""
    login_redirect = await _redirect_to_login_if_needed(request, auth_user)
    if login_redirect:
        return login_redirect
    return HTMXTemplate(template_name="new_project_simple.html")


ROUTE_HANDLERS = [
    new_project,
    new_project_simple,
]
