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

"""Project creation and XLSForm upload HTMX routes."""

import ast
import asyncio
import json
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from area_splitter import SplittingAlgorithm
from litestar import Litestar, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.response import Response, Template
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.auth.auth_deps import get_optional_auth_user, get_user_sub, login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import mapper
from app.config import AuthProvider, settings
from app.db.database import db_conn
from app.db.enums import FieldMappingApp, XLSFormType
from app.db.models import DbProject
from app.helpers.basemap_services import (
    check_tilepack_status,
    search_oam_imagery,
    trigger_tilepack_generation,
)
from app.htmx.htmx_schemas import XLSFormUploadData
from app.i18n import _
from app.projects import project_schemas
from app.projects.project_crud import (
    claim_simple_project_basemap_generation,
    claim_simple_project_basemap_resume,
)
from app.projects.project_services import (
    ConflictError,
    ServiceError,
    SplitAoiOptions,
    create_project_stub,
    derive_simple_project_metadata,
    download_osm_data,
    finalize_qfield_project,
    process_xlsform,
    save_data_extract,
    save_task_areas,
    split_aoi,
)
from app.projects.project_services import (
    ValidationError as SvcValidationError,
)

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


def _outline_json_error() -> str:
    """Return a translated validation message for malformed outline JSON."""
    return _(
        "Project area must be valid JSON "
        "(GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection)."
    )


def _first_form_value(value: object) -> str:
    """Normalize URL-encoded form values to a stripped string."""
    while isinstance(value, (list, tuple)):
        if not value:
            return ""
        value = next((item for item in value if item not in (None, "")), value[0])

    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    return str(value or "").strip()


def _coerce_single_form_value(value: object) -> object:
    """Unwrap list/tuple form values to a single payload item."""
    while isinstance(value, (list, tuple)):
        if not value:
            return {}
        value = next((item for item in value if item not in (None, "")), value[0])
    return value


def _parse_outline_json_string(value_str: str) -> object | None:
    """Parse a string outline payload via JSON first, then Python literal syntax."""
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(value_str)
        except (SyntaxError, ValueError):
            return None


def _parse_outline_payload(raw_value: object) -> dict:
    """Parse and normalize a GeoJSON outline payload from form data.

    Required for handling str, bytes, list wrapped values etc --> geojson.
    """
    if isinstance(raw_value, dict):
        return raw_value

    value: object = _coerce_single_form_value(raw_value)

    if isinstance(value, dict):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if value is None:
        return {}

    if isinstance(value, str):
        value_str = value.strip()
        if not value_str:
            return {}
        parsed = _parse_outline_json_string(value_str)
    else:
        try:
            parsed = json.loads(str(value))
        except (TypeError, ValueError):
            parsed = None

    if isinstance(parsed, dict):
        return parsed

    if isinstance(parsed, (list, tuple)) and len(parsed) == 1:
        return _parse_outline_payload(parsed[0])

    raise ValueError(_outline_json_error())


def _normalize_field_mapping_app(value: object) -> str:
    """Normalize field-mapping app form values to canonical enum values."""
    if isinstance(value, FieldMappingApp):
        return value.value
    value_str = str(value or "").strip()
    if not value_str:
        return ""
    if "." in value_str:
        value_str = value_str.split(".")[-1]
    normalized = value_str.upper()
    if normalized == "QFIELD":
        return FieldMappingApp.QFIELD.value
    if normalized == "ODK":
        return FieldMappingApp.ODK.value
    return value_str


def _project_form_error(message: str) -> str:
    """Build the standard project-create form error block."""
    return (
        '<div id="form-error"'
        ' style="margin-bottom: 16px;'
        ' display: block;">'
        '<wa-callout variant="danger">'
        '<span id="form-error-message">'
        f"{message}"
        "</span></wa-callout></div>"
    )


def _build_unique_simple_project_name(project_name: str) -> str:
    """Append a short unique suffix for simple-flow duplicate names."""
    return f"{project_name} {uuid4().hex[:8]}"


def _extract_has_features(data_extract_geojson: dict | None) -> bool:
    """Return whether a data extract contains at least one feature."""
    if not isinstance(data_extract_geojson, dict):
        return False
    features = data_extract_geojson.get("features")
    return isinstance(features, list) and len(features) > 0


def _simple_empty_extract_hx_trigger() -> str:
    """Build HTMX trigger payload for simple-flow empty extract notifications."""
    return json.dumps(
        {
            "simpleCollectNewDataNotice": _(
                "No existing OSM buildings were found in this area. "
                "Continue mapping from scratch."
            )
        }
    )


