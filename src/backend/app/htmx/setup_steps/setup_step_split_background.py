"""Background-task helper for the advanced HTMX split flow.

The split SQL (especially the alignment step over thousands of task
polygons) routinely exceeds both the BunkerWeb 90s proxy budget and the
splitter's default 270s per-statement timeout for large AOIs. Running the
split inline behind an HTTP request meant large projects always timed out.

This helper runs ``split_aoi`` on a fresh DB connection inside an asyncio
background task with ``statement_timeout_ms=0`` (no DB cap), persists the
proposed result (or error) into the ``projects`` row, and lets the
frontend poll for completion. Mirrors the pattern used by the simple
project creation flow.

Status is implicit in the two columns it writes:
    split_result_geojson set -> ready
    split_error set          -> failed
    both NULL                -> still running
"""

import logging

from psycopg import AsyncConnection

from app.config import settings
from app.db.models import DbProject
from app.i18n import _
from app.projects import project_schemas
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    SplitAoiOptions,
    split_aoi,
)
from app.projects.project_services import ValidationError as SvcValidationError

log = logging.getLogger(__name__)


async def run_split_aoi_background(project_id: int, options: SplitAoiOptions) -> None:
    """Run the splitter for ``project_id`` and persist its terminal state.

    Always opens a brand-new DB connection (the parent request's
    connection has already been released). On failure, opens a second
    fresh connection to write the error so a poisoned transaction can't
    block the status update.
    """
    options.statement_timeout_ms = 0
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
            tasks_featcol = await split_aoi(db, project_id, options)
            # "" rather than None — ProjectUpdate strips Nones via
            # exclude_none=True so we can't write SQL NULL through the
            # schema. "" reads the same as NULL ("no error") in the
            # status endpoint.
            await DbProject.update(
                db,
                project_id,
                project_schemas.ProjectUpdate(
                    split_error="",
                    split_result_geojson=tasks_featcol or {},
                ),
            )
            await db.commit()
            return
    except (SvcValidationError, ConflictError, ServiceError) as exc:
        error_message = exc.message
    except Exception:
        log.exception("Unexpected error splitting AOI for project %s", project_id)
        error_message = _("An unexpected error occurred. Please try again.")

    await _persist_split_failure(project_id, error_message)


async def _persist_split_failure(project_id: int, error_message: str | None) -> None:
    """Write split_error on a fresh connection (parent may be poisoned)."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await DbProject.update(
                bg_db,
                project_id,
                project_schemas.ProjectUpdate(
                    split_error=error_message,
                ),
            )
            await bg_db.commit()
    except Exception:
        log.exception(
            "Failed to persist split_error for project %s",
            project_id,
        )
