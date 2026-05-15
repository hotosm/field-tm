"""HTMX routes for setup-step task splitting workflow."""

# ruff: noqa: D103

import logging

from litestar import get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import mapper
from app.db.database import db_conn
from app.db.models import DbProject
from app.htmx.map_helpers import render_leaflet_map
from app.i18n import _
from app.projects import project_crud, project_schemas
from app.projects.project_services import (
    ServiceError,
    SplitAoiOptions,
    save_task_areas,
    split_aoi,
)

from ..htmx_helpers import callout as _callout
from ..setup_steps.setup_step_map_layers import (
    build_preview_layers as _build_preview_layers,
)
from ..setup_steps.setup_step_map_layers import (
    build_split_preview_response as _build_split_preview_response,
)
from ..setup_steps.setup_step_map_layers import (
    task_preview_state as _task_preview_state,
)
from ..setup_steps.setup_step_parsing import parse_json_payload as _parse_json_payload
from ..setup_steps.setup_step_parsing import (
    parse_split_form_options as _parse_split_form_options,
)
from ..setup_steps.setup_step_parsing import (
    parse_task_boundaries_json as _parse_task_boundaries_json,
)
from ..setup_steps.setup_step_responses import (
    authorized_project_or_response as _authorized_project_or_response,
)
from ..setup_steps.setup_step_responses import (
    html_error_response as _html_error_response,
)
from ..setup_steps.setup_step_responses import (
    is_fragment_mode as _is_fragment_mode,
)
from ..setup_steps.setup_step_responses import (
    service_error_response as _service_error_response,
)
from ..setup_steps.setup_step_responses import (
    step4_completion_response as _step4_completion_response,
)
from ..setup_steps.setup_step_responses import (
    unexpected_error_response as _unexpected_error_response,
)

log = logging.getLogger(__name__)


