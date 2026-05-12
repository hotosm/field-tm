"""Basemap attach preconditions and background orchestration."""

import asyncio
import logging
from datetime import datetime, timezone

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.config import settings
from app.db.enums import FieldMappingApp, ProjectStatus
from app.db.models import DbProject
from app.helpers.basemap_services import check_tilepack_status
from app.i18n import _
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_crud import (
    attach_basemap_to_qfield_project,
    get_missing_basemap_attach_config,
)

from ..htmx_helpers import callout as _callout
from .basemap_fragments import progress_fragment

log = logging.getLogger(__name__)
AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS = 8
AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS = 1


def contains_transient_attach_fragment(value: str) -> bool:
    """Return whether text contains a retryable transient-network fragment."""
    text = value.lower()
    return any(fragment in text for fragment in _TRANSIENT_ATTACH_FRAGMENTS)


def next_exception(exc: Exception) -> Exception | None:
    """Return the next chained exception when present."""
    next_exc = exc.__cause__ or exc.__context__
    return next_exc if isinstance(next_exc, Exception) else None


def is_transient_attach_exception(exc: Exception) -> bool:
    """Return True when an attach exception looks temporary and retryable."""
    if isinstance(exc, TimeoutError):
        return True

    current: Exception | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if contains_transient_attach_fragment(str(current)):
            return True

        if isinstance(current, HTTPException):
            detail = current.detail if isinstance(current.detail, str) else ""
            if contains_transient_attach_fragment(detail):
                return True

        current = next_exception(current)

    return False


def attach_error_text(exc: Exception) -> str:
    """Return a concise user-facing attach failure message."""
    fallback_message = _(
        "Basemap attach failed for now. Your project is ready to use. "
        "Please retry attach."
    )

    transient_message = _(
        "Basemap attach could not complete due to a temporary network issue. "
        "Your project is ready to use. Please retry attach."
    )

    if is_transient_attach_exception(exc):
        return transient_message

    return fallback_message


async def reconcile_missing_basemap_url(
    db: AsyncConnection, project: DbProject
) -> str | None:
    """Re-poll tilepack status when stored state lacks a URL; persist if found."""
    stac_item_id = str(project.basemap_stac_item_id or "").strip()
    if not stac_item_id:
        return None

    try:
        status_value, download_url = await check_tilepack_status(stac_item_id)
    except Exception:
        log.exception("Tilepack status reconcile failed for project %s", project.id)
        return None

    if not (status_value == "ready" and download_url):
        return None

    await DbProject.update(
        db,
        project.id,
        ProjectUpdate(basemap_status="ready", basemap_url=download_url),
    )
    await db.commit()
    return download_url


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
            content=_callout(
                "warning", _("Basemap attach is available after publication.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return Response(
            content=_callout(
                "warning", _("Basemap attach is only available for QField projects.")
            ),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if project.basemap_status != "ready":
        return Response(
            content=_callout(
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
                content=_callout(
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
        content=_callout(
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


async def run_basemap_attach_background(project_id: int, basemap_url: str) -> None:
    """Run heavy basemap attach flow in background and persist terminal state."""
    await asyncio.sleep(AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS)
    now = datetime.now(timezone.utc)

    for attempt in range(AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS + 1):
        try:
            async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
                project = await DbProject.one(db, project_id)
                await attach_basemap_to_qfield_project(db, project, basemap_url)
                await DbProject.update(
                    db,
                    project_id,
                    ProjectUpdate(
                        basemap_attach_status="ready",
                        basemap_attach_error=None,
                        basemap_attach_updated_at=now,
                    ),
                )
                await db.commit()
                return
        except Exception as exc:
            is_last_attempt = attempt >= AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS
            retryable = is_transient_attach_exception(exc)
            if retryable and not is_last_attempt:
                log.warning(
                    "Basemap attach transient failure for project %s; retrying once",
                    project_id,
                    exc_info=exc,
                )
                continue

            log.exception("Basemap attach failed for project %s", project_id)
            error_text = attach_error_text(exc)
            async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
                await DbProject.update(
                    db,
                    project_id,
                    ProjectUpdate(
                        basemap_attach_status="failed",
                        basemap_attach_error=error_text,
                        basemap_attach_updated_at=now,
                    ),
                )
                await db.commit()
            return


async def start_basemap_attach(
    db: AsyncConnection, project_id: int, basemap_url: str
) -> Template:
    """Mark attach as in progress, enqueue background work, and render progress."""
    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            basemap_attach_status="in_progress",
            basemap_attach_error=None,
            basemap_attach_updated_at=datetime.now(timezone.utc),
        ),
    )
    await db.commit()

    asyncio.create_task(run_basemap_attach_background(project_id, basemap_url))

    refreshed_project = await DbProject.one(db, project_id)
    return progress_fragment(refreshed_project, progress_scope="attach")


async def enqueue_autostart_attach(
    db: AsyncConnection, project_id: int, basemap_url: str
) -> None:
    """Flip a pending-autostart project to in-progress and enqueue attach.

    Used when a manual basemap status poll discovers the tilepack is ready
    and the project was reserved for simple-flow autostart attach.
    """
    await DbProject.update(
        db,
        project_id,
        ProjectUpdate(
            basemap_attach_status="in_progress",
            basemap_attach_error=None,
            basemap_attach_updated_at=datetime.now(timezone.utc),
        ),
    )
    await db.commit()

    asyncio.create_task(run_basemap_attach_background(project_id, basemap_url))


_TRANSIENT_ATTACH_FRAGMENTS = (
    "name or service not known",
    "temporary failure in name resolution",
    "failed to resolve",
    "dns",
    "timed out",
    "timeout",
    "connection reset",
    "connection refused",
    "connection aborted",
    "temporarily unavailable",
    "temporary failure",
    "network is unreachable",
    "protocolerror",
)