_SIMPLE_EMPTY_EXTRACT_VALIDATION_MARKERS = (
    "No data found in OSM",
    "No valid geometries found in OSM",
)


def _is_empty_extract_validation_error(message: str) -> bool:
    """Return whether service validation message indicates empty usable OSM extract."""
    return any(marker in message for marker in _SIMPLE_EMPTY_EXTRACT_VALIDATION_MARKERS)


def _parse_project_create_form(data: dict) -> tuple[str, str, str, list[str], dict]:
    """Normalize the HTMX project-create form payload."""
    project_name = _first_form_value(data.get("project_name", ""))
    description = _first_form_value(data.get("description", ""))
    field_mapping_app = _normalize_field_mapping_app(
        _first_form_value(data.get("field_mapping_app", ""))
    )
    hashtags_str = _first_form_value(data.get("hashtags", ""))
    outline = _parse_outline_payload(data.get("outline", ""))
    hashtags = [tag.strip() for tag in hashtags_str.split(",") if tag.strip()]
    return project_name, description, field_mapping_app, hashtags, outline


def _to_bool_form_value(value: object, default: bool = False) -> bool:
    """Normalize string/bool form values."""
    if value in ("", None):
        return default
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


async def _mark_basemap_autostart_failed(
    bg_db: AsyncConnection, project_id: int
) -> None:
    """Persist a failed basemap autostart state."""
    await DbProject.update(
        bg_db,
        project_id,
        project_schemas.ProjectUpdate(basemap_status="failed"),
    )
    await bg_db.commit()


async def _resume_simple_project_tilepack_if_needed(
    bg_db: AsyncConnection, project: DbProject
) -> bool:
    """Resume a previously-triggered tilepack generation if one already exists."""
    stac_item_id = str(project.basemap_stac_item_id or "").strip()
    if not stac_item_id:
        return False

    status_value, download_url = await check_tilepack_status(stac_item_id)
    now = datetime.now(timezone.utc)
    await DbProject.update(
        bg_db,
        project.id,
        project_schemas.ProjectUpdate(
            basemap_status=status_value,
            basemap_url=download_url or project.basemap_url,
            basemap_attach_status=(
                "in_progress" if status_value == "ready" else "idle"
            ),
            basemap_attach_error=None,
            basemap_attach_updated_at=(now if status_value == "ready" else None),
        ),
    )
    await bg_db.commit()

    if status_value == "ready" and (download_url or project.basemap_url):
        from app.htmx.basemap_routes import _run_basemap_attach_background

        asyncio.create_task(
            _run_basemap_attach_background(
                project.id, download_url or project.basemap_url
            )
        )

    return True


def _basemap_autostart_skipped(project: DbProject | None) -> bool:
    """Return whether basemap autostart should stop before any remote calls."""
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


async def _select_simple_project_basemap(outline: dict) -> dict | None:
    """Return the first matching STAC item for a simple-project outline."""
    from app.qfield.qfield_crud import _outline_to_bbox_str

    bbox = [float(v) for v in _outline_to_bbox_str(outline).split(",")]
    items = await search_oam_imagery(bbox)
    if not items:
        return None
    return items[0]


async def _start_simple_project_tilepack(
    bg_db: AsyncConnection,
    project_id: int,
    selected: dict,
) -> tuple[str, str | None]:
    """Persist tilepack request metadata and trigger generation."""
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
            basemap_attach_status="idle",
            basemap_attach_error=None,
            basemap_attach_updated_at=None,
        ),
    )

    status_value, download_url = await trigger_tilepack_generation(stac_item_id)
    now = datetime.now(timezone.utc)
    await DbProject.update(
        bg_db,
        project_id,
        project_schemas.ProjectUpdate(
            basemap_status=status_value,
            basemap_url=download_url,
            basemap_attach_status=(
                "in_progress" if status_value == "ready" else "idle"
            ),
            basemap_attach_error=None,
            basemap_attach_updated_at=(now if status_value == "ready" else None),
        ),
    )
    await bg_db.commit()
    return status_value, download_url


async def _maybe_resume_simple_project_tilepack(
    bg_db: AsyncConnection, project: DbProject
) -> bool:
    """Resume generating tilepacks that already have a selected STAC item."""
    existing_stac_item_id = str(project.basemap_stac_item_id or "").strip()
    if project.basemap_status != "generating" or not existing_stac_item_id:
        return False

    await _resume_simple_project_tilepack_if_needed(bg_db, project)
    return True


