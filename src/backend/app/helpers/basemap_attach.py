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
"""Attach a ready tilepack basemap to a QField project in the background.

Attach failures are retried once when they look like transient network errors.
"""

import asyncio
import logging
from datetime import datetime, timezone

from psycopg import AsyncConnection

from app.config import settings
from app.db.models import DbProject
from app.helpers.background_tasks import spawn
from app.helpers.basemap_services import check_tilepack_status
from app.i18n import _
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_crud import attach_basemap_to_qfield_project

log = logging.getLogger(__name__)
AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS = 8
AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS = 1


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


async def enqueue_basemap_attach(
    db: AsyncConnection, project_id: int, basemap_url: str
) -> None:
    """Mark the basemap attach as in progress and run it in the background."""
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

    spawn(
        run_basemap_attach_background(project_id, basemap_url),
        name=f"basemap-attach:{project_id}",
    )
