"""Validate and save task plans (see docs/task-plan.md)."""

import math
import re
import unicodedata

from psycopg import AsyncConnection

from app.helpers.geometry_utils import stamp_missing_task_ids
from app.i18n import _
from app.projects.project_services import ValidationError, save_task_areas

MAX_TASKS = 5000
MAX_NAME_LENGTH = 100
MAX_COMMENT_LENGTH = 500
# Matches ODK Central's property-name charset, so labels stay sync-safe.
GROUP_PATTERN = re.compile(r"^[A-Za-z0-9_-]*$")
COLOUR_PATTERN = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _clean_text(value: object) -> str:
    """Stringify and strip control/format characters."""
    text = "" if value is None else str(value)
    return "".join(
        c for c in text if unicodedata.category(c) not in ("Cc", "Cf")
    ).strip()


def _max_length_error(max_length: int) -> ValidationError:
    return ValidationError(
        _("Values must be %(max_length)s characters or fewer.")
        % {"max_length": max_length}
    )


def _clean_properties(properties: dict) -> dict:
    """Keep the known task plan properties, validated; drop the rest."""
    cleaned = {"task_id": properties.get("task_id")}

    group = _clean_text(properties.get("assigned_group"))
    if not GROUP_PATTERN.match(group):
        raise ValidationError(
            _(
                "Group labels may only contain letters, numbers, "
                "hyphens and underscores."
            )
        )
    for key, value, max_length in (
        ("assigned_group", group, MAX_NAME_LENGTH),
        ("assigned_to", _clean_text(properties.get("assigned_to")), MAX_NAME_LENGTH),
        ("comment", _clean_text(properties.get("comment")), MAX_COMMENT_LENGTH),
    ):
        if len(value) > max_length:
            raise _max_length_error(max_length)
        if value:
            cleaned[key] = value

    colour = _clean_text(properties.get("colour"))
    if colour:
        if not COLOUR_PATTERN.match(colour):
            raise ValidationError(_("Colours must be hex values such as #d63f3f."))
        if len(colour) == 4:  # noqa: PLR2004 (#rgb -> #rrggbb)
            colour = "#" + "".join(c * 2 for c in colour[1:])
        cleaned["colour"] = colour.lower()
    return cleaned


def _valid_position(position: object) -> bool:
    if not isinstance(position, list) or len(position) < 2:  # noqa: PLR2004
        return False
    lon, lat = position[0], position[1]
    if not all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        for v in (lon, lat)
    ):
        return False
    return -180 <= lon <= 180 and -90 <= lat <= 90  # noqa: PLR2004


def _valid_polygon(rings: object) -> bool:
    return (
        isinstance(rings, list)
        and len(rings) > 0
        and all(
            isinstance(ring, list)
            and len(ring) >= 4  # noqa: PLR2004
            and all(_valid_position(p) for p in ring)
            for ring in rings
        )
    )


def _valid_geometry(geometry: object) -> bool:
    if not isinstance(geometry, dict):
        return False
    coordinates = geometry.get("coordinates")
    if geometry.get("type") == "Polygon":
        return _valid_polygon(coordinates)
    if geometry.get("type") == "MultiPolygon":
        return (
            isinstance(coordinates, list)
            and len(coordinates) > 0
            and all(_valid_polygon(p) for p in coordinates)
        )
    return False


def _clean_feature(feature: object, number: int) -> dict:
    geometry = feature.get("geometry") if isinstance(feature, dict) else None
    if not _valid_geometry(geometry):
        raise ValidationError(
            _("Task %(number)s must be a Polygon with WGS84 coordinates.")
            % {"number": number}
        )
    properties = feature.get("properties")
    try:
        cleaned_properties = _clean_properties(
            properties if isinstance(properties, dict) else {}
        )
    except ValidationError as e:
        raise ValidationError(
            _("Task %(number)s: %(error)s") % {"number": number, "error": e.message}
        ) from e
    return {
        "type": "Feature",
        "geometry": {"type": geometry["type"], "coordinates": geometry["coordinates"]},
        "properties": cleaned_properties,
    }


def clean_task_plan(plan: object) -> dict:
    """Validate a task plan and return a clean copy with stamped task ids.

    Raises:
        ValidationError: with a user-facing message.
    """
    features = plan.get("features") if isinstance(plan, dict) else None
    if (
        not isinstance(plan, dict)
        or plan.get("type") != "FeatureCollection"
        or not isinstance(features, list)
    ):
        raise ValidationError(_("A task plan must be a GeoJSON FeatureCollection."))
    if not features:
        raise ValidationError(_("The task plan has no tasks."))
    if len(features) > MAX_TASKS:
        raise ValidationError(
            _("A task plan can have at most %(max_tasks)s tasks.")
            % {"max_tasks": MAX_TASKS}
        )

    cleaned_features = [
        _clean_feature(feature, number) for number, feature in enumerate(features, 1)
    ]
    params = plan.get("params")
    return stamp_missing_task_ids(
        {
            "type": "FeatureCollection",
            "task_plan_version": 1,
            "algorithm": _clean_text(plan.get("algorithm"))[:50] or "MANUAL",
            "params": params if isinstance(params, dict) else {},
            "features": cleaned_features,
        }
    )


async def save_task_plan(db: AsyncConnection, project_id: int, plan: object) -> int:
    """Validate and store a task plan, returning the task count."""
    return await save_task_areas(db, project_id, clean_task_plan(plan))
