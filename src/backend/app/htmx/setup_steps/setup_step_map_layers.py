"""Map-layer and preview helpers for setup-step HTMX routes."""

# ruff: noqa: D103

import json

from litestar import status_codes as status
from litestar.response import Response, Template

from app.htmx.map_helpers import render_leaflet_map
from app.i18n import _

from ..htmx_helpers import callout as _callout


def project_outline_layer(project) -> dict | None:
    if not project.outline:
        return None

    return {
        "data": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": project.outline, "properties": {}}
            ],
        },
        "name": _("Project AOI"),
        "color": "#d63f3f",
        "weight": 2,
        "opacity": 0.8,
        "fillOpacity": 0.1,
    }


def data_extract_layer(data_extract: dict) -> dict:
    data_feature_count = len(data_extract.get("features", []))
    return {
        "data": data_extract,
        "name": _("Data Extract (%(data_feature_count)s features)")
        % {"data_feature_count": data_feature_count},
        "color": "#3388ff",
        "weight": 2,
        "opacity": 0.8,
        "fillOpacity": 0.3,
    }


def task_boundaries_layer(task_boundaries: dict) -> dict:
    task_count = len(task_boundaries.get("features", []))
    return {
        "data": task_boundaries,
        "name": _("Task Boundaries (%(task_count)s tasks)")
        % {"task_count": task_count},
        "color": "#ff7800",
        "weight": 3,
        "opacity": 1.0,
        "fillOpacity": 0.1,
        "popup_options": {
            "showLayerName": False,
            "propertyLabels": {
                "task_id": _("Task ID"),
                "building_count": _("Building Count"),
            },
            "propertyOrder": ["task_id", "building_count"],
        },
    }


def task_preview_state(
    project, task_boundaries: dict | None
) -> tuple[bool, Response | None]:
    has_features = bool(task_boundaries and task_boundaries.get("features"))
    if has_features:
        return False, None
    if project.task_areas_geojson == {}:
        return True, None
    return False, Response(
        content=_callout(
            "warning",
            _(
                "No task boundaries found. Please split the project into tasks "
                'first using the "Split AOI" button above.'
            ),
        ),
        media_type="text/html",
        status_code=status.HTTP_200_OK,
    )


def build_preview_layers(
    project, data_extract: dict, task_boundaries: dict | None, is_no_splitting: bool
) -> list[dict]:
    geojson_layers = []
    outline_layer = project_outline_layer(project)
    if outline_layer:
        geojson_layers.append(outline_layer)
    geojson_layers.append(data_extract_layer(data_extract))
    if not is_no_splitting and task_boundaries and task_boundaries.get("features"):
        geojson_layers.append(task_boundaries_layer(task_boundaries))
    return geojson_layers


def build_split_preview_response(
    project_id: int,
    algorithm: str,
    tasks_featcol: dict,
    data_extract: dict | None,
    project,
) -> Template:
    task_count = len(tasks_featcol.get("features", []))
    geojson_layers = []
    outline_layer = project_outline_layer(project)
    if outline_layer:
        geojson_layers.append(outline_layer)
    if data_extract:
        geojson_layers.append(data_extract_layer(data_extract))
    geojson_layers.append(task_boundaries_layer(tasks_featcol))

    map_html_content = render_leaflet_map(
        map_id="leaflet-map-split-preview",
        geojson_layers=geojson_layers,
        height="600px",
        show_controls=True,
    )
    tasks_geojson_str = json.dumps(tasks_featcol)
    data_extract_info = ""
    if data_extract:
        data_feature_count = len(data_extract.get("features", []))
        data_extract_info = f" and {data_feature_count} data features"

    split_success_msg = _(
        "✓ AOI split successfully! Generated %(task_count)s task areas using "
        "%(algorithm)s."
    ) % {
        "task_count": task_count,
        "algorithm": algorithm.replace("_", " ").title(),
    }
    split_preview_msg = _(
        "Previewing %(task_count)s task boundaries%(data_extract_info)s. "
        'Review the results below. If satisfied, click "Accept Task Choices" '
        'to save. Otherwise, adjust parameters above and click "Split Again" '
        "to regenerate."
    ) % {
        "task_count": task_count,
        "data_extract_info": data_extract_info,
    }
    return Template(
        template_name="partials/project_details/fragments/split_preview.html",
        context={
            "project_id": project_id,
            "split_success_msg": split_success_msg,
            "split_preview_msg": split_preview_msg,
            "map_html_content": map_html_content,
            "tasks_geojson_str": tasks_geojson_str,
        },
        media_type="text/html",
        status_code=status.HTTP_200_OK,
        headers={
            "HX-Trigger": json.dumps(
                {
                    "project-setup:step4-preview-ready": {
                        "projectId": project_id,
                        "taskCount": task_count,
                        "code": "split_preview_ready",
                    }
                }
            )
        },
    )
