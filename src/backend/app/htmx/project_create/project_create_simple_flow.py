"""Simple-flow orchestration helpers for project-create HTMX routes."""

import json
import logging
import math
from datetime import datetime, timezone
from io import BytesIO

from area_splitter import SplittingAlgorithm
from psycopg import AsyncConnection

from app.auth.auth_deps import get_user_sub
from app.config import settings
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.helpers.background_tasks import spawn as _spawn_bg_task
from app.i18n import _
from app.projects import project_schemas
from app.projects.project_crud import claim_simple_project_basemap_generation
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    SplitAoiOptions,
    create_project_stub,
    download_osm_data,
    finalize_qfield_project,
    process_xlsform,
    save_data_extract,
    save_task_areas,
    split_aoi,
)
from app.projects.project_services import ValidationError as SvcValidationError

from .project_create_basemap_orchestration import (
    autostart_basemap_for_simple_project,
)
from .project_create_parsing import build_unique_simple_project_name
from .project_create_templates import get_default_buildings_template_bytes

log = logging.getLogger(__name__)

_SIMPLE_EMPTY_EXTRACT_VALIDATION_MARKERS = (
    "No data found in OSM",
    "No valid geometries found in OSM",
)

# CG_StraightSkeleton runtime is superlinear in vertex count and times
# out for large extracts even with per-splitpolygon scoping; above this
# many buildings, fall back to the cheaper Voronoi splitter.
_SIMPLE_SKELETON_FEATURE_LIMIT = 5000

# Floor / ceiling for buildings-per-task in the simple flow.
# 5 keeps tiny AOIs from collapsing to a single task; 100 keeps mega-AOIs
# from producing tasks too large to map in one go.
_SIMPLE_BPT_MIN = 5
_SIMPLE_BPT_MAX = 100


def _simple_buildings_per_task(feature_count: int) -> int:
    """Scale buildings-per-task by feature count.

    Square-root interpolation anchored at f=1k → 10/task and f=100k → 100/task.
    Smoother task-count growth than linear scaling: a 10k-feature AOI gets
    ~32/task (~312 tasks) rather than the same 100 tasks a 1k AOI would.
    Clamped to [5, 100] so very small AOIs don't collapse and very large
    ones don't produce unmappably-large tasks.
    """
    if feature_count <= 0:
        return _SIMPLE_BPT_MIN
    raw = round(10 * math.sqrt(feature_count / 1000))
    return max(_SIMPLE_BPT_MIN, min(_SIMPLE_BPT_MAX, raw))


def extract_has_features(data_extract_geojson: dict | None) -> bool:
    """Return whether a data extract contains at least one feature."""
    if not isinstance(data_extract_geojson, dict):
        return False
    features = data_extract_geojson.get("features")
    return isinstance(features, list) and len(features) > 0


def simple_empty_extract_hx_trigger() -> str:
    """Return HX-Trigger payload for empty-extract simple workflow notice."""
    return json.dumps(
        {
            "simpleCollectNewDataNotice": _(
                "No existing OSM buildings were found in this area. "
                "Continue mapping from scratch."
            )
        }
    )


def is_empty_extract_validation_error(message: str) -> bool:
    """Return whether a validation error means OSM returned no usable data."""
    return any(marker in message for marker in _SIMPLE_EMPTY_EXTRACT_VALIDATION_MARKERS)


async def create_simple_project_stub(
    db: AsyncConnection,
    auth_user: object,
    project_name: str,
    description: str,
    outline: dict,
    hashtags: list[str],
):
    """Create a simple QField project stub with conflict-safe name fallback."""
    create_kwargs = {
        "db": db,
        "field_mapping_app": FieldMappingApp.QFIELD.value,
        "description": description,
        "outline": outline,
        "hashtags": hashtags,
        "user_sub": get_user_sub(auth_user),
    }

    try:
        return await create_project_stub(
            project_name=project_name,
            **create_kwargs,
        )
    except ConflictError:
        return await create_project_stub(
            project_name=build_unique_simple_project_name(project_name),
            **create_kwargs,
        )


async def prepare_simple_project_data_extract(
    db: AsyncConnection, project_id: int
) -> None:
    """Populate data extract for simple workflow, falling back to empty extract."""
    try:
        geojson_data = await download_osm_data(
            db=db,
            project_id=project_id,
            osm_category="buildings",
            geom_type="POLYGON",
            centroid=False,
        )
        await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson_data,
        )
        return
    except SvcValidationError as e:
        if not is_empty_extract_validation_error(e.message):
            raise
        log.info(
            "No OSM data found for simple workflow project %s; "
            "defaulting to collect-new-data mode.",
            project_id,
        )
    except ServiceError as e:
        log.warning(
            "OSM data extract failed for simple workflow project %s; "
            "defaulting to collect-new-data mode: %s",
            project_id,
            e,
        )

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_geojson={"type": "FeatureCollection", "features": []},
            task_areas_geojson={},
        ),
    )
    await db.commit()


