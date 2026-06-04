"""Handlers for setup-step data extract HTMX workflow."""

import logging

from geojson_aoi import parse_aoi
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.response import Response, Template
from psycopg import AsyncConnection

from app.config import settings
from app.db.models import DbProject
from app.helpers.geometry_utils import check_crs
from app.htmx.map_helpers import render_leaflet_map
from app.i18n import _
from app.projects import project_schemas
from app.projects.project_services import (
    ServiceError,
    download_osm_data,
    save_data_extract,
)
from app.projects.project_services import ValidationError as SvcValidationError

from ..htmx_helpers import callout as _callout
from .setup_step_extract_helpers import (
    get_submitted_geojson_data as _get_submitted_geojson_data,
)
from .setup_step_responses import (
    build_data_extract_preview_response as _build_data_extract_preview_response,
)
from .setup_step_responses import hx_trigger_response as _hx_trigger_response
from .setup_step_responses import service_error_response as _service_error_response
from .setup_step_responses import (
    unexpected_error_response as _unexpected_error_response,
)

log = logging.getLogger(__name__)


async def handle_download_osm_data(
    db: AsyncConnection,
    project_id: int,
    osm_category: str,
    geom_type: str,
    centroid: bool,
) -> Response:
    """Download an OSM extract and return the review preview fragment.

    The extract is persisted to ``data_extract_geojson`` here (replacing any
    prior staged extract) so the Accept form is a no-body confirm rather than
    a round-trip of the entire GeoJSON. If the user discards or re-downloads
    before accepting, the staged extract is overwritten or cleared.
    """
    try:
        featcol_single_geom_type = await download_osm_data(
            db=db,
            project_id=project_id,
            osm_category=osm_category,
            geom_type=geom_type,
            centroid=centroid,
        )
        feature_count = await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=featcol_single_geom_type,
        )

        map_html_content = render_leaflet_map(
            map_id="leaflet-map-download",
            geojson_layers=[
                {
                    "data": featcol_single_geom_type,
                    "name": _("Data Extract"),
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        status_message = _(
            "OSM data downloaded successfully! Found %(feature_count)s features."
        ) % {"feature_count": feature_count}
        preview_message = _(
            "Previewing %(feature_count)s features on map. Review the data "
            'below. If satisfied, click "Accept Data Extract" to save. '
            "Otherwise, try downloading again with different parameters."
        ) % {"feature_count": feature_count}
        return _build_data_extract_preview_response(
            status_message=status_message,
            preview_message=preview_message,
            map_html_content=map_html_content,
            project_id=project_id,
        )
    except (SvcValidationError, ServiceError) as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(f"Error downloading OSM data via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_upload_geojson(
    db: AsyncConnection,
    data: UploadFile,
    project_id: int,
) -> Response:
    """Validate an uploaded GeoJSON extract and return the preview fragment.

    Like the OSM download path, the parsed extract is persisted to
    ``data_extract_geojson`` here so Accept is a no-body confirm.
    """
    try:
        file_content = await data.read()

        if not data.filename.lower().endswith((".geojson", ".json")):
            return Response(
                content=_callout(
                    "danger",
                    _("Invalid file type. Please upload a .geojson or .json file."),
                ),
                media_type="text/html",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            featcol = parse_aoi(
                settings.FTM_DB_URL,
                file_content,
                merge=False,
            )
        except ValueError as e:
            return Response(
                content=_callout("danger", str(e)),
                media_type="text/html",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not featcol.get("features", []):
            return Response(
                content=_callout(
                    "danger",
                    _("No valid geometries found in GeoJSON."),
                ),
                media_type="text/html",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        await check_crs(featcol)

        feature_count = await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=featcol,
        )

        map_html_content = render_leaflet_map(
            map_id="leaflet-map-upload",
            geojson_layers=[
                {
                    "data": featcol,
                    "name": _("Data Extract"),
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.3,
                }
            ],
            height="500px",
            show_controls=False,
        )

        upload_success_msg = _(
            "✓ GeoJSON uploaded successfully! Found %(feature_count)s features."
        ) % {"feature_count": feature_count}
        upload_preview_msg = _(
            "Previewing %(feature_count)s features on map. Review the data "
            'below. If satisfied, click "Accept Data Extract" to save. '
            "Otherwise, try uploading a different file."
        ) % {"feature_count": feature_count}
        return _build_data_extract_preview_response(
            status_message=upload_success_msg,
            preview_message=upload_preview_msg,
            map_html_content=map_html_content,
            project_id=project_id,
        )

    except SvcValidationError as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(f"Error uploading GeoJSON via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_preview_geojson(db: AsyncConnection, project_id: int) -> Response:
    """Render a saved project data extract preview."""
    try:
        project = await DbProject.one(db, project_id)
        geojson_data = project.data_extract_geojson

        if not geojson_data:
            return Response(
                content=_callout(
                    "warning",
                    _(
                        "No GeoJSON data found. Please download OSM data or "
                        "upload a GeoJSON file first."
                    ),
                ),
                media_type="text/html",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        feature_count = len(geojson_data.get("features", []))
        geojson_layers = []

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
                    "name": _("Project AOI"),
                    "color": "#d63f3f",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.1,
                }
            )

        geojson_layers.append(
            {
                "data": geojson_data,
                "name": _("Data Extract (%(feature_count)s features)")
                % {"feature_count": feature_count},
                "color": "#3388ff",
                "weight": 2,
                "opacity": 0.8,
                "fillOpacity": 0.3,
            }
        )

        map_html_content = render_leaflet_map(
            map_id="leaflet-map-preview",
            geojson_layers=geojson_layers,
            height="500px",
            show_controls=True,
        )

        preview_msg = _(
            "Previewing %(feature_count)s data features on map. Review the "
            "data, then continue to the next step."
        ) % {"feature_count": feature_count}

        return Template(
            template_name="partials/project_details/fragments/map_preview.html",
            context={
                "preview_message": preview_msg,
                "map_html_content": map_html_content,
            },
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        log.error(f"Error previewing GeoJSON via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_collect_new_data_only(
    db: AsyncConnection, project_id: int
) -> Response:
    """Persist an empty data extract for collect-new-data-only projects."""
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
        return _hx_trigger_response(
            _callout(
                "success",
                _(
                    "✓ Collect-new-data mode selected. Task splitting is "
                    "skipped and you can continue."
                ),
            ),
            event="project-setup:step3-complete",
            payload={
                "projectId": project_id,
                "step": 3,
                "nextStep": 4,
                "code": "collect_new_data_enabled",
            },
        )
    except Exception as e:
        log.error(f"Error enabling collect-new-data mode via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_submit_geojson_data_extract(
    db: AsyncConnection,
    project_id: int,
    data: dict,
) -> Response:
    """Persist a submitted custom GeoJSON data extract."""
    try:
        request_keys = list(data.keys()) if data else "None"
        log.debug(f"Submit data extract request received. Keys in data: {request_keys}")
        geojson_data, error_response = await _get_submitted_geojson_data(
            db,
            project_id,
            data or {},
        )
        if error_response or not geojson_data:
            return error_response or Response(
                content=_callout(
                    "warning",
                    _(
                        "No GeoJSON data found. Please download OSM data or "
                        "upload a GeoJSON file first."
                    ),
                ),
                media_type="text/html",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        await save_data_extract(
            db=db,
            project_id=project_id,
            geojson_data=geojson_data,
        )
        log.info(
            f"Saved data extract to database for project {project_id} "
            "(entity list creation deferred to final step)"
        )

        saved_message = _(
            "✓ Data extract successfully saved! You can now proceed to Step 4 "
            "(split tasks)."
        )
        return _hx_trigger_response(
            _callout("success", saved_message),
            event="project-setup:step3-complete",
            payload={
                "projectId": project_id,
                "step": 3,
                "nextStep": 4,
                "code": "data_extract_saved",
            },
        )

    except SvcValidationError as e:
        return _service_error_response(e)
    except ServiceError as e:
        return _service_error_response(e)
    except Exception as e:
        log.error(
            f"Error submitting GeoJSON data extract via HTMX: {e}",
            exc_info=True,
        )
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_accept_data_extract(
    db: AsyncConnection,
    project_id: int,
) -> Response:
    """Confirm the staged data extract and advance to step 4.

    The extract was already persisted on download/upload. Accept is a
    no-body POST that verifies an extract is present and emits the
    step3-complete event; the client reloads to /projects/{id}.
    """
    try:
        project = await DbProject.one(db, project_id)
        geojson_data = project.data_extract_geojson if project else None
        features = (
            geojson_data.get("features", []) if isinstance(geojson_data, dict) else []
        )

        if not features:
            return Response(
                content=_callout(
                    "warning",
                    _(
                        "No data extract is staged. Please download OSM data "
                        "or upload a GeoJSON file first."
                    ),
                ),
                media_type="text/html",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        feature_count = len(features)
        log.info(
            f"Accepted staged data extract with {feature_count} "
            f"features for project {project_id}"
        )

        accepted_msg = _(
            "✓ Data extract accepted! Saved %(feature_count)s features. Step "
            "3 is now complete."
        ) % {"feature_count": feature_count}
        return _hx_trigger_response(
            _callout("success", accepted_msg),
            event="project-setup:step3-complete",
            payload={
                "projectId": project_id,
                "step": 3,
                "nextStep": 4,
                "code": "data_extract_accepted",
                "featureCount": feature_count,
            },
        )

    except Exception as e:
        log.error(f"Error accepting data extract via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)


async def handle_discard_data_extract(
    db: AsyncConnection,
    project_id: int,
) -> Response:
    """Clear the staged extract so the user can choose a data source again.

    Called when the user clicks "Discard" on the preview. Also nulls
    ``task_areas_geojson`` because any split would have been based on the
    discarded extract.
    """
    try:
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(
                data_extract_geojson=None,
                task_areas_geojson=None,
            ),
        )
        await db.commit()
        log.info(f"Discarded staged data extract for project {project_id}")
        return Response(
            content=_callout(
                "info",
                _("Data extract discarded. Choose a data source above to try again."),
            ),
            media_type="text/html",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        log.error(f"Error discarding data extract via HTMX: {e}", exc_info=True)
        return _unexpected_error_response(str(e) if hasattr(e, "__str__") else None)
