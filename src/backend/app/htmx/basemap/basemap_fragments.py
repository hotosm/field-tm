"""Basemap fragment and response builders."""

from litestar import status_codes as status
from litestar.response import Response, Template

from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.i18n import _

from ..htmx_helpers import callout as _callout
from .basemap_formatting import basemap_metadata_url, format_bytes, format_zoom_range


def project_not_found_response() -> Response:
    """Return a consistent 404 response when project context is missing."""
    return Response(
        content=_callout("danger", _("Project not found or access denied.")),
        media_type="text/html",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def basemap_template_context(
    project: DbProject,
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> dict:
    """Build a shared template context for basemap fragments."""
    resolved_minzoom = (
        project.basemap_minzoom if basemap_minzoom is None else basemap_minzoom
    )
    resolved_maxzoom = (
        project.basemap_maxzoom if basemap_maxzoom is None else basemap_maxzoom
    )
    return {
        "project": project,
        "is_qfield": project.field_mapping_app == FieldMappingApp.QFIELD,
        "is_odk": project.field_mapping_app == FieldMappingApp.ODK,
        "basemap_size_bytes": basemap_size_bytes,
        "basemap_minzoom": resolved_minzoom,
        "basemap_maxzoom": resolved_maxzoom,
        "basemap_zoom_display": format_zoom_range(resolved_minzoom, resolved_maxzoom),
        "basemap_metadata_url": basemap_metadata_url(project.basemap_stac_item_id),
    }


def progress_fragment(
    project: DbProject,
    progress_scope: str = "generation",
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> Template:
    """Render progress fragment."""
    is_initially_processing = (
        project.basemap_attach_status == "in_progress"
        if progress_scope == "attach"
        else project.basemap_status == "generating"
    )

    return Template(
        template_name="partials/project_details/fragments/basemap_progress.html",
        context={
            **basemap_template_context(
                project,
                basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
            "progress_scope": progress_scope,
            "is_initially_processing": is_initially_processing,
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def ready_fragment(
    project: DbProject,
    basemap_size_bytes: int | None = None,
    basemap_minzoom: int | None = None,
    basemap_maxzoom: int | None = None,
) -> Template:
    """Render ready fragment."""
    return Template(
        template_name="partials/project_details/fragments/basemap_ready.html",
        context={
            **basemap_template_context(
                project,
                basemap_size_bytes,
                basemap_minzoom=basemap_minzoom,
                basemap_maxzoom=basemap_maxzoom,
            ),
            "basemap_size_display": format_bytes(basemap_size_bytes),
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def attach_status_fragment(project: DbProject) -> Response | Template:
    """Render basemap attach status based on attach lifecycle state."""
    attach_status = project.basemap_attach_status or "idle"

    if attach_status == "in_progress":
        return progress_fragment(project, progress_scope="attach")

    if attach_status == "ready":
        return Response(
            content=_callout(
                "success", _("Basemap attached to QField project successfully.")
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    if attach_status == "failed":
        return progress_fragment(project, progress_scope="attach")

    return Response(
        content=_callout("neutral", _("Basemap attach has not started yet.")),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def search_failure_response() -> Response:
    """Return a sanitized search failure response."""
    return Response(
        content=_callout(
            "danger",
            _("Failed to search imagery right now. Please try again shortly."),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def generation_failure_response() -> Response:
    """Return a sanitized generation failure response."""
    return Response(
        content=_callout(
            "danger",
            _(
                "Failed to start basemap generation right now. "
                "Please try again shortly."
            ),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def status_failure_response() -> Response:
    """Return a sanitized status failure response."""
    return Response(
        content=_callout(
            "danger",
            _("Failed to refresh basemap status right now. Please try again shortly."),
        ),
        media_type="text/html",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
