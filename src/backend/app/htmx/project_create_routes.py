"""Project creation and form setup HTMX routes."""

from app.htmx.setup_step_routes import (
    create_project_htmx,
    get_template_xlsform,
    new_project,
    upload_xlsform_htmx,
)  # noqa: F401

__all__ = [
    "new_project",
    "create_project_htmx",
    "get_template_xlsform",
    "upload_xlsform_htmx",
]
