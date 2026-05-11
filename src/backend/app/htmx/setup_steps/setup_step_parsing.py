"""Parsing helpers for setup-step HTMX routes."""

# ruff: noqa: D103

import html
import json
import logging

from litestar.response import Response

from ..setup_steps.setup_step_responses import html_error_response

log = logging.getLogger(__name__)


def parse_json_payload(
    raw_value, invalid_message: str, log_prefix: str
) -> tuple[dict | None, Response | None]:
    try:
        normalized_value = (
            html.unescape(raw_value) if isinstance(raw_value, str) else raw_value
        )
        return json.loads(normalized_value), None
    except (json.JSONDecodeError, TypeError) as e:
        preview = raw_value[:100] if isinstance(raw_value, str) else raw_value
        log.error(
            "%s: %s, type: %s, value: %s", log_prefix, e, type(raw_value), preview
        )
        return None, html_error_response(invalid_message, 400)


def parse_bool_flag(raw_value, default: bool = True) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, list):
        raw_value = raw_value[-1] if raw_value else default
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def parse_int_form_value(raw_value, default: int) -> int:
    try:
        return int(raw_value)
    except (ValueError, TypeError):
        return default


def parse_split_form_options(data: dict | None) -> dict:
    payload = data or {}
    return {
        "algorithm": payload.get("algorithm", "").strip(),
        "no_of_buildings": parse_int_form_value(payload.get("no_of_buildings", 10), 10),
        "no_of_tasks": parse_int_form_value(payload.get("no_of_tasks", 10), 10),
        "dimension_meters": parse_int_form_value(
            payload.get("dimension_meters", 100), 100
        ),
        "include_roads": parse_bool_flag(payload.get("include_roads"), default=True),
        "include_rivers": parse_bool_flag(payload.get("include_rivers"), default=True),
        "include_railways": parse_bool_flag(
            payload.get("include_railways"), default=True
        ),
        "include_aeroways": parse_bool_flag(
            payload.get("include_aeroways"), default=True
        ),
    }


def parse_task_boundaries_json(task_boundaries_json, project_id: int) -> dict | None:
    if isinstance(task_boundaries_json, dict):
        return task_boundaries_json
    if not isinstance(task_boundaries_json, str):
        return None

    try:
        return json.loads(task_boundaries_json)
    except json.JSONDecodeError:
        log.warning("Failed to parse task boundaries JSON for project %s", project_id)
        return None
