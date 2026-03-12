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

import html
import json
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

from app.config import settings
from app.qfield.qfield_crud import add_qfc_project_collaborator

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)

# ── Roles available in the collaborator dropdown ────────────────────────
COLLABORATOR_ROLES = [
    ("admin", "Admin"),
    ("manager", "Manager"),
    ("editor", "Editor"),
    ("reporter", "Reporter"),
    ("reader", "Reader"),
]


# ── Helpers ─────────────────────────────────────────────────────────────


def _qfc_client(url: str, token: str) -> Client:
    """Build an authenticated QFieldCloud SDK client from raw values."""
    return Client(url=url, token=token)


def _strip_api_suffix(url: str) -> str:
    """Strip /api/v1/ suffix from a QFC URL to get the base domain."""
    url = url.rstrip("/")
    if url.endswith("/api/v1"):
        url = url[: -len("/api/v1")]
    return url


def _normalise_qfc_url(url: str) -> str:
    """Ensure a QFC URL ends with /api/v1/."""
    url = url.rstrip("/")
    if not url.endswith("/api/v1"):
        url = f"{url}/api/v1"
    return f"{url}/"


def _resolve_login_qfc_url(submitted_url: str) -> str:
    """Use the configured QFC URL when the submitted URL looks local."""
    qfc_url = _normalise_qfc_url(submitted_url)
    configured_url = str(settings.QFIELDCLOUD_URL or "").strip()
    if not configured_url:
        return qfc_url

    if "localhost" in qfc_url or "field-tm.dev.test" in qfc_url:
        return _normalise_qfc_url(configured_url)

    return qfc_url


def _hidden_fields_html(qfc_url: str, qfc_token: str) -> str:
    """Return hidden input elements that carry QFC state between requests."""
    return (
        f'<input type="hidden" name="qfc_url" value="{html.escape(qfc_url)}" />'
        f'<input type="hidden" name="qfc_token" value="{html.escape(qfc_token)}" />'
    )


def _friendly_add_collaborator_error(exc: Exception) -> str:
    """Map verbose QFC collaborator errors to user-friendly messages."""
    msg = str(exc).lower()
    if "does not exist" in msg:
        return "This user does not exist. Please create it first."
    if "already exists" in msg:
        return "This user is already a collaborator on this project."
    return f"Failed to add collaborator: {exc}"


def _org_membership_permission_error(organization: str) -> str:
    """Return a clear error when the user cannot manage org members."""
    return (
        f"This project belongs to the {organization} organization. "
        f"The user must be added to that organization before they can be "
        f"added as a collaborator. Your QFieldCloud account does not have "
        f"permission to manage organization members."
    )


def _role_badge_variant(role: str) -> str:
    """Map a QFC collaborator role to a wa-badge variant."""
    return {
        "admin": "danger",
        "manager": "warning",
        "editor": "primary",
        "reporter": "neutral",
        "reader": "neutral",
    }.get(role, "neutral")