@get(
    path="/preview-tasks-and-data-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def preview_tasks_and_data_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson

        if not data_extract:
            return Response(
                content=_callout(
                    "warning",
                    _(
                        "No data extract found. Please download OSM data or "
                        "upload a GeoJSON file first."
                    ),
                ),
                media_type="text/html",
                status_code=404,
            )

        task_boundaries_json = await project_crud.get_task_geometry(db, project_id)
        task_boundaries = _parse_task_boundaries_json(task_boundaries_json, project_id)
        is_no_splitting, preview_blocker = _task_preview_state(project, task_boundaries)
        if preview_blocker:
            return preview_blocker

        data_feature_count = len(data_extract.get("features", []))
        geojson_layers = _build_preview_layers(
            project,
            data_extract,
            task_boundaries,
            is_no_splitting,
        )

        map_html_content = render_leaflet_map(
            map_id="leaflet-map-tasks-and-data",
            geojson_layers=geojson_layers,
            height="600px",
            show_controls=True,
        )

        if is_no_splitting:
            preview_message = _(
                "Previewing whole AOI (no splitting) with "
                "%(data_feature_count)s data features. The entire AOI will be "
                "used as a single task."
            ) % {"data_feature_count": data_feature_count}
        else:
            task_count = len(task_boundaries.get("features", []))
            preview_message = _(
                "Previewing %(task_count)s task boundaries and "
                "%(data_feature_count)s data features together."
            ) % {
                "task_count": task_count,
                "data_feature_count": data_feature_count,
            }

        return Template(
            template_name="partials/project_details/fragments/map_preview.html",
            context={
                "preview_message": preview_message,
                "map_html_content": map_html_content,
            },
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(
            f"Error previewing tasks and data extract via HTMX: {e}", exc_info=True
        )
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


@post(
    path="/skip-task-split-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def skip_task_split_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    project_id: int = Parameter(),
    mode: str = Parameter(default="refresh"),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        project = await DbProject.one(db, project_id)

        if not project.outline:
            return Response(
                content=_callout(
                    "danger",
                    _("Project outline not found. Cannot skip task splitting."),
                ),
                media_type="text/html",
                status_code=400,
            )

        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(task_areas_geojson={}),
        )
        await db.commit()

        log.info(
            f"Task splitting skipped for project {project_id}. "
            "Will use whole AOI as single task."
        )

        refreshed_project = (
            await DbProject.one(db, project_id) if _is_fragment_mode(mode) else None
        )
        return _step4_completion_response(
            request=request,
            project_id=project_id,
            message=_(
                "✓ Task splitting skipped. The whole AOI will be used as "
                "a single task. You can proceed to Step 5."
            ),
            mode=mode,
            project=refreshed_project,
        )

    except Exception as e:
        log.error(f"Error skipping task split via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


@post(
    path="/split-aoi-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def split_aoi_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
    mode: str = Parameter(default="refresh"),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        log.debug(
            f"Split AOI request data keys: {list(data.keys()) if data else 'None'}"
        )
        split_options = _parse_split_form_options(data)
        algorithm = split_options["algorithm"]

        log.debug(
            "Split AOI parameters: "
            f"algorithm={algorithm}, "
            f"no_of_buildings={split_options['no_of_buildings']}, "
            f"no_of_tasks={split_options['no_of_tasks']}, "
            f"dimension_meters={split_options['dimension_meters']}, "
            f"include_roads={split_options['include_roads']}, "
            f"include_rivers={split_options['include_rivers']}, "
            f"include_railways={split_options['include_railways']}, "
            f"include_aeroways={split_options['include_aeroways']}"
        )

        if not algorithm:
            return _html_error_response(_("Please select a splitting option."), 400)

        tasks_featcol = await split_aoi(
            db=db,
            project_id=project_id,
            options=SplitAoiOptions(
                algorithm=algorithm,
                no_of_buildings=split_options["no_of_buildings"],
                no_of_tasks=split_options["no_of_tasks"],
                dimension_meters=split_options["dimension_meters"],
                include_roads=split_options["include_roads"],
                include_rivers=split_options["include_rivers"],
                include_railways=split_options["include_railways"],
                include_aeroways=split_options["include_aeroways"],
            ),
        )

        if tasks_featcol == {}:
            refreshed_project = (
                await DbProject.one(db, project_id) if _is_fragment_mode(mode) else None
            )
            return _step4_completion_response(
                request=request,
                project_id=project_id,
                message=_("✓ Task splitting is not required for this project setup."),
                mode=mode,
                project=refreshed_project,
            )

        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson
        return _build_split_preview_response(
            project_id,
            algorithm,
            tasks_featcol,
            data_extract,
            project,
        )

    except ServiceError as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(f"Error splitting AOI via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


@post(
    path="/accept-split-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def accept_split_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: object,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
    mode: str = Parameter(default="refresh"),
) -> Response:
    _project, not_found_response = _authorized_project_or_response(
        current_user, project_id
    )
    if not_found_response:
        return not_found_response

    try:
        tasks_geojson_str = data.get("tasks_geojson", "")
        if not tasks_geojson_str:
            data_keys = list(data.keys()) if data else "None"
            log.debug(f"Accept split data keys: {data_keys}")
            return _html_error_response(_("No task areas data provided."), 400)

        tasks_geojson, error_response = _parse_json_payload(
            tasks_geojson_str,
            _("Invalid task areas data format."),
            "Error parsing task areas GeoJSON",
        )
        if error_response:
            return error_response

        task_count = await save_task_areas(
            db=db,
            project_id=project_id,
            tasks_geojson=tasks_geojson,
        )
        is_empty_task_areas = tasks_geojson == {}

        log.info(
            f"Accepted and saved task areas for project {project_id} "
            f"(empty: {is_empty_task_areas}, count: {task_count})"
        )
        refreshed_project = (
            await DbProject.one(db, project_id) if _is_fragment_mode(mode) else None
        )
        return _step4_completion_response(
            request=request,
            project_id=project_id,
            message=_("✓ Split tasks saved successfully"),
            mode=mode,
            project=refreshed_project,
        )

    except ServiceError as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(f"Error accepting split via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


ROUTE_HANDLERS = [
    preview_tasks_and_data_htmx,
    skip_task_split_htmx,
    split_aoi_htmx,
    accept_split_htmx,
]
