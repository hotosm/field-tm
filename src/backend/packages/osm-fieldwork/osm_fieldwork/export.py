"""Normalise survey submissions from different apps into one GeoJSON format.

Every feature gets the same core properties, followed by the form answers:

    id, task_id, osm_id, status, username, submitted_at, attachments

Adapters (`from_odk`, `from_qfield`) only map app-specific metadata;
`normalise_feature` does the rest, so new apps (e.g. Kobo) are small.
"""

import json
from io import BytesIO

import pandas as pd

CORE_FIELDS = (
    "id",
    "task_id",
    "osm_id",
    "status",
    "username",
    "submitted_at",
    "attachments",
)

# Field-TM form internals and device metadata: not survey answers
DROP_FIELDS = {
    "start",
    "end",
    "today",
    "phonenumber",
    "deviceid",
    "email",
    "username",
    "osm_username",
    "warmup",
    "mapping_mode",
    "task",
    "selected_task_id",
    "feature",
    "new_feature",
    "xid",
    "xlocation",
    "created_by",
    "fill",
    "marker-color",
    "stroke",
    "stroke-width",
    "instanceID",
    "fid",
    "uuid",
}

MEDIA_TYPES = {"image", "audio", "video", "file", "background-audio"}


def media_fields(xlsform: bytes) -> set[str]:
    """Names of the attachment (photo, audio, etc) questions in an XLSForm."""
    survey = pd.read_excel(BytesIO(xlsform), sheet_name="survey", engine="calamine")
    return {
        name
        for field_type, name in zip(survey["type"], survey["name"])
        if isinstance(field_type, str)
        and isinstance(name, str)
        and field_type.split()[0] in MEDIA_TYPES
    }


def javarosa_to_geojson(value: str) -> dict | None:
    """'lat lon alt acc;...' to a Point, LineString or (closed) Polygon."""
    if not value or not isinstance(value, str):
        return None

    coordinates = []
    for point in value.strip().split(";"):
        parts = point.split()
        if len(parts) < 2:
            continue
        try:
            coordinates.append([float(parts[1]), float(parts[0])])
        except ValueError:
            continue

    if not coordinates:
        return None
    if len(coordinates) == 1:
        return {"type": "Point", "coordinates": coordinates[0]}
    if len(coordinates) >= 4 and coordinates[0] == coordinates[-1]:
        return {"type": "Polygon", "coordinates": [coordinates]}
    return {"type": "LineString", "coordinates": coordinates}


def _is_geojson(value) -> bool:
    return isinstance(value, dict) and "type" in value and "coordinates" in value


def _flatten(record: dict, out: dict | None = None, path: str = "") -> dict:
    """Flatten nested groups to leaf names (`group/name` on a clash)."""
    out = {} if out is None else out
    for key, value in record.items():
        if key.startswith("__") or "@odata" in key:
            continue
        name = key.rsplit("/", 1)[-1]
        full = f"{path}/{name}" if path else name
        if isinstance(value, dict) and not _is_geojson(value):
            _flatten(value, out, full)
        else:
            out[full if name in out else name] = value
    return out


def _find_media(value, media: set[str], found: list) -> list:
    """Collect attachment filenames, including inside repeats."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key.rsplit("/", 1)[-1] in media and isinstance(item, str) and item:
                found.append(item)
            else:
                _find_media(item, media, found)
    elif isinstance(value, list):
        for item in value:
            _find_media(item, media, found)
    return found


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value or None


def _scalar(value):
    """GeoJSON viewers need flat values, so nest as a JSON string."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def normalise_feature(  # noqa: PLR0913
    answers: dict,
    geometry: dict | None,
    *,
    feature_id: str | None,
    username: str | None = None,
    submitted_at: str | None = None,
    attachments: list[str] | None = None,
) -> dict:
    """Build a standard feature from flat answers plus metadata."""
    properties = {
        "id": feature_id,
        "task_id": _to_int(answers.get("task_id")),
        "osm_id": _to_int(answers.get("xid", answers.get("osm_id"))),
        "status": answers.get("status") or None,
        "username": username or None,
        "submitted_at": submitted_at or None,
        "attachments": attachments or [],
    }
    for key, value in answers.items():
        if key not in DROP_FIELDS and key not in properties and key != "osm_id":
            properties[key] = _scalar(value)
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def from_odk(record: dict, media: set[str] = frozenset()) -> dict:
    """An ODK Central OData submission (use `$expand=*` to include repeats)."""
    answers = _flatten(record)
    geometry = next(
        (answers[k] for k in ("new_feature", "warmup") if _is_geojson(answers.get(k))),
        None,
    )
    if answers.get("xlocation"):
        geometry = javarosa_to_geojson(answers["xlocation"]) or geometry
    system = record.get("__system") or {}
    return normalise_feature(
        answers,
        geometry,
        feature_id=record.get("__id") or answers.get("instanceID"),
        username=answers.get("osm_username")
        or answers.get("username")
        or system.get("submitterName"),
        submitted_at=system.get("submissionDate"),
        attachments=_find_media(record, media, []),
    )


def from_qfield(feature: dict, media: set[str] = frozenset()) -> dict:
    """A GeoJSON feature from the QField `survey` layer."""
    answers = feature.get("properties") or {}
    geometry = feature.get("geometry") or javarosa_to_geojson(answers.get("xlocation"))
    raw_id = answers.get("uuid") or feature.get("id") or answers.get("fid")
    return normalise_feature(
        answers,
        geometry,
        feature_id=str(raw_id) if raw_id is not None else None,
        username=answers.get("osm_username") or answers.get("username"),
        submitted_at=answers.get("end") or answers.get("start"),
        attachments=_find_media(answers, media, []),
    )


def to_feature_collection(features: list[dict]) -> dict:
    """Wrap normalised features."""
    return {"type": "FeatureCollection", "features": features}
