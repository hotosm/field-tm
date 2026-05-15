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

"""QFieldCloud admin panel - HTMX routes for managing projects & collaborators.

All state is kept client-side: the QFC auth token and API URL are passed
as hidden form fields with every HTMX request.  The server never stores
credentials or sessions.
"""

import logging
from asyncio import get_running_loop
from functools import partial
from typing import Optional

from litestar import Response, delete, get, patch, post
from litestar import status_codes as status
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Template
from qfieldcloud_sdk.sdk import Client, ProjectCollaboratorRole

from app.i18n import _
from app.qfield.qfield_crud import add_qfc_project_collaborator
from app.qfield.qfield_utils import resolve_backend_qfc_url, strip_qfc_api_suffix

from ..htmx_helpers import callout as _callout
from .qfc_admin_templates import (
    render_collaborators_panel as _render_collaborators_panel,
)
from .qfc_admin_templates import render_management_area as _render_management_area

log = logging.getLogger(__name__)

# ── Helpers ─────────────────────────────────────────────────────────────


def _qfc_client(url: str, token: str) -> Client:
    """Build an authenticated QFieldCloud SDK client from raw values."""
    return Client(url=url, token=token)


def _strip_api_suffix(url: str) -> str:
    """Strip /api/v1/ suffix from a QFC URL to get the base domain."""
    return strip_qfc_api_suffix(url)


def _resolve_login_qfc_url(submitted_url: str) -> str:
    """Use shared backend URL resolution policy for login API calls."""
    return resolve_backend_qfc_url(submitted_url)


def _friendly_add_collaborator_error(exc: Exception) -> str:
    """Map verbose QFC collaborator errors to user-friendly messages."""
    msg = str(exc).lower()
    if "does not exist" in msg:
        return _("This user does not exist. Please create it first.")
    if "already exists" in msg:
        return _("This user is already a collaborator on this project.")
    return _("Failed to add collaborator: %(exc)s") % {"exc": exc}


@get(path="/qfc-admin")
async def qfc_admin_page(
    request: HTMXRequest,
    url: Optional[str] = Parameter(query="url", default=None),
) -> Template:
    """Render the QFC admin page with login form."""
    return HTMXTemplate(
        template_name="qfc_admin.html",
        context={"prefill_url": _strip_api_suffix(url) if url else ""},
    )


# ── Login & project listing ─────────────────────────────────────────────


