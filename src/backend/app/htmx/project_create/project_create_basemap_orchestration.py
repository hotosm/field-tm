"""Basemap autostart helpers for project-create HTMX routes."""

import asyncio
import logging
from datetime import datetime, timezone

from psycopg import AsyncConnection

from app.config import settings
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.helpers.basemap_services import (
    check_tilepack_status,
    search_oam_imagery,
    trigger_tilepack_generation,
)
from app.htmx.basemap.basemap_attach_flow import run_basemap_attach_background
from app.projects import project_schemas

log = logging.getLogger(__name__)


async def mark_basemap_autostart_failed(
    bg_db: AsyncConnection, project_id: int
) -> None:
    """Persist failed basemap autostart status for a project."""
    await DbProject.update(
        bg_db,
        project_id,
        project_schemas.ProjectUpdate(
            basemap_status="failed",
            basemap_attach_status="idle",
        ),
    )
    await bg_db.commit()


async def resume_simple_project_tilepack_if_needed(
    bg_db: AsyncConnection, project: DbProject
) -> bool:
    """Resume tracking/attach flow for an in-progress simple-project tilepack."""
    stac_item_id = str(project.basemap_stac_item_id or "").strip()
    if not stac_item_id:
        return False

    status_value, download_url = await check_tilepack_status(stac_item_id)
    resolved_url = download_url or project.basemap_url
    is_ready_with_url = status_value == "ready" and bool(resolved_url)
    # Once the project has flipped to "ready" with a stored URL, refuse to
    # downgrade on a later poll (upstream can return 200 OK without a URL,
    # which we map to "generating").
    already_ready = project.basemap_status == "ready" and bool(project.basemap_url)
    persisted_status = (
        "ready" if already_ready and not is_ready_with_url else status_value
    )
    now = datetime.now(timezone.utc)

    if is_ready_with_url:
        next_attach_status = "in_progress"
    elif status_value == "generating":
        next_attach_status = "pending_autostart"
    else:
        next_attach_status = "idle"

    await DbProject.update(
        bg_db,
        project.id,
        project_schemas.ProjectUpdate(
            basemap_status=persisted_status,
            basemap_url=resolved_url,
            basemap_attach_status=next_attach_status,
            basemap_attach_error=None,
            basemap_attach_updated_at=(now if is_ready_with_url else None),
        ),
    )
    await bg_db.commit()

    if is_ready_with_url:
        asyncio.create_task(run_basemap_attach_background(project.id, resolved_url))

    return True


def basemap_autostart_skipped(project: DbProject | None) -> bool:
    """Return whether basemap autostart should be skipped for this project."""
    if not project:
        return True

    if project.field_mapping_app != FieldMappingApp.QFIELD:
        return True

    if project.status != project_schemas.ProjectStatus.PUBLISHED:
        return True

    if project.basemap_status == "ready":
        return True

    return bool(
        project.basemap_status == "generating"
        and str(project.basemap_stac_item_id or "").strip()
    )


async def select_simple_project_basemap(outline: dict) -> dict | None:
    """Pick the best available imagery candidate for a simple-project outline."""
    from app.qfield.qfield_crud import _outline_to_bbox_str

    bbox = [float(v) for v in _outline_to_bbox_str(outline).split(",")]
    items = await search_oam_imagery(bbox)
    if not items:
        return None
    return items[0]


async def start_simple_project_tilepack(
    bg_db: AsyncConnection,
    project_id: int,
    selected: dict,
) -> tuple[str, str | None]:
    """Start tilepack generation and persist immediate basemap state transitions."""
    stac_item_id = str(selected.get("id") or "").strip()
    if not stac_item_id:
        raise ValueError("Missing STAC item id")

    await DbProject.update(
        bg_db,
        project_id,
        project_schemas.ProjectUpdate(
            basemap_stac_item_id=stac_item_id,
            basemap_status="generating",
            basemap_url=None,
            basemap_minzoom=selected.get("minzoom"),
            basemap_maxzoom=selected.get("maxzoom"),
            basemap_attach_status="pending_autostart",
            basemap_attach_error=None,
            basemap_attach_updated_at=None,
        ),
    )

    status_value, download_url = await trigger_tilepack_generation(stac_item_id)
    is_ready_with_url = status_value == "ready" and bool(download_url)
    now = datetime.now(timezone.utc)

    if is_ready_with_url:
        next_attach_status = "in_progress"
    elif status_value == "generating":
        next_attach_status = "pending_autostart"
    else:
        # status_value is "failed" or unexpected — there is nothing to autostart.
        next_attach_status = "idle"

    await DbProject.update(
        bg_db,
        project_id,
        project_schemas.ProjectUpdate(
            basemap_status=status_value,
            basemap_url=download_url,
            basemap_attach_status=next_attach_status,
            basemap_attach_error=None,
            basemap_attach_updated_at=(now if is_ready_with_url else None),
        ),
    )
    await bg_db.commit()
    return status_value, download_url


async def maybe_resume_simple_project_tilepack(
    bg_db: AsyncConnection, project: DbProject
) -> bool:
    """Resume tilepack flow when project is already in generating state."""
    existing_stac_item_id = str(project.basemap_stac_item_id or "").strip()
    if project.basemap_status != "generating" or not existing_stac_item_id:
        return False

    await resume_simple_project_tilepack_if_needed(bg_db, project)
    return True


async def select_and_start_simple_project_tilepack(
    bg_db: AsyncConnection, project_id: int, outline: dict
) -> tuple[str, str | None] | None:
    """Choose imagery and start tilepack generation, or mark autostart failed."""
    selected = await select_simple_project_basemap(outline)
    if selected is None:
        await mark_basemap_autostart_failed(bg_db, project_id)
        return None

    try:
        return await start_simple_project_tilepack(bg_db, project_id, selected)
    except ValueError:
        await mark_basemap_autostart_failed(bg_db, project_id)
        return None


def enqueue_simple_project_basemap_attach(
    project_id: int, download_url: str | None
) -> None:
    """Queue asynchronous basemap attach when tilepack URL is available."""
    if not download_url:
        return

    asyncio.create_task(run_basemap_attach_background(project_id, download_url))


async def run_simple_project_basemap_autostart(
    bg_db: AsyncConnection, project_id: int, outline: dict
) -> None:
    """Drive simple-project basemap autostart from project state to enqueue."""
    project = await DbProject.one(bg_db, project_id)
    if not project:
        return

    if await maybe_resume_simple_project_tilepack(bg_db, project):
        return

    if basemap_autostart_skipped(project):
        return

    tilepack = await select_and_start_simple_project_tilepack(
        bg_db, project_id, outline
    )
    if tilepack is None:
        return

    status_value, download_url = tilepack
    if status_value == "ready" and download_url:
        enqueue_simple_project_basemap_attach(project_id, download_url)


async def persist_simple_project_basemap_autostart_failure(project_id: int) -> None:
    """Best-effort failure persistence when autostart orchestration errors."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await mark_basemap_autostart_failed(bg_db, project_id)
    except Exception:
        log.exception(
            "Failed to persist basemap autostart failure for project %s", project_id
        )


async def autostart_basemap_for_simple_project(project_id: int, outline: dict) -> None:
    """Run basemap autostart in isolated DB connection for background workflows."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await run_simple_project_basemap_autostart(bg_db, project_id, outline)
    except Exception:
        log.exception(
            "Simple-project basemap autostart failed for project %s", project_id
        )
        await persist_simple_project_basemap_autostart_failure(project_id)
