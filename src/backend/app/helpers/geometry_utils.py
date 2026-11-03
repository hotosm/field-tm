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
"""GeoJSON and geometry helper functions."""

import json
import logging
import types
from typing import Optional

from psycopg import AsyncConnection, Connection

from app.errors import (
    UnprocessableError,
    ValidationError,
)
from app.i18n import _

log = logging.getLogger(__name__)

MIN_LONGITUDE = -180
MAX_LONGITUDE = 180
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LAT_LON_PARTS = 2
MIN_POLYGON_POINTS = 4
MIN_CENTROID_POINTS = 3
POLYGON_AREA_EPSILON = 1e-10

# Project area limits (km²)
AREA_WARN_KM2 = 100
AREA_LIMIT_KM2 = 1000


_COORD_NESTING = {
    "Point": 0,
    "LineString": 1,
    "MultiPoint": 1,
    "Polygon": 2,
    "MultiLineString": 2,
    "MultiPolygon": 3,
}


def _flatten_geom_coords(geom: dict) -> list:
    """Flatten all coordinates in a GeoJSON geometry to a list of [lon, lat] pairs."""
    geom_type = geom.get("type", "")
    if geom_type == "GeometryCollection":
        return [
            c for sub in geom.get("geometries", []) for c in _flatten_geom_coords(sub)
        ]
    if geom_type not in _COORD_NESTING:
        return []
    coords = [geom.get("coordinates", [])]
    for _level in range(_COORD_NESTING[geom_type]):
        coords = [c for part in coords for c in part]
    return coords


def outline_bbox(outline: dict) -> tuple[float, float, float, float]:
    """Compute the bbox (xmin, ymin, xmax, ymax) of a project outline.

    The outline may be a raw GeoJSON geometry, a Feature, or a FeatureCollection.
    """
    geometry = extract_geometry(outline)
    if not geometry:
        raise UnprocessableError(_("Project outline is missing or has no geometry."))
    coords = _flatten_geom_coords(geometry)
    if not coords:
        raise UnprocessableError(_("Project outline geometry has no coordinates."))
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return min(lons), min(lats), max(lons), max(lats)


def extract_geometry(geojson_obj: dict) -> Optional[dict]:
    """Extract the geometry dict from a GeoJSON object of any type."""
    if not geojson_obj or not isinstance(geojson_obj, dict):
        return None
    obj_type = geojson_obj.get("type", "")
    if obj_type == "FeatureCollection":
        features = geojson_obj.get("features", [])
        if features and isinstance(features[0], dict):
            return features[0].get("geometry", features[0])
        return None
    if obj_type == "Feature":
        return geojson_obj.get("geometry")
    if "coordinates" in geojson_obj:
        return geojson_obj
    return None


async def geojson_area_km2(db: AsyncConnection, geojson_geom: dict) -> float:
    """Calculate the geodesic area of a GeoJSON geometry in km² using PostGIS.

    Uses ST_Area with the geography type for WGS84 spheroid accuracy.
    """
    geom_type = geojson_geom.get("type", "")
    if geom_type not in ("Polygon", "MultiPolygon"):
        return 0.0
    async with db.cursor() as cur:
        await cur.execute(
            """
               SELECT ST_Area(ST_SetSRID(
                   ST_GeomFromGeoJSON(%s), 4326
                )::geography) / 1000000
            """,
            (json.dumps(geojson_geom),),
        )
        row = await cur.fetchone()
    return float(row[0]) if row and row[0] is not None else 0.0


def merge_featcol_polygons_sync(db_url: str, featcol: dict) -> dict:
    """Union polygon features into one feature.

    Workaround for geojson_aoi_parser<=0.3.5 ignoring merge=True; remove
    once upstream implements merging in geojson_aoi/_sync/postgis.py.
    """
    features = featcol.get("features", [])
    if len(features) <= 1:
        return featcol
    geoms = [feat["geometry"] for feat in features if feat.get("geometry")]
    if len(geoms) <= 1:
        return featcol

    with Connection.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT ST_AsGeoJSON(ST_Union(ST_GeomFromGeoJSON(value::text)))::json "
            "FROM jsonb_array_elements(%s::jsonb)",
            (json.dumps(geoms),),
        )
        row = cur.fetchone()

    merged_geom = row[0] if row else None
    if not merged_geom:
        return featcol

    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": merged_geom, "properties": None}],
    }