@post(path="/qfc-admin/login", status_code=status.HTTP_200_OK)
async def qfc_admin_login(
    request: HTMXRequest,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Validate QFC credentials and return the project list."""
    qfc_url_raw = (data.get("qfc_url") or "").strip()
    username = (data.get("qfc_username") or "").strip()
    password = (data.get("qfc_password") or "").strip()

    if not all([qfc_url_raw, username, password]):
        return Response(
            content=_callout("danger", _("All fields are required.")),
            media_type="text/html",
        )

    qfc_url = _resolve_login_qfc_url(qfc_url_raw)
    loop = get_running_loop()

    try:
        client = await loop.run_in_executor(None, partial(Client, url=qfc_url))
        result = await loop.run_in_executor(
            None, partial(client.login, username, password)
        )
        token = result.get("token", client.token)
        if not token:
            return Response(
                content=_callout("danger", _("Login succeeded but no token received.")),
                media_type="text/html",
            )
    except Exception as exc:
        log.debug("QFC login failed: %s", exc)
        return Response(
            content=_callout(
                "danger",
                _("Login failed. Check your URL and credentials."),
            ),
            media_type="text/html",
        )

    # Fetch projects
    try:
        projects = await loop.run_in_executor(None, partial(client.list_projects))
    except Exception as exc:
        log.warning("QFC list_projects failed: %s", exc)
        projects = []

    return Response(
        content=_render_management_area(
            qfc_url,
            token,
            username,
            projects,
            base_url=_strip_api_suffix(qfc_url),
        ),
        media_type="text/html",
    )


# ── Collaborator management ─────────────────────────────────────────────


@get(path="/qfc-admin/projects/{project_id:str}/collaborators")
async def list_collaborators(
    request: HTMXRequest,
    project_id: str,
    qfc_url: str = Parameter(query="qfc_url", default=""),
    qfc_token: str = Parameter(query="qfc_token", default=""),
    qfc_username: str = Parameter(query="qfc_username", default=""),
) -> Response:
    """List collaborators for a QFC project."""
    # HTMX sends form data as query params on GET
    if not qfc_url or not qfc_token:
        return Response(
            content=_callout("danger", _("Session expired. Please log in again.")),
            media_type="text/html",
        )

    loop = get_running_loop()
    try:
        client = _qfc_client(qfc_url, qfc_token)
        collaborators = await loop.run_in_executor(
            None, partial(client.get_project_collaborators, project_id)
        )
    except Exception as exc:
        log.warning("QFC list collaborators failed: %s", exc)
        return Response(
            content=_callout(
                "warning",
                _("Could not load collaborators: %(exc)s") % {"exc": exc},
            ),
            media_type="text/html",
        )

    return Response(
        content=_render_collaborators_panel(
            qfc_url, qfc_token, qfc_username, project_id, collaborators
        ),
        media_type="text/html",
    )


@post(
    path="/qfc-admin/projects/{project_id:str}/collaborators",
    status_code=status.HTTP_200_OK,
)
async def add_collaborator(
    request: HTMXRequest,
    project_id: str,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Add a collaborator to a QFC project."""
    qfc_url = data.get("qfc_url", "")
    qfc_token = data.get("qfc_token", "")
    qfc_username = data.get("qfc_username", "")
    username = (data.get("new_username") or "").strip()
    role_str = data.get("new_role", "editor")

    if not username:
        return Response(
            content=_callout("danger", _("Username is required.")),
            media_type="text/html",
        )

    role = ProjectCollaboratorRole(role_str)
    loop = get_running_loop()

    try:
        client = _qfc_client(qfc_url, qfc_token)
        # Set the authenticated QFC user so org-owned project handling works.
        client.username = qfc_username
        await add_qfc_project_collaborator(client, project_id, username, role)
    except Exception as exc:
        log.warning("QFC add collaborator failed: %s", exc)
        detail = getattr(exc, "detail", None) or _friendly_add_collaborator_error(exc)
        return Response(
            content=_callout("danger", detail),
            media_type="text/html",
        )

    # Re-render the full collaborator panel
    return await _reload_collaborators(
        loop, client, project_id, qfc_url, qfc_token, qfc_username
    )


@delete(
    path="/qfc-admin/projects/{project_id:str}/collaborators/{username:str}",
    status_code=200,
)
async def remove_collaborator(
    request: HTMXRequest,
    project_id: str,
    username: str,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Remove a collaborator from a QFC project."""
    qfc_url = data.get("qfc_url", "")
    qfc_token = data.get("qfc_token", "")
    qfc_username = data.get("qfc_username", "")

    loop = get_running_loop()
    try:
        client = _qfc_client(qfc_url, qfc_token)
        client.username = qfc_username
        await loop.run_in_executor(
            None,
            partial(client.remove_project_collaborator, project_id, username),
        )
    except Exception as exc:
        log.warning("QFC remove collaborator failed: %s", exc)
        return Response(
            content=_callout(
                "danger",
                _("Failed to remove collaborator: %(exc)s") % {"exc": exc},
            ),
            media_type="text/html",
        )

    return await _reload_collaborators(
        loop, client, project_id, qfc_url, qfc_token, qfc_username
    )


@patch(path="/qfc-admin/projects/{project_id:str}/collaborators/{username:str}")
async def update_collaborator(
    request: HTMXRequest,
    project_id: str,
    username: str,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Change a collaborator's role."""
    qfc_url = data.get("qfc_url", "")
    qfc_token = data.get("qfc_token", "")
    qfc_username = data.get("qfc_username", "")
    role_str = data.get("role", "editor")

    role = ProjectCollaboratorRole(role_str)
    loop = get_running_loop()

    try:
        client = _qfc_client(qfc_url, qfc_token)
        client.username = qfc_username
        await loop.run_in_executor(
            None,
            partial(
                client.patch_project_collaborators,
                project_id,
                username,
                role,
            ),
        )
    except Exception as exc:
        log.warning("QFC update collaborator failed: %s", exc)
        return Response(
            content=_callout(
                "danger",
                _("Failed to update collaborator: %(exc)s") % {"exc": exc},
            ),
            media_type="text/html",
        )

    return await _reload_collaborators(
        loop, client, project_id, qfc_url, qfc_token, qfc_username
    )


async def _reload_collaborators(
    loop,
    client: Client,
    project_id: str,
    qfc_url: str,
    qfc_token: str,
    qfc_username: str,
) -> Response:
    """Re-fetch collaborators and return the full panel HTML."""
    try:
        collaborators = await loop.run_in_executor(
            None, partial(client.get_project_collaborators, project_id)
        )
    except Exception as exc:
        return Response(
            content=_callout(
                "warning",
                _("Collaborator refresh failed: %(exc)s") % {"exc": exc},
            ),
            media_type="text/html",
        )

    return Response(
        content=_render_collaborators_panel(
            qfc_url, qfc_token, qfc_username, project_id, collaborators
        ),
        media_type="text/html",
    )


ROUTE_HANDLERS = [
    qfc_admin_page,
    qfc_admin_login,
    list_collaborators,
    add_collaborator,
    remove_collaborator,
    update_collaborator,
]