async def finalize_simple_project_creation(
    db: AsyncConnection,
    project_id: int,
    outline: dict,
    autostart_callback,
) -> tuple[bool, dict[str, str]]:
    """Finalize simple project setup and return redirect/event response headers."""
    default_template_bytes = await get_default_buildings_template_bytes(db)
    if not default_template_bytes:
        raise ServiceError(
            _("Could not load default OSM Buildings form for simple project creation.")
        )

    await process_xlsform(
        db=db,
        project_id=project_id,
        xlsform_bytes=BytesIO(default_template_bytes),
        need_verification_fields=True,
        include_photo_upload=True,
        mandatory_photo_upload=False,
        use_odk_collect=False,
        default_language=None,
    )

    await prepare_simple_project_data_extract(db=db, project_id=project_id)

    refreshed_project = await DbProject.one(db, project_id)
    data_extract_geojson = (
        refreshed_project.data_extract_geojson if refreshed_project else None
    )
    has_features = extract_has_features(data_extract_geojson)

    if has_features:
        feature_count = len(data_extract_geojson.get("features", []))
        algorithm = (
            SplittingAlgorithm.AVG_BUILDING_VORONOI
            if feature_count > _SIMPLE_SKELETON_FEATURE_LIMIT
            else SplittingAlgorithm.AVG_BUILDING_SKELETON
        )
        buildings_per_task = _simple_buildings_per_task(feature_count)
        log.info(
            "Simple project %s: %s features -> %s splitter, %s buildings/task",
            project_id,
            feature_count,
            algorithm.value,
            buildings_per_task,
        )
        tasks_geojson = await split_aoi(
            db,
            project_id,
            SplitAoiOptions(
                algorithm=algorithm.value,
                no_of_buildings=buildings_per_task,
                include_roads=True,
                include_rivers=True,
                include_railways=True,
                include_aeroways=True,
                # Simple flow runs in a background task (see
                # run_simple_project_creation_background); no reverse-proxy
                # budget to protect, so let CG_StraightSkeleton run to
                # completion instead of capping at 270s.
                statement_timeout_ms=0,
            ),
        )
        await save_task_areas(db, project_id, tasks_geojson)

    await finalize_qfield_project(db=db, project_id=project_id)

    claimed = await claim_simple_project_basemap_generation(
        db=db, project_id=project_id
    )
    if claimed:
        _spawn_bg_task(
            autostart_callback(project_id, outline),
            name=f"basemap-autostart:{project_id}",
        )

    headers = {"HX-Redirect": f"/projects/{project_id}"}
    if not has_features:
        headers["HX-Trigger"] = simple_empty_extract_hx_trigger()

    return has_features, headers


async def _persist_creation_terminal_state(
    project_id: int,
    *,
    status_value: str,
    error_message: str | None,
) -> None:
    """Update creation_status on a fresh connection (parent may be in error)."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await DbProject.update(
                bg_db,
                project_id,
                project_schemas.ProjectUpdate(
                    creation_status=status_value,
                    creation_error=error_message,
                    creation_updated_at=datetime.now(timezone.utc),
                ),
            )
            await bg_db.commit()
    except Exception:
        log.exception(
            "Failed to persist creation_status=%s for project %s",
            status_value,
            project_id,
        )


async def run_simple_project_creation_background(
    project_id: int, outline: dict
) -> None:
    """Run simple-flow finalize in the background and persist terminal state.

    Reuses a single DB connection for the happy path; on failure, opens a
    fresh connection to persist the error so a poisoned transaction on the
    original connection can't block the update.
    """
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as db:
            await finalize_simple_project_creation(
                db=db,
                project_id=project_id,
                outline=outline,
                autostart_callback=autostart_basemap_for_simple_project,
            )
            await DbProject.update(
                db,
                project_id,
                project_schemas.ProjectUpdate(
                    creation_status="ready",
                    creation_error=None,
                    creation_updated_at=datetime.now(timezone.utc),
                ),
            )
            await db.commit()
            return
    except (SvcValidationError, ConflictError, ServiceError) as exc:
        error_message = exc.message
    except Exception:
        log.exception("Unexpected error finalizing simple project %s", project_id)
        error_message = _("An unexpected error occurred. Please try again.")

    await _persist_creation_terminal_state(
        project_id,
        status_value="failed",
        error_message=error_message,
    )