async def _select_and_start_simple_project_tilepack(
    bg_db: AsyncConnection, project_id: int, outline: dict
) -> tuple[str, str | None] | None:
    """Select a basemap candidate and start tilepack generation."""
    selected = await _select_simple_project_basemap(outline)
    if selected is None:
        await _mark_basemap_autostart_failed(bg_db, project_id)
        return None

    try:
        return await _start_simple_project_tilepack(bg_db, project_id, selected)
    except ValueError:
        await _mark_basemap_autostart_failed(bg_db, project_id)
        return None


def _enqueue_simple_project_basemap_attach(
    project_id: int, download_url: str | None
) -> None:
    """Queue basemap attachment once a tilepack is ready."""
    if not download_url:
        return

    from app.htmx.basemap_routes import _run_basemap_attach_background

    asyncio.create_task(_run_basemap_attach_background(project_id, download_url))


async def _run_simple_project_basemap_autostart(
    bg_db: AsyncConnection, project_id: int, outline: dict
) -> None:
    """Execute simple-project basemap autostart once a DB connection is open."""
    project = await DbProject.one(bg_db, project_id)
    if not project:
        return

    if await _maybe_resume_simple_project_tilepack(bg_db, project):
        return

    if _basemap_autostart_skipped(project):
        return

    tilepack = await _select_and_start_simple_project_tilepack(
        bg_db, project_id, outline
    )
    if tilepack is None:
        return

    status_value, download_url = tilepack
    if status_value == "ready" and download_url:
        _enqueue_simple_project_basemap_attach(project_id, download_url)


async def _persist_simple_project_basemap_autostart_failure(project_id: int) -> None:
    """Best-effort persistence for background basemap autostart failures."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await _mark_basemap_autostart_failed(bg_db, project_id)
    except Exception:
        log.exception(
            "Failed to persist basemap autostart failure for project %s", project_id
        )


async def _autostart_basemap_for_simple_project(project_id: int, outline: dict) -> None:
    """Auto-start basemap generation for simple projects in the background."""
    try:
        async with await AsyncConnection.connect(settings.FTM_DB_URL) as bg_db:
            await _run_simple_project_basemap_autostart(bg_db, project_id, outline)
    except Exception:
        log.exception(
            "Simple-project basemap autostart failed for project %s", project_id
        )
        await _persist_simple_project_basemap_autostart_failure(project_id)


def _is_simple_basemap_reconcile_candidate(project_row: dict) -> bool:
    """Return whether a project row is eligible for simple-flow basemap recovery."""
    if project_row.get("field_mapping_app") != FieldMappingApp.QFIELD.value:
        return False

    if project_row.get("status") != project_schemas.ProjectStatus.PUBLISHED.value:
        return False

    outline = project_row.get("outline")
    if not isinstance(outline, dict):
        return False

    outline_type = str(outline.get("type") or "").strip()
    return bool(outline_type)


async def _claim_simple_project_basemap_reconcile(
    conn: AsyncConnection, row: dict
) -> bool:
    """Claim a stranded basemap row for either generation or resume."""
    project_id = int(row["id"])
    existing_stac_item_id = str(row.get("basemap_stac_item_id") or "").strip()

    if existing_stac_item_id:
        return await claim_simple_project_basemap_resume(
            db=conn,
            project_id=project_id,
        )

    return await claim_simple_project_basemap_generation(
        db=conn,
        project_id=project_id,
    )


def _enqueue_simple_project_basemap_reconcile(row: dict) -> None:
    """Schedule basemap autostart for a claimed reconcile row."""
    project_id = int(row["id"])
    outline = row["outline"]
    asyncio.create_task(_autostart_basemap_for_simple_project(project_id, outline))


async def reconcile_simple_project_basemap_autostarts(server: Litestar) -> None:
    """Re-enqueue simple basemap autostarts stranded across process restarts."""
    enqueued = 0

    async with server.state.db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    field_mapping_app::text AS field_mapping_app,
                    status::text AS status,
                    basemap_stac_item_id,
                    ST_AsGeoJSON(outline)::jsonb AS outline
                FROM projects
                WHERE basemap_status = 'generating';
                """
            )
            rows = await cur.fetchall()

        if not rows:
            return

        for row in rows:
            try:
                if not _is_simple_basemap_reconcile_candidate(row):
                    continue

                claimed = await _claim_simple_project_basemap_reconcile(conn, row)
                if not claimed:
                    continue

                _enqueue_simple_project_basemap_reconcile(row)
                enqueued += 1
            except Exception:
                log.exception(
                    "Failed to re-enqueue simple basemap autostart for project %s",
                    row.get("id"),
                )

    if enqueued:
        log.info(
            "Re-enqueued basemap autostarts for %s stranded simple projects", enqueued
        )