async def polygon_to_centroid(
    polygon: dict,
) -> types.SimpleNamespace:
    """Compute the centroid of a GeoJSON Polygon using the shoelace formula."""
    coords = polygon.get("coordinates", [[]])[0]
    n = len(coords)
    if n < MIN_CENTROID_POINTS:
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        cx = sum(lons) / n if n else 0.0
        cy = sum(lats) / n if n else 0.0
        return types.SimpleNamespace(x=cx, y=cy)
    area = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n - 1):
        xi, yi = coords[i][0], coords[i][1]
        xi1, yi1 = coords[i + 1][0], coords[i + 1][1]
        cross = xi * yi1 - xi1 * yi
        area += cross
        cx += (xi + xi1) * cross
        cy += (yi + yi1) * cross
    area /= 2.0
    if abs(area) < POLYGON_AREA_EPSILON:
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return types.SimpleNamespace(x=sum(lons) / n, y=sum(lats) / n)
    cx /= 6.0 * area
    cy /= 6.0 * area
    return types.SimpleNamespace(x=cx, y=cy)


async def featcol_polygons_to_centroids(featcol: dict) -> dict:
    """Replace Polygon and MultiPolygon geometries with their centroid."""
    features = []
    for feature in featcol.get("features", []):
        geom = feature.get("geometry") or {}
        if geom.get("type") == "MultiPolygon" and geom.get("coordinates"):
            geom = {"type": "Polygon", "coordinates": geom["coordinates"][0]}
        if geom.get("type") == "Polygon":
            point = await polygon_to_centroid(geom)
            feature = {
                **feature,
                "geometry": {"type": "Point", "coordinates": [point.x, point.y]},
            }
        features.append(feature)
    return {**featcol, "features": features}


def featcol_keep_single_geom_type(
    featcol: dict,
    geom_type: Optional[str] = None,
) -> dict:
    """Strip out any geometries not matching the dominant geometry type."""
    features = featcol.get("features", [])

    if not geom_type:
        # Default to keep the predominant geometry type
        geom_type = get_featcol_dominant_geom_type(featcol)

    features_filtered = [
        feature
        for feature in features
        if (feature.get("geometry") or {}).get("type", "") == geom_type
    ]

    return {"type": "FeatureCollection", "features": features_filtered}


def get_featcol_dominant_geom_type(featcol: dict) -> str:
    """Get the predominant geometry type in a FeatureCollection."""
    geometry_counts = {"Polygon": 0, "Point": 0, "LineString": 0}

    for feature in featcol.get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        if geometry_type in geometry_counts:
            geometry_counts[geometry_type] += 1

    return max(geometry_counts, key=lambda key: geometry_counts[key])


def _valid_task_id(task_id) -> bool:
    """A valid task id is a positive integer (bools excluded)."""
    return isinstance(task_id, int) and not isinstance(task_id, bool) and task_id > 0


def stamp_missing_task_ids(featcol: dict) -> dict:
    """Ensure unique positive integer task_ids, normalizing digit strings in place.

    Preserve the first occurrence of each valid ID. Replace missing, invalid,
    or duplicate IDs with the smallest unused positive integers.
    """
    features = featcol.get("features", []) if isinstance(featcol, dict) else []

    # First pass: normalize digit-strings and reserve valid first-seen ids
    existing_ids = set()
    for feature in features:
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
            feature["properties"] = properties
        task_id = properties.get("task_id")
        if isinstance(task_id, str) and task_id.isdigit():
            task_id = int(task_id)
            properties["task_id"] = task_id
        if _valid_task_id(task_id):
            existing_ids.add(task_id)

    # Second pass: re-stamp anything missing, malformed, or duplicated
    next_id = 1
    seen_ids = set()
    for feature in features:
        properties = feature["properties"]
        task_id = properties.get("task_id")
        if _valid_task_id(task_id) and task_id not in seen_ids:
            seen_ids.add(task_id)
            continue
        while next_id in existing_ids:
            next_id += 1
        properties["task_id"] = next_id
        existing_ids.add(next_id)
        seen_ids.add(next_id)

    return featcol


