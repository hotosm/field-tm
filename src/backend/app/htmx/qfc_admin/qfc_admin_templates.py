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
        "editor": "primary",
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
<div class="ftm-flex-between" style="margin-bottom:1.5rem">
  <div>
    <h2 class="ftm-section-title" style="margin:0">{_("QFieldCloud Projects")}</h2>
    <p
      style="margin:4px 0 0;color:var(--ftm-text-muted);
             font-size:var(--hot-font-size-small)"
    >
      {_("Connected as")} <strong>{html.escape(username)}</strong>
      {_("to")} <code>{html.escape(base_url)}</code>
    </p>
  </div>
  <wa-button variant="default" size="small"
    onclick="document.getElementById('qfc-management').innerHTML='';
             document.getElementById('qfc-login-panel').style.display='block';">
    {_("Log Out")}
  </wa-button>
</div>"""

    if not projects:
        table = f'<p style="color:var(--ftm-text-muted)">{_("No projects found.")}</p>'
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
      <wa-button variant="default" size="small" type="submit">{_("Manage")}</wa-button>
    </form>
  </td>
</tr>
<tr><td colspan="5" id="qfc-collabs-{pid}" class="ftm-qfc-collabs-cell"></td></tr>""")

        table = f"""
<div style="overflow-x:auto">
  <table class="ftm-qfc-table">
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
  <td style="font-weight:var(--hot-font-weight-semibold)">{uname}</td>
  <td>
    <wa-badge variant="{role_badge_variant(role)}">
      {html.escape(role.title())}
    </wa-badge>
  </td>
  <td class="ftm-qfc-collab-actions">
    <form hx-patch="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
          hx-target="#{target_id}" hx-swap="innerHTML"
          style="display:inline-flex;gap:0.5rem;align-items:center">
      {hidden}
      <select
        name="role"
        class="ftm-projects-filter__select"
        style="width:auto;min-width:6rem"
      >
        {role_options}
      </select>
      <wa-button variant="default" size="small" type="submit">{_("Update")}</wa-button>
    </form>
    <wa-button variant="danger" size="small" outline
      onclick="document.getElementById('{dialog_id}').show()">{_("Remove")}</wa-button>
  </td>
</tr>""")

            dialogs.append(f"""
<wa-dialog id="{dialog_id}" label="{_("Remove Collaborator")}" with-header>
  <p style="margin:0;line-height:1.6">
    {_("Remove")} <strong>{uname}</strong> {_("from this project?")}
  </p>
  <div slot="footer" class="ftm-flex-end">
    <wa-button variant="default"
      onclick="document.getElementById('{dialog_id}').hide()">{_("Cancel")}</wa-button>
    <wa-button variant="danger"
      hx-delete="/qfc-admin/projects/{pid_e}/collaborators/{uname}"
      hx-target="#{target_id}" hx-swap="innerHTML"
      hx-vals="{hx_vals}">{_("Remove")}</wa-button>
  </div>
</wa-dialog>""")

        collab_table = f"""
<table class="ftm-qfc-table ftm-qfc-table--nested">
  <thead><tr><th>{_("User")}</th><th>{_("Role")}</th><th>{_("Actions")}</th></tr></thead>
  <tbody>{"".join(collab_rows)}</tbody>
</table>"""
    else:
        collab_table = (
            '<p style="color:var(--ftm-text-muted);'
            f'font-size:var(--hot-font-size-small)">{_("No collaborators yet.")}</p>'
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
    <wa-input name="new_username" placeholder="{_("Username")}" size="small"
              required style="flex:1;min-width:8rem"></wa-input>
    <select
      name="new_role"
      class="ftm-projects-filter__select"
      style="width:auto;min-width:6rem"
    >
      {role_options_add}
    </select>
    <wa-button variant="primary" size="small" type="submit">
      {_("Add Collaborator")}
    </wa-button>
  </form>
</div>"""

    close_btn = f"""
<div style="text-align:right;margin-bottom:0.5rem">
  <wa-button variant="default" size="small"
    onclick="document.getElementById('{target_id}').innerHTML=''">{_("Close")}</wa-button>
</div>"""

    return f"""<div class="ftm-qfc-collab-panel">
  {close_btn}
  <h4
    style="margin:0 0 0.75rem;font-family:var(--hot-font-sans-variant-condensed)"
  >{_("Collaborators")}</h4>
  {collab_table}
  {add_form}
</div>{"".join(dialogs)}"""
