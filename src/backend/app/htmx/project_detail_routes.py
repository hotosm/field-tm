"""Project detail and QR HTMX routes."""

from app.htmx.setup_step_routes import (  # noqa: F401
    project_details,
    project_qrcode_htmx,
)

__all__ = ["project_details", "project_qrcode_htmx"]
