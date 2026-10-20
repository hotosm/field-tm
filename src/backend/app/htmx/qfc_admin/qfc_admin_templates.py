"""Rendering helpers for QFieldCloud admin HTMX routes."""

import html
import json

from app.i18n import _

COLLABORATOR_ROLES = [
    ("admin", _("Admin")),
    ("manager", _("Manager")),
    ("editor", _("Editor")),
    ("reporter", _("Reporter")),
    ("reader", _("Reader")),
]


def hidden_fields_html(qfc_url: str, qfc_token: str, qfc_username: str) -> str:
    """Return hidden input elements that carry QFC state between requests."""
    username = html.escape(qfc_username)
    return (
        f'<input type="hidden" name="qfc_url" value="{html.escape(qfc_url)}" />'
        f'<input type="hidden" name="qfc_token" value="{html.escape(qfc_token)}" />'
        f'<input type="hidden" name="qfc_username" value="{username}" />'
    )


def role_badge_variant(role: str) -> str:
    """Map a QFC collaborator role to a wa-badge variant."""
    return {
        "admin": "danger",
        "manager": "warning",
        "editor": "brand",
        "reporter": "neutral",
        "reader": "neutral",
    }.get(role, "neutral")


def render_management_area(
    qfc_url: str,
    token: str,
    username: str,
    projects: list,
    base_url: str,
) -> str:
    """Build the full management area HTML returned after login."""
    hidden = hidden_fields_html(qfc_url, token, username)

    header = f"""
<div class="wa-split wa-gap-m">
  <div>
    <h2 class="ftm-section-title">{_("QFieldCloud Projects")}</h2>
    <p class="ftm-hint">
      {_("Connected as")} <strong>{html.escape(username)}</strong>
      {_("to")} <code>{html.escape(base_url)}</code>
    </p>
  </div>
  <wa-button variant="neutral" appearance="outlined" size="small"
    onclick="document.getElementById('qfc-management').innerHTML='';
             document.getElementById('qfc-login-panel').style.display='block';">
    {_("Log Out")}
  </wa-button>
</div>"""

    if not projects:
        table = f'<p class="ftm-hint">{_("No projects found.")}</p>'
    else:
        rows = []
        for p in projects:
            pid = html.escape(str(p.get("id", "")))
            name = html.escape(str(p.get("name", "Untitled")))
            owner = html.escape(str(p.get("owner", "")))
            desc = html.escape(str(p.get("description", ""))[:80])
            visibility = (
                f'<wa-badge variant="success">{_("Public")}</wa-badge>'
                if p.get("is_public", False)
                else f'<wa-badge variant="neutral">{_("Private")}</wa-badge>'
            )
            rows.append(f"""
<tr id="qfc-project-row-{pid}">
  <td><strong>{name}</strong></td>
  <td><code>{owner}</code></td>
  <td>{visibility}</td>
  <td class="ftm-hint">{desc}</td>
  <td>
    <form hx-get="/qfc-admin/projects/{pid}/collaborators"
          hx-target="#qfc-collabs-{pid}" hx-swap="innerHTML">
      {hidden}
      <wa-button variant="neutral" appearance="outlined" size="small"
        type="submit">{_("Manage")}</wa-button>
    </form>
  </td>
</tr>
<tr><td colspan="5" id="qfc-collabs-{pid}" class="ftm-qfc-collabs-cell"></td></tr>""")

        table = f"""
<div class="ftm-table-scroll">
  <table class="wa-hover-rows">
    <thead>
      <tr><th>{_("Project")}</th><th>{_("Owner")}</th><th>{_("Visibility")}</th><th>{_("Description")}</th><th></th></tr>
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


def render_collaborators_panel(
    qfc_url: str,
    token: str,
    username: str,
    project_id: str,
    collaborators: list,
) -> str:
    """Build the collaborator management panel HTML."""
    hidden = hidden_fields_html(qfc_url, token, username)
    pid_e = html.escape(project_id)
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
                    {
                        "qfc_url": qfc_url,
                        "qfc_token": token,
                        "qfc_username": username,
                    }
                )
            )

            collab_rows.append(f"""
<tr id="qfc-collab-{pid_e}-{uname}">
  <td><strong>{uname}</strong></td>
  <td>
    <wa-badge variant="{role_badge_variant(role)}">
      {html.escape(role.title())}
    </wa-badge>
  </td>
  <td class="wa-cluster wa-gap-xs">
    <form hx-patch="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
          hx-target="#{target_id}" hx-swap="innerHTML"
          class="wa-cluster wa-gap-xs">
      {hidden}
      <select name="role">
        {role_options}
      </select>
      <wa-button variant="neutral" appearance="outlined" size="small"
        type="submit">{_("Update")}</wa-button>
    </form>
    <wa-button variant="danger" appearance="outlined" size="small"
      onclick="document.getElementById('{dialog_id}').show()">{_("Remove")}</wa-button>
  </td>
</tr>""")

            dialogs.append(f"""
<wa-dialog id="{dialog_id}" label="{_("Remove Collaborator")}" with-header>
  <p>
    {_("Remove")} <strong>{uname}</strong> {_("from this project?")}
  </p>
  <div slot="footer" class="wa-cluster">
    <wa-button variant="neutral" appearance="outlined"
      onclick="document.getElementById('{dialog_id}').hide()">{_("Cancel")}</wa-button>
    <wa-button variant="danger"
      hx-delete="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
      hx-target="#{target_id}" hx-swap="innerHTML"
      hx-vals="{hx_vals}">{_("Remove")}</wa-button>
  </div>
</wa-dialog>""")

        collab_table = f"""
<table>
  <thead><tr><th>{_("User")}</th><th>{_("Role")}</th><th>{_("Actions")}</th></tr></thead>
  <tbody>{"".join(collab_rows)}</tbody>
</table>"""
    else:
        collab_table = f'<p class="ftm-hint">{_("No collaborators yet.")}</p>'

    role_options_add = "".join(
        f'<option value="{r}"{"selected" if r == "editor" else ""}>{label}</option>'
        for r, label in COLLABORATOR_ROLES
    )
    add_form = f"""
<form hx-post="/qfc-admin/projects/{pid_e}/collaborators"
      hx-target="#{target_id}" hx-swap="innerHTML"
      class="wa-cluster wa-gap-xs">
    {hidden}
    <wa-input name="new_username" placeholder="{_("Username")}" size="small"
              required></wa-input>
    <select name="new_role">
      {role_options_add}
    </select>
    <wa-button variant="brand" size="small" type="submit">
      {_("Add Collaborator")}
    </wa-button>
</form>"""

    close_btn = f"""
<div class="wa-split">
  <h3 class="ftm-section-title">{_("Collaborators")}</h3>
  <wa-button variant="neutral" appearance="plain" size="small"
    onclick="document.getElementById('{target_id}').innerHTML=''">{_("Close")}</wa-button>
</div>"""

    return f"""<div class="ftm-panel ftm-panel--quiet wa-stack">
  {close_btn}
  {collab_table}
  {add_form}
</div>{"".join(dialogs)}"""
