"""Parsing and form helpers for project-create HTMX routes."""

import ast
import json
from urllib.parse import quote
from uuid import uuid4

from app.db.enums import FieldMappingApp
from app.i18n import _


def outline_json_error() -> str:
    """Return localized validation error for invalid project outline JSON."""
    return _(
        "Project area must be valid JSON "
        "(GeoJSON Polygon, MultiPolygon, Feature, or FeatureCollection)."
    )


def first_form_value(value: object) -> str:
    """Extract first non-empty scalar value from form payload variants."""
    while isinstance(value, (list, tuple)):
        if not value:
            return ""
        value = next((item for item in value if item not in (None, "")), value[0])

    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    return str(value or "").strip()


def coerce_single_form_value(value: object) -> object:
    """Collapse list/tuple form fields into a single representative value."""
    while isinstance(value, (list, tuple)):
        if not value:
            return {}
        value = next((item for item in value if item not in (None, "")), value[0])
    return value


def parse_outline_json_string(value_str: str) -> object | None:
    """Parse outline JSON text with Python-literal fallback for legacy inputs."""
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(value_str)
        except (SyntaxError, ValueError):
            return None


def parse_outline_payload(raw_value: object) -> dict:
    """Normalize submitted outline payload into a GeoJSON-like dictionary."""
    if isinstance(raw_value, dict):
        return raw_value

    value: object = coerce_single_form_value(raw_value)

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
        parsed = parse_outline_json_string(value_str)
    else:
        try:
            parsed = json.loads(str(value))
        except (TypeError, ValueError):
            parsed = None

    if isinstance(parsed, dict):
        return parsed

    if isinstance(parsed, (list, tuple)) and len(parsed) == 1:
        return parse_outline_payload(parsed[0])

    raise ValueError(outline_json_error())


def normalize_field_mapping_app(value: object) -> str:
    """Normalize field-mapping app form values to canonical enum strings."""
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


def project_form_error(message: str) -> str:
    """Build standard form-level error callout HTML for project-create flows."""
    return (
        '<div id="form-error"'
        ' style="margin-bottom: 16px;'
        ' display: block;">'
        '<wa-callout variant="danger">'
        '<span id="form-error-message">'
        f"{message}"
        "</span></wa-callout></div>"
    )


def build_unique_simple_project_name(project_name: str) -> str:
    """Append a short random suffix to keep simple-project names unique."""
    return f"{project_name} {uuid4().hex[:8]}"


def parse_project_create_form(data: dict) -> tuple[str, str, str, list[str], dict]:
    """Parse and normalize form data for full project-create submissions."""
    project_name = first_form_value(data.get("project_name", ""))
    description = first_form_value(data.get("description", ""))
    field_mapping_app = normalize_field_mapping_app(
        first_form_value(data.get("field_mapping_app", ""))
    )
    hashtags_str = first_form_value(data.get("hashtags", ""))
    outline = parse_outline_payload(data.get("outline", ""))
    hashtags = [tag.strip() for tag in hashtags_str.split(",") if tag.strip()]
    return project_name, description, field_mapping_app, hashtags, outline


def to_bool_form_value(value: object, default: bool = False) -> bool:
    """Convert mixed form values into booleans using explicit string semantics."""
    if value in ("", None):
        return default
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def login_prompt_path(next_path: str) -> str:
    """Build login redirect URL preserving desired post-auth destination."""
    return f"/login?return_to={quote(next_path, safe='')}"