def _login_prompt_path(next_path: str) -> str:
    """Build login URL preserving a return-to path."""
    return f"/login?return_to={quote(next_path, safe='')}"


async def _create_simple_project_stub(
    db: AsyncConnection,
    auth_user: object,
    project_name: str,
    description: str,
    outline: dict,
    hashtags: list[str],
):
    """Create a simple-flow project, retrying once with a unique name."""
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
            project_name=_build_unique_simple_project_name(project_name),
            **create_kwargs,
        )


async def _finalize_simple_project_creation(
    db: AsyncConnection,
    project_id: int,
    outline: dict,
) -> tuple[bool, dict[str, str]]:
    """Prepare extract, finalize QField setup, and enqueue basemap autostart."""
    default_template_bytes = await _get_default_buildings_template_bytes(db)
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

    await _prepare_simple_project_data_extract(db=db, project_id=project_id)

    refreshed_project = await DbProject.one(db, project_id)
    extract_has_features = _extract_has_features(
        refreshed_project.data_extract_geojson if refreshed_project else None
    )

    if extract_has_features:
        tasks_geojson = await split_aoi(
            db,
            project_id,
            SplitAoiOptions(
                algorithm=SplittingAlgorithm.AVG_BUILDING_SKELETON.value,
                no_of_buildings=10,
                include_roads=True,
                include_rivers=True,
                include_railways=True,
                include_aeroways=True,
            ),
        )
        await save_task_areas(db, project_id, tasks_geojson)

    await finalize_qfield_project(db=db, project_id=project_id)

    claimed = await claim_simple_project_basemap_generation(
        db=db, project_id=project_id
    )
    if claimed:
        asyncio.create_task(_autostart_basemap_for_simple_project(project_id, outline))

    headers = {"HX-Redirect": f"/projects/{project_id}"}
    if not extract_has_features:
        headers["HX-Trigger"] = _simple_empty_extract_hx_trigger()

    return extract_has_features, headers


async def _validate_xlsform_extension(data: XLSFormUploadData) -> BytesIO:
    """Validate an uploaded XLSForm has .xls or .xlsx extension and return bytes."""
    filename = Path(data.filename or "")
    file_ext = filename.suffix.lower()

    if file_ext not in [".xls", ".xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_("Provide a valid .xls or .xlsx file"),
        )

    return BytesIO(await data.read())