async def check_crs(  # noqa: C901
    input_geojson: dict,
):
    """Validate CRS is valid for a geojson."""
    log.debug("validating coordinate reference system")

    def is_valid_crs(crs_name):
        valid_crs_list = [
            "urn:ogc:def:crs:OGC:1.3:CRS84",
            "urn:ogc:def:crs:EPSG::4326",
            "WGS 84",
        ]
        return crs_name in valid_crs_list

    def is_valid_coordinate(coord):
        if coord is None:
            return False
        return (
            MIN_LONGITUDE <= coord[0] <= MAX_LONGITUDE
            and MIN_LATITUDE <= coord[1] <= MAX_LATITUDE
        )

    error_message = (
        "ERROR: Unsupported coordinate system, it is recommended to use a "
        "GeoJSON file in WGS84(EPSG 4326) standard."
    )
    if "crs" in input_geojson:
        crs = input_geojson.get("crs", {}).get("properties", {}).get("name")
        if not is_valid_crs(crs):
            log.error(error_message)
            raise ValidationError(error_message)
        return

    if (input_geojson_type := input_geojson.get("type")) == "FeatureCollection":
        features = input_geojson.get("features", [])
        coordinates = (
            features[-1].get("geometry", {}).get("coordinates", []) if features else []
        )
    elif input_geojson_type == "Feature":
        coordinates = input_geojson.get("geometry", {}).get("coordinates", [])
    else:
        coordinates = input_geojson.get("coordinates", {})

    first_coordinate = None
    if coordinates:
        while isinstance(coordinates, list):
            first_coordinate = coordinates
            coordinates = coordinates[0]

    error_message = (
        "ERROR: The coordinates within the GeoJSON file are not valid. "
        "Is the file empty?"
    )
    if not is_valid_coordinate(first_coordinate):
        log.error(error_message)
        raise ValidationError(error_message)


async def geojson_to_javarosa_geom(geojson_geometry: dict) -> str:
    """Convert GeoJSON to JavaRosa: lat lon 0.0 0.0 points separated by semicolons."""
    if geojson_geometry is None:
        return ""

    coordinates = geojson_geometry.get("coordinates", [])
    geometry_type = geojson_geometry["type"]

    # Normalize to groups of coordinate pairs.
    if geometry_type == "Point":
        coordinates = [[coordinates]]
    elif geometry_type in ["LineString", "MultiPoint"]:
        coordinates = [coordinates]
    elif geometry_type in ["Polygon", "MultiLineString"]:
        pass
    elif geometry_type == "MultiPolygon":
        coordinates = [coord for poly in coordinates for coord in poly]
    else:
        raise ValueError(f"Unsupported GeoJSON geometry type: {geometry_type}")

    javarosa_geometry = []
    for polygon_or_line in coordinates:
        for lon, lat in polygon_or_line:
            javarosa_geometry.append(f"{lat} {lon} 0.0 0.0")

    return ";".join(javarosa_geometry)


async def javarosa_to_geojson_geom(javarosa_geom_string: str) -> dict:
    """Convert JavaRosa to GeoJSON, inferring point, line, or closed polygon."""
    if not javarosa_geom_string or not isinstance(javarosa_geom_string, str):
        return {}

    coordinates = []

    for point_str in javarosa_geom_string.strip().split(";"):
        parts = point_str.strip().split()

        if len(parts) < MIN_LAT_LON_PARTS:
            continue

        try:
            lat = float(parts[0])
            lon = float(parts[1])
            coordinates.append([lon, lat])
        except ValueError:
            continue

    if not coordinates:
        return {}

    if len(coordinates) == 1:
        geom_type = "Point"
        coordinates = coordinates[0]
    elif coordinates[0] == coordinates[-1] and len(coordinates) >= MIN_POLYGON_POINTS:
        geom_type = "Polygon"
        coordinates = [coordinates]
    else:
        geom_type = "LineString"

    return {"type": geom_type, "coordinates": coordinates}
