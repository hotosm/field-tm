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

"""HTMX routes for project setup steps (data extract, task splitting, finalize)."""

import json
import logging

from geojson_aoi import parse_aoi
from litestar import get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.plugins.htmx import HTMXRequest
from litestar.response import Response
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import mapper, project_manager
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.database import db_conn
from app.db.models import DbProject
from app.helpers.geometry_utils import (
    AREA_LIMIT_KM2,
    AREA_WARN_KM2,
    check_crs,
    geojson_area_km2,
)
from app.htmx.map_helpers import render_leaflet_map
from app.projects import project_crud, project_schemas
from app.projects.project_services import (
    ODKFinalizeResult,
    ServiceError,
    download_osm_data,
    finalize_odk_project,
    finalize_qfield_project,
    save_data_extract,
    save_task_areas,
    split_aoi,
)
from app.projects.project_services import (
    ValidationError as SvcValidationError,
)
from app.qfield.qfield_schemas import QFieldCloud

from .htmx_helpers import callout as _callout

log = logging.getLogger(__name__)


def _build_odk_finalize_success_html(result: ODKFinalizeResult) -> str:
    """Build success markup returned by HTMX ODK finalize."""
    box_style = (
        "margin-top: 12px; padding: 16px;"
        " background-color: #f5f5f5; border-radius: 8px;"
    )
    link_style = "color: #d63f3f; text-decoration: none; font-weight: 600;"
    usr = result.manager_username
    pwd = result.manager_password

    return f"""
    <wa-callout variant="success">
      <span>Project created in ODK Central.</span>
    </wa-callout>
    <div style="{box_style}">
      <h4 style="margin: 0 0 10px 0;">
        Manager Access (ODK Central UI)
      </h4>
      <p style="margin: 0 0 8px 0;">
        <a href="{result.odk_url}"
           target="_blank" style="{link_style}">
          Open project in ODK Central
        </a>
      </p>
      <p style="margin: 0;">
        <strong>Username:</strong> <code>{usr}</code>
      </p>
      <p style="margin: 6px 0 0 0;">
        <strong>Password:</strong> <code>{pwd}</code>
      </p>
      <p style="margin: 8px 0 0 0; color: #666;">
        Save these credentials now. They will only be shown once.
      </p>
    </div>
    <div style="margin-top: 12px;">
      <wa-button type="button" variant="default"
        onclick="window.location.reload()">
        Reload Project Page
      </wa-button>
    </div>
    """


@post(
    path="/download-osm-data-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def download_osm_data_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    osm_category: str = Parameter(default="buildings"),
    geom_type: str = Parameter(default="POLYGON"),
    centroid: bool = Parameter(default=False),
) -> Response:
    """Download OSM data extract via HTMX and store GeoJSON in database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        featcol_single_geom_type = await download_osm_data(
            db=db,
            project_id=project_id,
            osm_category=osm_category,
            geom_type=geom_type,
            centroid=centroid,
        )
        feature_count = len(featcol_single_geom_type.get("features", []))

        # Encode GeoJSON for the Accept button (don't save yet)
        geojson_str = json.dumps(featcol_single_geom_type).replace('"', "&quot;")

        # Automatically show preview after successful download
        project = await DbProject.one(db, project_id)

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-download",
            geojson_layers=[
                {
                    "data": featcol_single_geom_type,
                    "name": "Data Extract",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        # Return success with map preview and Accept btn
        success_msg = _callout(
            "success",
            f"OSM data downloaded successfully! Found {feature_count} features.",
        )
        info_msg = (
            f"Previewing {feature_count} features"
            " on map. Review the data below."
            ' If satisfied, click "Accept Data'
            ' Extract" to save. Otherwise, try'
            " downloading again with different"
            " parameters."
        )
        form_style = "margin-top: 15px; display: flex; gap: 10px;"
        hx_url = f"/accept-data-extract-htmx?project_id={project_id}"
        html = f"""{success_msg}
<div id="geojson-preview-container"
     style="margin-top: 15px;">
    <div style="margin-bottom: 10px;">
        {_callout("info", info_msg)}
    </div>
    {map_html_content}
    <form id="accept-data-extract-form"
          style="{form_style}">
        <input type="hidden"
               name="data_extract_geojson"
               value='{geojson_str}' />
        <button
            id="accept-data-extract-btn"
            type="submit"
            hx-post="{hx_url}"
            hx-target="#osm-data-status"
            hx-swap="innerHTML"
            hx-include="#accept-data-extract-form"
            class="wa-button wa-button--primary"
            style="flex: 1;">
            Accept Data Extract
        </button>
    </form>