# ── Page render ─────────────────────────────────────────────────────────


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
            content=_callout("danger", "All fields are required."),
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
                content=_callout("danger", "Login succeeded but no token received."),
                media_type="text/html",
            )
    except Exception as exc:
        log.debug("QFC login failed: %s", exc)
        return Response(
            content=_callout(
                "danger",
                "Login failed. Check your URL and credentials.",
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
        content=_render_management_area(qfc_url, token, username, projects),
        media_type="text/html",
    )


def _render_management_area(
    qfc_url: str,
    token: str,
    username: str,
    projects: list,
) -> str:
    """Build the full management area HTML returned after login."""
    hidden = _hidden_fields_html(qfc_url, token)
    base_url = _strip_api_suffix(qfc_url)

    header = f"""
<div class="ftm-flex-between" style="margin-bottom:1.5rem">
  <div>
    <h2 class="ftm-section-title" style="margin:0">QFieldCloud Projects</h2>
    <p
      style="margin:4px 0 0;color:var(--ftm-text-muted);
             font-size:var(--hot-font-size-small)"
    >
      Connected as <strong>{html.escape(username)}</strong>
      to <code>{html.escape(base_url)}</code>
    </p>
  </div>
  <wa-button variant="default" size="small"
    onclick="document.getElementById('qfc-management').innerHTML='';
             document.getElementById('qfc-login-panel').style.display='block';">
    Log Out
  </wa-button>
</div>"""

    if not projects:
        table = '<p style="color:var(--ftm-text-muted)">No projects found.</p>'
    else:
        rows = []
        for p in projects:
            pid = html.escape(str(p.get("id", "")))
            name = html.escape(str(p.get("name", "Untitled")))
            owner = html.escape(str(p.get("owner", "")))
            desc = html.escape(str(p.get("description", ""))[:80])
            visibility = (
                '<wa-badge variant="success">Public</wa-badge>'
                if p.get("is_public", False)
                else '<wa-badge variant="neutral">Private</wa-badge>'
            )
            rows.append(f"""
<tr class="ftm-qfc-project-row" id="qfc-project-row-{pid}">
  <td style="font-weight:var(--hot-font-weight-semibold)">{name}</td>
  <td><code style="font-size:0.8em">{owner}</code></td>
  <td>{visibility}</td>
  <td
    style="color:var(--ftm-text-muted);font-size:var(--hot-font-size-small)"
  >{desc}</td>
  <td>
    <form hx-get="/qfc-admin/projects/{pid}/collaborators"
          hx-target="#qfc-collabs-{pid}" hx-swap="innerHTML">
      {hidden}
      <wa-button variant="default" size="small" type="submit">Manage</wa-button>
    </form>
  </td>
</tr>
<tr><td colspan="5" id="qfc-collabs-{pid}" class="ftm-qfc-collabs-cell"></td></tr>""")

        table = f"""
<div style="overflow-x:auto">
  <table class="ftm-qfc-table">
    <thead>
      <tr><th>Project</th><th>Owner</th><th>Visibility</th><th>Description</th><th></th></tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""

    return (
        header
        + table
        + "\n<script>"
        + "document.getElementById('qfc-login-panel').style.display='none';"
        + "</script>"
    )


# ── Collaborator management ─────────────────────────────────────────────


@get(path="/qfc-admin/projects/{project_id:str}/collaborators")
async def list_collaborators(
    request: HTMXRequest,
    project_id: str,
    qfc_url: str = Parameter(query="qfc_url", default=""),
    qfc_token: str = Parameter(query="qfc_token", default=""),
) -> Response:
    """List collaborators for a QFC project."""
    # HTMX sends form data as query params on GET
    if not qfc_url or not qfc_token:
        return Response(
            content=_callout("danger", "Session expired. Please log in again."),
            media_type="text/html",
        )

    loop = get_running_loop()
    try:
        client = _qfc_client(qfc_url, qfc_token)
        collaborators = await loop.run_in_executor(
            None, partial(client.get_project_collaborators, project_id)
        )
        # Get project details (to know the owner for org membership)
        project = await loop.run_in_executor(
            None, partial(client.get_project, project_id)
        )
    except Exception as exc:
        log.warning("QFC list collaborators failed: %s", exc)
        return Response(
            content=_callout("warning", f"Could not load collaborators: {exc}"),
            media_type="text/html",
        )

    owner = project.get("owner", "")

    return Response(
        content=_render_collaborators_panel(
            qfc_url, qfc_token, project_id, owner, collaborators
        ),
        media_type="text/html",
    )


def _render_collaborators_panel(
    qfc_url: str,
    token: str,
    project_id: str,
    owner: str,
    collaborators: list,
) -> str:
    """Build the collaborator management panel HTML."""
    hidden = _hidden_fields_html(qfc_url, token)
    pid_e = html.escape(project_id)
    owner_e = html.escape(owner)
    target_id = f"qfc-collabs-{pid_e}"

    dialogs = []

    if collaborators:
        collab_rows = []
        for c in collaborators:
            uname = html.escape(str(c.get("collaborator", "")))
            role = str(c.get("role", "reader"))
            role_options = "".join(
                (
                    f'<option value="{r}" {"selected" if r == role else ""}>'
                    f"{label}</option>"
                )
                for r, label in COLLABORATOR_ROLES
            )
            dialog_id = f"qfc-rm-{pid_e}-{uname}"
            hx_vals = html.escape(
                json.dumps(
                    {"qfc_url": qfc_url, "qfc_token": token, "project_owner": owner}
                )
            )

            collab_rows.append(f"""
<tr id="qfc-collab-{pid_e}-{uname}">
  <td style="font-weight:var(--hot-font-weight-semibold)">{uname}</td>
  <td>
    <wa-badge variant="{_role_badge_variant(role)}">
      {html.escape(role.title())}
    </wa-badge>
  </td>
  <td class="ftm-qfc-collab-actions">
    <form hx-patch="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
          hx-target="#{target_id}" hx-swap="innerHTML"
          style="display:inline-flex;gap:0.5rem;align-items:center">
      {hidden}
      <input type="hidden" name="project_owner" value="{owner_e}" />
      <select
        name="role"
        class="ftm-projects-filter__select"
        style="width:auto;min-width:6rem"
      >
        {role_options}
      </select>
      <wa-button variant="default" size="small" type="submit">Update</wa-button>
    </form>
    <wa-button variant="danger" size="small" outline
      onclick="document.getElementById('{dialog_id}').show()">Remove</wa-button>
  </td>
</tr>""")

            dialogs.append(f"""
<wa-dialog id="{dialog_id}" label="Remove Collaborator" with-header>
  <p style="margin:0;line-height:1.6">
    Remove <strong>{uname}</strong> from this project?
  </p>
  <div slot="footer" class="ftm-flex-end">
    <wa-button variant="default"
      onclick="document.getElementById('{dialog_id}').hide()">Cancel</wa-button>
    <wa-button variant="danger"
      hx-delete="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
      hx-target="#{target_id}" hx-swap="innerHTML"
      hx-vals="{hx_vals}">Remove</wa-button>
  </div>
</wa-dialog>""")

        collab_table = f"""
<table class="ftm-qfc-table ftm-qfc-table--nested">
  <thead><tr><th>User</th><th>Role</th><th>Actions</th></tr></thead>
  <tbody>{"".join(collab_rows)}</tbody>
</table>"""
    else:
        collab_table = (
            '<p style="color:var(--ftm-text-muted);'
            'font-size:var(--hot-font-size-small)">No collaborators yet.</p>'
        )

    role_options_add = "".join(
        f'<option value="{r}"{"selected" if r == "editor" else ""}>{label}</option>'
        for r, label in COLLABORATOR_ROLES
    )
    add_form = f"""
<div class="ftm-qfc-add-collab">
  <form hx-post="/qfc-admin/projects/{pid_e}/collaborators"
        hx-target="#{target_id}" hx-swap="innerHTML"
        class="ftm-qfc-add-collab-form">
    {hidden}
    <input type="hidden" name="project_owner" value="{owner_e}" />
    <wa-input name="new_username" placeholder="Username" size="small"
              required style="flex:1;min-width:8rem"></wa-input>
    <select
      name="new_role"
      class="ftm-projects-filter__select"
      style="width:auto;min-width:6rem"
    >
      {role_options_add}
    </select>
    <wa-button variant="primary" size="small" type="submit">Add Collaborator</wa-button>
  </form>
</div>"""

    close_btn = f"""
<div style="text-align:right;margin-bottom:0.5rem">
  <wa-button variant="default" size="small"
    onclick="document.getElementById('{target_id}').innerHTML=''">Close</wa-button>
</div>"""

    return f"""<div class="ftm-qfc-collab-panel">
  {close_btn}
  <h4
    style="margin:0 0 0.75rem;font-family:var(--hot-font-sans-variant-condensed)"
  >Collaborators</h4>
  {collab_table}
  {add_form}
</div>{"".join(dialogs)}"""


@post(path="/qfc-admin/projects/{project_id:str}/collaborators", status_code=status.HTTP_200_OK)
async def add_collaborator(
    request: HTMXRequest,
    project_id: str,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Add a collaborator to a QFC project."""
    qfc_url = data.get("qfc_url", "")
    qfc_token = data.get("qfc_token", "")
    username = (data.get("new_username") or "").strip()
    role_str = data.get("new_role", "editor")
    owner = data.get("project_owner", "")

    if not username:
        return Response(
            content=_callout("danger", "Username is required."),
            media_type="text/html",
        )

    role = ProjectCollaboratorRole(role_str)
    loop = get_running_loop()

    try:
        client = _qfc_client(qfc_url, qfc_token)
        # Set username so org-ownership check works correctly
        client.username = owner
        await add_qfc_project_collaborator(client, project_id, username, role)
    except Exception as exc:
        log.warning("QFC add collaborator failed: %s", exc)
        detail = getattr(exc, "detail", None) or _friendly_add_collaborator_error(exc)
        return Response(
            content=_callout("danger", detail),
            media_type="text/html",
        )

    # Re-render the full collaborator panel
    return await _reload_collaborators(loop, client, project_id, qfc_url, qfc_token)


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

    loop = get_running_loop()
    try:
        client = _qfc_client(qfc_url, qfc_token)
        await loop.run_in_executor(
            None,
            partial(client.remove_project_collaborator, project_id, username),
        )
    except Exception as exc:
        log.warning("QFC remove collaborator failed: %s", exc)
        return Response(
            content=_callout("danger", f"Failed to remove collaborator: {exc}"),
            media_type="text/html",
        )

    return await _reload_collaborators(loop, client, project_id, qfc_url, qfc_token)


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
    role_str = data.get("role", "editor")

    role = ProjectCollaboratorRole(role_str)
    loop = get_running_loop()

    try:
        client = _qfc_client(qfc_url, qfc_token)
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
            content=_callout("danger", f"Failed to update collaborator: {exc}"),
            media_type="text/html",
        )

    return await _reload_collaborators(loop, client, project_id, qfc_url, qfc_token)


async def _reload_collaborators(
    loop, client: Client, project_id: str, qfc_url: str, qfc_token: str
) -> Response:
    """Re-fetch collaborators and return the full panel HTML."""
    try:
        collaborators = await loop.run_in_executor(
            None, partial(client.get_project_collaborators, project_id)
        )
        project = await loop.run_in_executor(
            None, partial(client.get_project, project_id)
        )
        owner = project.get("owner", "")
    except Exception as exc:
        return Response(
            content=_callout("warning", f"Collaborator refresh failed: {exc}"),
            media_type="text/html",
        )

    return Response(
        content=_render_collaborators_panel(
            qfc_url, qfc_token, project_id, owner, collaborators
        ),
        media_type="text/html",
    )


