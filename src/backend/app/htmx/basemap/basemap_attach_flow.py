"""Basemap attach preconditions and progress responses for HTMX routes."""

from litestar import status_codes as status
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.db.enums import FieldMappingApp, ProjectStatus
from app.db.models import DbProject
from app.helpers.basemap_attach import (
    enqueue_basemap_attach,
    reconcile_missing_basemap_url,
)
from app.i18n import _
from app.qfield.qfield_crud import get_missing_basemap_attach_config

from ..htmx_helpers import callout
from .basemap_fragments import progress_fragment


async def attach_precondition_response(
    db: AsyncConnection, project: DbProject
) -> Response | None:
    """Return the first attach precondition failure response, if any.

    When the stored project has ``basemap_status='ready'`` but no
    ``basemap_url`` (a stale state that can arise from older buggy parsing
    of the upstream tilepack API), this also re-polls the upstream API once
    to self-heal before returning a failure response.
    """
    if project.status != ProjectStatus.PUBLISHED:
        return Response(
            content=callout(
                "warning", _("Basemap attach is available after publication.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return Response(
            content=callout(
                "warning", _("Basemap attach is only available for QField projects.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.basemap_status != "ready":
        return Response(
            content=callout(
                "warning",
                _("Basemap is not ready yet. Please wait for generation to complete."),
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not project.basemap_url:
        recovered_url = await reconcile_missing_basemap_url(db, project)
        if recovered_url:
            project.basemap_url = recovered_url
        else:
            return Response(
                content=callout(
                    "warning",
                    _(
                        "Basemap download URL is not available yet. "
                        "Please refresh status and try again shortly."
                    ),
                ),
                media_type="text/html",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    missing_config = get_missing_basemap_attach_config(project)
    if not missing_config:
        return None

    return Response(
        content=callout(
            "warning",
            _(
                "QField basemap attach is not configured on this deployment. "
                "Missing %(config)s."
            )
            % {"config": ", ".join(missing_config)},
        ),
        media_type="text/html",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def start_basemap_attach(
    db: AsyncConnection, project_id: int, basemap_url: str
) -> Template:
    """Enqueue background attach and render its progress."""
    await enqueue_basemap_attach(db, project_id, basemap_url)
    refreshed_project = await DbProject.one(db, project_id)
    return progress_fragment(refreshed_project, progress_scope="attach")