</div>"""
        return Response(
            content=html,
            media_type="text/html",
            status_code=200,
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error downloading OSM data via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/upload-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def upload_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    project_id: int = Parameter(),
) -> Response:
    """Upload custom GeoJSON file via HTMX and store in database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Read and validate file
        file_content = await data.read()

        # Validate file extension
        if not data.filename.lower().endswith((".geojson", ".json")):
            return Response(
                content=_callout(
                    "danger",
                    "Invalid file type. Please upload a .geojson or .json file.",
                ),
                media_type="text/html",
                status_code=400,
            )

        # Parse and validate with geojson-aoi-parser (same as validate-geojson endpoint)
        try:
            featcol = parse_aoi(
                settings.FMTM_DB_URL,
                file_content,
                merge=False,
            )
        except ValueError as e:
            return Response(
                content=_callout("danger", str(e)),
                media_type="text/html",
                status_code=422,
            )

        # Check if we have any features
        if not featcol.get("features", []):
            return Response(
                content=_callout(
                    "danger",
                    "No valid geometries found in GeoJSON.",
                ),
                media_type="text/html",
                status_code=422,
            )

        # Validate CRS (same as validate-geojson)
        await check_crs(featcol)

        feature_count = len(featcol.get("features", []))

        # Encode GeoJSON for the Accept button (don't save yet)
        geojson_str = json.dumps(featcol).replace('"', "&quot;")

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-upload",
            geojson_layers=[
                {
                    "data": featcol,
                    "name": "Data Extract",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        upload_success_msg = (
            f"✓ GeoJSON uploaded successfully! Found {feature_count} features."
        )
        upload_preview_msg = (
            f"Previewing {feature_count} features on map. Review the data below. "
            'If satisfied, click "Accept Data Extract" to save. '
            "Otherwise, try uploading a different file."
        )
        return Response(
            content=f"""
            {_callout("success", upload_success_msg)}
            <div id="geojson-preview-container" style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    {_callout("info", upload_preview_msg)}
                </div>
                {map_html_content}
                <form
                    id="accept-data-extract-form"
                    style="margin-top: 15px; display: flex; gap: 10px;"
                >
                    <input
                        type="hidden"
                        name="data_extract_geojson"
                        value='{geojson_str}'
                    />
                    <button
                        id="accept-data-extract-btn"
                        type="submit"
                        hx-post="/accept-data-extract-htmx?project_id={project_id}"
                        hx-target="#osm-data-status"
                        hx-swap="innerHTML"
                        hx-include="#accept-data-extract-form"
                        class="wa-button wa-button--primary"
                        style="flex: 1;"
                    >
                        Accept Data Extract
                    </button>
                </form>
            </div>
            """,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error uploading GeoJSON via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@get(
    path="/preview-geojson-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def preview_geojson_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Preview GeoJSON data extract in Leaflet map via HTMX."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get stored GeoJSON
        project = await DbProject.one(db, project_id)
        geojson_data = project.data_extract_geojson

        if not geojson_data:
            return Response(
                content=_callout(
                    "warning",
                    "No GeoJSON data found. Please download OSM data "
                    "or upload a GeoJSON file first.",
                ),
                media_type="text/html",
                status_code=404,
            )

        feature_count = len(geojson_data.get("features", []))

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer (always show)
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        # Add data extract layer
        geojson_layers.append(
            {
                "data": geojson_data,
                "name": f"Data Extract ({feature_count} features)",
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.3,
            }
        )

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-preview",
            geojson_layers=geojson_layers,
            height="500px",
            show_controls=True,
        )

        # Return HTML with Leaflet map
        preview_msg = (
            f"Previewing {feature_count} data features on map. "
            "Review the data, then continue to the next step."
        )
        map_html = f"""
        <div style="margin-top: 15px;">
            <div style="margin-bottom: 10px;">
                {_callout("info", preview_msg)}
            </div>
            {map_html_content}
        </div>
        """

        return Response(
            content=map_html,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(f"Error previewing GeoJSON via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/collect-new-data-only-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def collect_new_data_only_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Set setup to collect new data only without preloaded feature extract."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(
                data_extract_geojson={"type": "FeatureCollection", "features": []},
                task_areas_geojson={},
            ),
        )
        await db.commit()
        return Response(
            content=_callout(
                "success",
                "✓ Collect-new-data mode selected. "
                "Task splitting is skipped and you can continue.",
            ),
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )
    except Exception as e:
        log.error(f"Error enabling collect-new-data mode via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/submit-geojson-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def submit_geojson_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Save GeoJSON data extract to database (Step 2).

    Entity list creation is deferred to the final project creation step.
    This endpoint only saves the geometry data to the database.
    """
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get GeoJSON from request body (passed from download/upload endpoints)
        # or fall back to database if not in request (for backwards compatibility)
        geojson_data = None

        request_keys = list(data.keys()) if data else "None"
        log.debug(f"Submit data extract request received. Keys in data: {request_keys}")

        if "geojson-data" in data:
            # Get from request body (new flow - not saved to DB yet)
            try:
                geojson_str = data["geojson-data"]
                geojson_len = len(geojson_str) if geojson_str else 0
                log.debug(f"Received geojson-data, length: {geojson_len}")
                geojson_data = json.loads(geojson_str)
                parsed_feature_count = len(geojson_data.get("features", []))
                log.debug(
                    f"Successfully parsed GeoJSON with {parsed_feature_count} features"
                )
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse GeoJSON from request: {e}")
                return Response(
                    content=_callout(
                        "danger",
                        "Invalid GeoJSON data in request. Please try uploading again.",
                    ),
                    media_type="text/html",
                    status_code=400,
                )
            except (TypeError, KeyError) as e:
                log.error(f"Error accessing geojson-data from request: {e}")
                return Response(
                    content=_callout(
                        "danger",
                        "Error reading GeoJSON data from request.",
                    ),
                    media_type="text/html",
                    status_code=400,
                )
        else:
            # Fall back to database (backwards compatibility)
            log.debug("No geojson-data in request, falling back to database")
            project_db = await DbProject.one(db, project_id)
            geojson_data = project_db.data_extract_geojson

        if not geojson_data:
            return Response(
                content=_callout(
                    "warning",
                    "No GeoJSON data found. Please download OSM data "
                    "or upload a GeoJSON file first.",
                ),
                media_type="text/html",
                status_code=404,
            )

        # Delegate to shared service function (used by both HTMX and API routes)
        await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson_data,
        )
        log.info(
            f"Saved data extract to database for project {project_id} "
            "(entity list creation deferred to final step)"
        )

        saved_message = (
            "✓ Data extract successfully saved! You can now proceed to Step 3 "
            "(upload XLSForm) and then Step 4 (split tasks)."
        )
        return Response(
            content=(
                _callout("success", saved_message) + "<script>"
                "setTimeout(() => window.location.reload(), 2000);"
                "</script>"
            ),
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(
            f"Error submitting GeoJSON data extract via HTMX: {e}",
            exc_info=True,
        )
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


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
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Preview task boundaries and data extract together on a Leaflet map via HTMX."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get stored GeoJSON data extract
        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson

        if not data_extract:
            return Response(
                content=_callout(
                    "warning",
                    "No data extract found. Please download OSM data "
                    "or upload a GeoJSON file first.",
                ),
                media_type="text/html",
                status_code=404,
            )

        # Get task boundaries
        task_boundaries_json = await project_crud.get_task_geometry(db, project_id)
        task_boundaries = None
        is_no_splitting = False

        if task_boundaries_json:
            if isinstance(task_boundaries_json, str):
                try:
                    task_boundaries = json.loads(task_boundaries_json)
                except json.JSONDecodeError:
                    log.warning(
                        f"Failed to parse task boundaries JSON for project {project_id}"
                    )
            elif isinstance(task_boundaries_json, dict):
                task_boundaries = task_boundaries_json

        # Check if NO_SPLITTING was selected (empty dict or empty features)
        if (
            not task_boundaries
            or not task_boundaries.get("features")
            or len(task_boundaries.get("features", [])) == 0
        ):
            # Check if task_areas_geojson is explicitly set to {} (NO_SPLITTING)
            if project.task_areas_geojson == {}:
                is_no_splitting = True
            else:
                # No splitting has been done yet
                return Response(
                    content=_callout(
                        "warning",
                        "No task boundaries found. Please split the project into "
                        'tasks first using the "Split AOI" button above.',
                    ),
                    media_type="text/html",
                    status_code=200,  # Return 200 instead of 404 to show message
                )

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer (always show)
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        # Add data extract layer
        data_feature_count = len(data_extract.get("features", []))
        geojson_layers.append(
            {
                "data": data_extract,
                "name": f"Data Extract ({data_feature_count} features)",
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.3,
            }
        )

        # Add task boundaries layer (only if splitting was done)
        if not is_no_splitting and task_boundaries and task_boundaries.get("features"):
            task_count = len(task_boundaries.get("features", []))
            geojson_layers.append(
                {
                    "data": task_boundaries,
                    "name": f"Task Boundaries ({task_count} tasks)",
                    "color": "#ff7800",
                    "weight": 3,
                    "opacity": 1.0,
                    "fillOpacity": 0.1,
                }
            )

        # Use reusable map rendering function
        map_html_content = render_leaflet_map(
            map_id="leaflet-map-tasks-and-data",
            geojson_layers=geojson_layers,
            height="600px",
            show_controls=True,
        )

        # Generate preview message
        if is_no_splitting:
            preview_message = (
                f"Previewing whole AOI (no splitting) with "
                f"{data_feature_count} data features. "
                "The entire AOI will be used as a single task."
            )
        else:
            task_count = len(task_boundaries.get("features", []))
            preview_message = (
                f"Previewing {task_count} task boundaries and "
                f"{data_feature_count} data features together."
            )

        return Response(
            content=f"""
            <div style="margin-top: 15px;">
                <div style="margin-bottom: 10px;">
                    <wa-callout variant="info">
                        <span>{preview_message}</span>
                    </wa-callout>
                </div>
                {map_html_content}
            </div>
            """,
            media_type="text/html",
            status_code=200,
        )

    except Exception as e:
        log.error(
            f"Error previewing tasks and data extract via HTMX: {e}", exc_info=True
        )
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


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
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> Response:
    """Skip task splitting and use the whole AOI as a single task."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get project with outline
        project = await DbProject.one(db, project_id)

        if not project.outline:
            return Response(
                content=_callout(
                    "danger",
                    "Project outline not found. Cannot skip task splitting.",
                ),
                media_type="text/html",
                status_code=400,
            )

        # For ODK: Don't create task_boundaries dataset (it will be None/empty)
        # For QField: Don't create temp table (it won't exist)
        # The project generation will handle this by using the whole AOI

        # Store empty dict {} to indicate task splitting was skipped
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

        return Response(
            content=_callout(
                "success",
                "✓ Task splitting skipped. The whole AOI will be used as a "
                "single task. You can proceed to Step 4.",
            ),
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except Exception as e:
        log.error(f"Error skipping task split via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


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
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Split AOI into tasks using selected algorithm and return preview map."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Extract form data
        log.debug(
            f"Split AOI request data keys: {list(data.keys()) if data else 'None'}"
        )
        algorithm = data.get("algorithm", "").strip() if data else ""

        def parse_bool_flag(raw_value, default: bool = True) -> bool:
            """Parse truthy form values from URL-encoded payload."""
            if raw_value is None:
                return default
            if isinstance(raw_value, list):
                raw_value = raw_value[-1] if raw_value else default
            if isinstance(raw_value, bool):
                return raw_value
            return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}

        try:
            no_of_buildings = int(data.get("no_of_buildings", 10)) if data else 10
        except (ValueError, TypeError):
            no_of_buildings = 10

        try:
            dimension_meters = int(data.get("dimension_meters", 100)) if data else 100
        except (ValueError, TypeError):
            dimension_meters = 100

        include_roads = parse_bool_flag(
            data.get("include_roads") if data else None, default=True
        )
        include_rivers = parse_bool_flag(
            data.get("include_rivers") if data else None, default=True
        )
        include_railways = parse_bool_flag(
            data.get("include_railways") if data else None, default=True
        )
        include_aeroways = parse_bool_flag(
            data.get("include_aeroways") if data else None, default=True
        )

        log.debug(
            "Split AOI parameters: "
            f"algorithm={algorithm}, "
            f"no_of_buildings={no_of_buildings}, "
            f"dimension_meters={dimension_meters}, "
            f"include_roads={include_roads}, "
            f"include_rivers={include_rivers}, "
            f"include_railways={include_railways}, "
            f"include_aeroways={include_aeroways}"
        )

        if not algorithm or algorithm == "":
            return Response(
                content=_callout("danger", "Please select a splitting option."),
                media_type="text/html",
                status_code=400,
            )

        tasks_featcol = await split_aoi(
            db=db,
            project_id=project_id,
            algorithm=algorithm,
            no_of_buildings=no_of_buildings,
            dimension_meters=dimension_meters,
            include_roads=include_roads,
            include_rivers=include_rivers,
            include_railways=include_railways,
            include_aeroways=include_aeroways,
        )

        if tasks_featcol == {}:
            return Response(
                content=_callout(
                    "success",
                    "✓ Task splitting is not required for this project setup.",
                ),
                media_type="text/html",
                status_code=200,
                headers={"HX-Refresh": "true"},
            )

        task_count = len(tasks_featcol.get("features", []))

        # Store preview in a temporary location (we'll save it when user accepts)
        # For now, we'll encode it in the response and save it when Accept is clicked

        # Get project outline and data extract for map preview
        project = await DbProject.one(db, project_id)
        data_extract = project.data_extract_geojson

        # Prepare layers for map
        geojson_layers = []

        # Add AOI outline layer
        if project.outline:
            aoi_featcol = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": project.outline, "properties": {}}
                ],
            }
            geojson_layers.append(
                {
                    "data": aoi_featcol,
                    "name": "Project AOI",
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        # Add data extract layer if available
        if data_extract:
            data_feature_count = len(data_extract.get("features", []))
            geojson_layers.append(
                {
                    "data": data_extract,
                    "name": f"Data Extract ({data_feature_count} features)",
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            )

        # Add task boundaries layer
        geojson_layers.append(
            {
                "data": tasks_featcol,
                "name": f"Task Boundaries ({task_count} tasks)",
                "color": "#ff7800",
                "weight": 3,
                "opacity": 1.0,
                "fillOpacity": 0.1,
            }
        )

        map_html_content = render_leaflet_map(
            map_id="leaflet-map-split-preview",
            geojson_layers=geojson_layers,
            height="600px",
            show_controls=True,
        )

        # Encode the task areas GeoJSON for the Accept button
        tasks_geojson_str = json.dumps(tasks_featcol).replace('"', "&quot;")

        # Return success message with preview and Accept button
        data_extract_info = ""
        if data_extract:
            data_feature_count = len(data_extract.get("features", []))
            data_extract_info = f" and {data_feature_count} data features"

        split_success_msg = (
            "✓ AOI split successfully! Generated "
            f"{task_count} task areas using "
            f"{algorithm.replace('_', ' ').title()}."
        )
        split_preview_msg = (
            f"Previewing {task_count} task boundaries{data_extract_info}. "
            "Review the results below. If satisfied, click "
            '"Accept Task Choices" to save. Otherwise, adjust parameters '
            'above and click "Split Again" to regenerate.'
        )
        return Response(
            content=f"""
            {_callout("success", split_success_msg)}
            <div style="margin-top: 20px;">
                <div style="margin-bottom: 10px;">
                    {_callout("info", split_preview_msg)}
                </div>
                {map_html_content}
                <form
                    id="accept-split-form"
                    style="margin-top: 20px; display: flex; gap: 10px;
                    justify-content: center;"
                >
                    <input
                        type="hidden"
                        name="tasks_geojson"
                        value='{tasks_geojson_str}'
                    />
                    <button
                        id="accept-split-btn"
                        type="submit"
                        hx-post="/accept-split-htmx?project_id={project_id}"
                        hx-target="#split-status"
                        hx-swap="innerHTML"
                        hx-include="#accept-split-form"
                        class="wa-button wa-button--primary"
                        style="min-width: 200px"
                    >
                        Accept Task Choices
                    </button>
                </form>
            </div>
            """,
            media_type="text/html",
            status_code=200,
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error splitting AOI via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/accept-data-extract-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(mapper),
    },
)
async def accept_data_extract_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Accept and save the data extract to the database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        geojson_str = data.get("data_extract_geojson", "")
        if not geojson_str:
            data_keys = list(data.keys()) if data else "None"
            log.debug(f"Accept data extract data keys: {data_keys}")
            return Response(
                content=_callout("danger", "No data extract provided."),
                media_type="text/html",
                status_code=400,
            )

        # Parse the GeoJSON
        try:
            geojson_data = json.loads(geojson_str)
        except (json.JSONDecodeError, TypeError) as e:
            geojson_preview = (
                geojson_str[:100] if isinstance(geojson_str, str) else geojson_str
            )
            log.error(
                "Error parsing data extract GeoJSON: "
                f"{e}, type: {type(geojson_str)}, value: {geojson_preview}"
            )
            return Response(
                content=_callout("danger", "Invalid data extract format."),
                media_type="text/html",
                status_code=400,
            )

        feature_count = await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson_data,
        )
        log.info(
            f"Accepted and saved data extract with {feature_count} "
            f"features for project {project_id}"
        )

        accepted_msg = (
            f"✓ Data extract accepted! Saved {feature_count} features. "
            "Step 2 is now complete."
        )
        return Response(
            content=_callout("success", accepted_msg),
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error accepting data extract via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


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
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
    project_id: int = Parameter(),
) -> Response:
    """Accept and save the task split results to the database."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        # Get task areas GeoJSON from form data (hx-vals sends it as form data)
        tasks_geojson_str = data.get("tasks_geojson", "")
        if not tasks_geojson_str:
            data_keys = list(data.keys()) if data else "None"
            log.debug(f"Accept split data keys: {data_keys}")
            return Response(
                content=_callout("danger", "No task areas data provided."),
                media_type="text/html",
                status_code=400,
            )

        # Parse the GeoJSON
        try:
            tasks_geojson = json.loads(tasks_geojson_str)
        except (json.JSONDecodeError, TypeError) as e:
            tasks_preview = (
                tasks_geojson_str[:100]
                if isinstance(tasks_geojson_str, str)
                else tasks_geojson_str
            )
            log.error(
                "Error parsing task areas GeoJSON: "
                f"{e}, type: {type(tasks_geojson_str)}, value: {tasks_preview}"
            )
            return Response(
                content=_callout("danger", "Invalid task areas data format."),
                media_type="text/html",
                status_code=400,
            )

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
        success_message = _callout("success", "✓ Split tasks saved successfully")

        return Response(
            content=success_message,
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )

    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error accepting split via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/create-project-odk-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_odk_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Final step: Create project in ODK Central with all setup data."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        custom_odk_creds = None
        external_url = data.get("external_project_instance_url", "").strip()
        external_username = data.get("external_project_username", "").strip()
        external_password = data.get("external_project_password", "").strip()

        any_custom = any([external_url, external_username, external_password])
        all_custom = all([external_url, external_username, external_password])

        if any_custom and not all_custom:
            custom_creds_msg = (
                "Provide ODK URL, username, and password (all 3), or leave "
                "them all blank to use server defaults."
            )
            return Response(
                content=_callout("warning", custom_creds_msg),
                media_type="text/html",
                status_code=400,
            )

        if all_custom:
            custom_odk_creds = ODKCentral(
                external_project_instance_url=external_url,
                external_project_username=external_username,
                external_project_password=external_password,
            )

        odk_result = await finalize_odk_project(
            db=db, project_id=project_id, custom_odk_creds=custom_odk_creds
        )

        return Response(
            content=_build_odk_finalize_success_html(odk_result),
            media_type="text/html",
            status_code=200,
        )
    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error creating ODK project via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/create-project-qfield-htmx",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
)
async def create_project_qfield_htmx(
    request: HTMXRequest,
    db: AsyncConnection,
    current_user: ProjectUserDict,
    auth_user: AuthUser,
    project_id: int = Parameter(),
    data: dict = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response:
    """Final step: Create project in QField with all data."""
    project = current_user.get("project")
    if not project or project.id != project_id:
        return Response(
            content=_callout("danger", "Project not found or access denied."),
            media_type="text/html",
            status_code=404,
        )

    try:
        custom_qfield_creds = None
        qfield_url_param = data.get("qfield_cloud_url", "").strip()
        qfield_user = data.get("qfield_cloud_user", "").strip()
        qfield_password = data.get("qfield_cloud_password", "").strip()

        if qfield_url_param and qfield_user and qfield_password:
            custom_qfield_creds = QFieldCloud(
                qfield_cloud_url=qfield_url_param,
                qfield_cloud_user=qfield_user,
                qfield_cloud_password=qfield_password,
            )
        qfield_url = await finalize_qfield_project(
            db=db, project_id=project_id, custom_qfield_creds=custom_qfield_creds
        )

        qfield_success_html = (
            '<wa-callout variant="success"><span>'
            "✓ Project successfully created in QField! "
            f'<a href="{qfield_url}" target="_blank">'
            "View Project in QField"
            "</a></span></wa-callout>"
        )
        return Response(
            content=qfield_success_html,
            media_type="text/html",
            status_code=200,
            headers={"HX-Refresh": "true"},
        )
    except SvcValidationError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=400,
        )
    except ServiceError as e:
        return Response(
            content=_callout("danger", e.message),
            media_type="text/html",
            status_code=500,
        )
    except Exception as e:
        log.error(f"Error creating QField project via HTMX: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=_callout("danger", f"Error: {error_msg}"),
            media_type="text/html",
            status_code=500,
        )


@post(
    path="/validate-geojson",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def validate_geojson(
    request: HTMXRequest,
    db: AsyncConnection,
    auth_user: AuthUser,
    data: dict = Body(media_type=RequestEncodingType.JSON),
) -> Response:
    """Validate and normalize GeoJSON for project area upload.

    Accepts GeoJSON (Feature, FeatureCollection, or Geometry) and returns
    a normalized, optionally merged single polygon FeatureCollection suitable for use
    as a project area of interest (AOI).

    Args:
        request: Incoming HTMX request (unused, kept for route signature).
        db: Async DB connection provided by dependency injection.
        auth_user: Authenticated user context from `login_required`.
        data: Request body containing:
            - geojson: The GeoJSON to validate and normalize
            - merge_geometries: Optional boolean to merge geometries using convex hull
    """
    try:
        geojson_input = data.get("geojson")
        merge_geometries = data.get("merge_geometries", False)

        if not geojson_input:
            return Response(
                content=json.dumps({"error": "GeoJSON is required"}),
                media_type="application/json",
                status_code=400,
            )

        # Normalize and validate AOI using geojson-aoi-parser (PostGIS-backed).
        merged_featcol = parse_aoi(
            settings.FMTM_DB_URL,
            geojson_input,
            merge=bool(merge_geometries),
        )

        if not merged_featcol.get("features", []):
            return Response(
                content=json.dumps(
                    {
                        "error": (
                            "No polygon geometries found. "
                            "Project area must be a polygon."
                        )
                    }
                ),
                media_type="application/json",
                status_code=422,
            )

        # Return normalized GeoJSON
        # If single feature, return it directly; otherwise return FeatureCollection
        result_geojson = (
            merged_featcol["features"][0]
            if len(merged_featcol.get("features", [])) == 1
            else merged_featcol
        )

        # Calculate area and include size feedback
        response_body: dict = {"geojson": result_geojson}
        try:
            geom = result_geojson
            if geom.get("type") == "Feature":
                geom = geom.get("geometry", geom)
            elif geom.get("type") == "FeatureCollection":
                features = geom.get("features", [])
                if features:
                    geom = features[0].get("geometry", features[0])
            area_km2 = geojson_area_km2(geom)
            response_body["area_km2"] = round(area_km2, 2)
            if area_km2 > AREA_LIMIT_KM2:
                response_body["warning"] = (
                    f"Area is {area_km2:,.0f} km², which exceeds the "
                    f"{AREA_LIMIT_KM2:,} km² limit. "
                    "Please select a smaller area."
                )
            elif area_km2 > AREA_WARN_KM2:
                response_body["warning"] = (
                    f"Area is {area_km2:,.0f} km². Large areas "
                    f"(>{AREA_WARN_KM2} km²) may take longer to process. "
                    f"The data extract API is limited to 200 km²."
                )
        except Exception as e:
            log.warning(f"Could not calculate area: {e}")

        return Response(
            content=json.dumps(response_body),
            media_type="application/json",
            status_code=200,
        )

    except HTTPException as e:
        # Convert HTTP exceptions to JSON format
        return Response(
            content=json.dumps({"error": e.detail}),
            media_type="application/json",
            status_code=e.status_code,
        )
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=422,
        )
    except Exception as e:
        log.error(f"Error validating GeoJSON: {e}", exc_info=True)
        error_msg = str(e) if hasattr(e, "__str__") else "An unexpected error occurred"
        return Response(
            content=json.dumps({"error": error_msg}),
            media_type="application/json",
            status_code=500,
        )