async def _resolve_uploaded_xlsform_bytes(
    data: XLSFormUploadData,
    db: AsyncConnection,
) -> tuple[BytesIO | None, Response | None]:
    """Load XLSForm bytes from a chosen template or uploaded file."""
    template_form_id_str = str(data.template_form_id) if data.template_form_id else ""
    if template_form_id_str:
        template_bytes = await _get_template_xlsform_bytes(
            int(template_form_id_str), db
        )
        if not template_bytes:
            return None, Response(
                content=_callout("danger", _("Failed to load template form.")),
                media_type="text/html",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return BytesIO(template_bytes), None

    if not data.xlsform:
        return None, Response(
            content=_callout("danger", _("Please select a form or upload a file.")),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return await _validate_xlsform_extension(data.xlsform), None


@get(
    path="/new",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def new_project(
    request: HTMXRequest, db: AsyncConnection, auth_user: object | None
) -> Template | Response:
    """Render the new project creation form."""
    if settings.AUTH_PROVIDER != AuthProvider.DISABLED and auth_user is None:
        login_path = _login_prompt_path(str(request.url.path))
        if request.headers.get("HX-Request") == "true":
            return Response(
                content="",
                status_code=status.HTTP_200_OK,
                headers={"HX-Redirect": login_path},
            )
        return Response(
            content="",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": login_path},
        )
    return HTMXTemplate(template_name="new_project.html")


@get(
    path="/new/simple",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(get_optional_auth_user),
    },
)
async def new_project_simple(
    request: HTMXRequest, db: AsyncConnection, auth_user: object | None
) -> Template | Response:
    """Render the simple AOI-only project creation form."""
    if settings.AUTH_PROVIDER != AuthProvider.DISABLED and auth_user is None:
        login_path = _login_prompt_path(str(request.url.path))
        if request.headers.get("HX-Request") == "true":
            return Response(
                content="",
                status_code=status.HTTP_200_OK,
                headers={"HX-Redirect": login_path},
            )
        return Response(
            content="",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": login_path},
        )
    return HTMXTemplate(template_name="new_project_simple.html")


def _template_form_type_from_title(form_title: str | None) -> XLSFormType | None:
    """Resolve a template title to an XLSFormType enum member."""
    if not form_title:
        return None
    return next(
        (xls_type for xls_type in XLSFormType if xls_type.value == form_title),
        None,
    )


async def _get_template_xlsform_bytes(
    form_id: int,
    db: AsyncConnection,
) -> bytes | None:
    """Get template XLSForm bytes by ID from database or osm-fieldwork.

    Returns the bytes if found, None otherwise.
    """
    # First try to get from database
    sql = """
        SELECT title, xls
        FROM template_xlsforms
        WHERE id = %(form_id)s;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"form_id": form_id})
        result = await cur.fetchone()

    if not result:
        return None

    # If XLSForm bytes exist in database, return them
    if result.get("xls"):
        return result["xls"]

    form_type = _template_form_type_from_title(result.get("title"))
    if not form_type:
        return None

    try:
        form_path = f"{xlsforms_path}/{form_type.name}.yaml"
        xlsx_bytes = convert_to_xlsform(str(form_path))
        if xlsx_bytes:
            return xlsx_bytes
    except Exception as e:
        log.error(f"Error converting YAML to XLSForm: {e}", exc_info=True)

    return None


async def _get_default_buildings_template_bytes(db: AsyncConnection) -> bytes | None:
    """Get bytes for the default OSM Buildings XLSForm template."""
    sql = """
        SELECT id
        FROM template_xlsforms
        WHERE title = %(title)s
        ORDER BY id
        LIMIT 1;
    """

    async with db.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, {"title": XLSFormType.buildings.value})
        result = await cur.fetchone()

    if result and result.get("id") is not None:
        xlsx_bytes = await _get_template_xlsform_bytes(int(result["id"]), db)
        if xlsx_bytes:
            return xlsx_bytes

    try:
        fallback_path = f"{xlsforms_path}/{XLSFormType.buildings.name}.yaml"
        return convert_to_xlsform(fallback_path)
    except Exception as e:
        log.error(
            "Error converting default OSM Buildings YAML to XLSForm: %s",
            e,
            exc_info=True,
        )
        return None


async def _prepare_simple_project_data_extract(
    db: AsyncConnection,
    project_id: int,
) -> None:
    """Populate simple workflow extract, falling back to collect-new-data mode."""
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
        if not _is_empty_extract_validation_error(e.message):
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


@get(
    "/template-xlsform/{form_id:int}",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def get_template_xlsform(
    form_id: int,
    db: AsyncConnection,
) -> Response:
    """Get template XLSForm bytes by ID from database or osm-fieldwork."""
    xlsx_bytes = await _get_template_xlsform_bytes(form_id, db)

    if not xlsx_bytes:
        return Response(
            content="Template XLSForm not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=template_{form_id}.xlsx"
        },
    )


@post(
    path="/projects/create",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Create a project via HTMX form submission."""
    try:
        try:
            project_name, description, field_mapping_app, hashtags, outline = (
                _parse_project_create_form(data)
            )
        except ValueError:
            return Response(
                content=_project_form_error(_outline_json_error()),
                media_type="text/html",
                # Keep HTMX validation responses as 200 so reverse proxies / WAF
                # don't replace the body with branded error pages.
                status_code=status.HTTP_200_OK,
            )

        project = await create_project_stub(
            db=db,
            project_name=project_name,
            field_mapping_app=field_mapping_app,
            description=description,
            outline=outline,
            hashtags=hashtags,
            user_sub=get_user_sub(auth_user),
        )
        await db.commit()

        return Response(
            content="",
            status_code=status.HTTP_200_OK,
            headers={"HX-Redirect": f"/projects/{project.id}"},
        )
    except SvcValidationError as e:
        message = e.message
        headers = {}
        if "Description is required" in message:
            headers.update(
                {
                    "HX-Retarget": "#description-error",
                    "HX-Reswap": "innerHTML",
                }
            )
        if "Area of Interest" in message or "too large" in message:
            headers["HX-Trigger"] = json.dumps({"missingOutline": message})
        return Response(
            content=_project_form_error(message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers=headers,
        )
    except ConflictError as e:
        hx_trigger = json.dumps({"duplicateProjectName": e.message})
        return Response(
            content=_project_form_error(e.message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers={"HX-Trigger": hx_trigger},
        )
    except ServiceError as e:
        return Response(
            content=_project_form_error(e.message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        log.error(
            f"Error creating project via HTMX: {e}",
            exc_info=True,
        )
        return Response(
            content=_project_form_error(
                _("An unexpected error occurred. Please try again.")
            ),
            media_type="text/html",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@post(
    path="/projects/create-simple",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def create_simple_project_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Create a simple OSM buildings project from AOI only."""
    try:
        try:
            outline = _parse_outline_payload(data.get("outline", ""))
        except ValueError:
            return Response(
                content=_project_form_error(_outline_json_error()),
                media_type="text/html",
                status_code=status.HTTP_200_OK,
            )

        (
            project_name,
            description,
            hashtags,
            _location_str,
        ) = await derive_simple_project_metadata(db=db, outline=outline)
        project = await _create_simple_project_stub(
            db=db,
            auth_user=auth_user,
            project_name=project_name,
            description=description,
            outline=outline,
            hashtags=hashtags,
        )
        _extract_has_features, headers = await _finalize_simple_project_creation(
            db=db,
            project_id=project.id,
            outline=outline,
        )

        return Response(
            content="",
            status_code=status.HTTP_200_OK,
            headers=headers,
        )
    except SvcValidationError as e:
        message = e.message
        headers = {}
        if "Area of Interest" in message or "too large" in message:
            headers["HX-Trigger"] = json.dumps({"missingOutline": message})
        return Response(
            content=_project_form_error(message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers=headers,
        )
    except ConflictError as e:
        hx_trigger = json.dumps({"duplicateProjectName": e.message})
        return Response(
            content=_project_form_error(e.message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers={"HX-Trigger": hx_trigger},
        )
    except ServiceError as e:
        return Response(
            content=_project_form_error(e.message),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        log.error(
            f"Error creating simple project via HTMX: {e}",
            exc_info=True,
        )
        return Response(
            content=_project_form_error(
                _("An unexpected error occurred. Please try again.")
            ),
            media_type="text/html",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@post(
    path="/upload-xlsform-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_xlsform_htmx(  # noqa: PLR0911, PLR0913
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,  # noqa: ARG001
    data: XLSFormUploadData = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    """Upload XLSForm via HTMX form submission."""
    project = current_user.get("project")
    if not project:
        return Response(
            content=_callout("danger", _("Project not found.")),
            media_type="text/html",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Verify project_id matches the user's project for security
    if project.id != project_id:
        return Response(
            content=_callout(
                "danger",
                _("Project ID mismatch. You do not have access to this project."),
            ),
            media_type="text/html",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Use project.id from current_user (more secure)
    project_id = project.id

    need_verification_fields_bool = _to_bool_form_value(
        data.need_verification_fields, default=True
    )
    include_photo_upload_bool = _to_bool_form_value(
        data.include_photo_upload, default=True
    )
    mandatory_photo_upload_bool = _to_bool_form_value(
        data.mandatory_photo_upload, default=False
    )
    use_odk_collect_bool = _to_bool_form_value(data.use_odk_collect, default=False)
    default_language_explicit = _to_bool_form_value(
        data.default_language_explicit, default=False
    )
    default_language = data.default_language if default_language_explicit else None

    try:
        xlsform_bytes, error_response = await _resolve_uploaded_xlsform_bytes(data, db)
        if error_response:
            return error_response

        # Delegate to shared service function (used by both HTMX and API routes)
        await process_xlsform(
            db=db,
            project_id=project_id,
            xlsform_bytes=xlsform_bytes,
            need_verification_fields=need_verification_fields_bool,
            include_photo_upload=include_photo_upload_bool,
            mandatory_photo_upload=mandatory_photo_upload_bool,
            use_odk_collect=use_odk_collect_bool,
            default_language=default_language,
        )

        # Return success response with HTMX redirect
        return Response(
            content=_callout(
                "success",
                _("Form validated and uploaded successfully! Reloading page..."),
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
            headers={
                "HX-Refresh": "true",  # Reload the page to show updated state
            },
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        log.error(f"Error uploading XLSForm via HTMX: {e}", exc_info=True)
        error_msg = (
            str(e) if hasattr(e, "__str__") else _("An unexpected error occurred")
        )
        return Response(
            content=_callout(
                "danger", (_("Error"), ": {error_msg}".format(error_msg=error_msg))
            ),
            media_type="text/html",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
