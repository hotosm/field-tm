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

import logging
import types
from typing import Optional, Union

import geojson
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from pyproj import Geod

log = logging.getLogger(__name__)

MIN_LONGITUDE = -180
MAX_LONGITUDE = 180
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LAT_LON_PARTS = 2
MIN_POLYGON_POINTS = 4

# Project area limits (km²)
AREA_WARN_KM2 = 100
AREA_LIMIT_KM2 = 1000


def geojson_area_km2(geojson_geom: dict) -> float:
    """Calculate the geodesic area of a GeoJSON geometry in km².

    Uses the WGS84 ellipsoid for accurate results regardless of location.
    """
    geod = Geod(ellps="WGS84")
    geom_type = geojson_geom.get("type", "")
    coords = geojson_geom.get("coordinates", [])
    total_area_m2 = 0.0
    if geom_type == "Polygon":
        outer_ring = coords[0] if coords else []
        lons = [c[0] for c in outer_ring]
        lats = [c[1] for c in outer_ring]
        area, _ = geod.polygon_area_perimeter(lons, lats)
        total_area_m2 = abs(area)
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            outer_ring = polygon[0] if polygon else []
            lons = [c[0] for c in outer_ring]
            lats = [c[1] for c in outer_ring]
            area, _ = geod.polygon_area_perimeter(lons, lats)
            total_area_m2 += abs(area)
    return total_area_m2 / 1_000_000


async def polygon_to_centroid(
    polygon: geojson.Polygon,
) -> types.SimpleNamespace:
    """Compute the centroid of a GeoJSON Polygon using the shoelace formula."""
    coords = polygon.get("coordinates", [[]])[0]
    n = len(coords)
    if n < 3:
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
    if abs(area) < 1e-10:
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return types.SimpleNamespace(x=sum(lons) / n, y=sum(lats) / n)
    cx /= 6.0 * area
    cy /= 6.0 * area
    return types.SimpleNamespace(x=cx, y=cy)


def featcol_keep_single_geom_type(
    featcol: geojson.FeatureCollection,
    geom_type: Optional[str] = None,
) -> geojson.FeatureCollection:
    """Strip out any geometries not matching the dominant geometry type."""
    features = featcol.get("features", [])

    if not geom_type:
        # Default to keep the predominant geometry type
        geom_type = get_featcol_dominant_geom_type(featcol)

    features_filtered = [
        feature
        for feature in features
        if feature.get("geometry", {}).get("type", "") == geom_type
    ]

    return geojson.FeatureCollection(features_filtered)


def get_featcol_dominant_geom_type(featcol: geojson.FeatureCollection) -> str:
    """Get the predominant geometry type in a FeatureCollection."""
    geometry_counts = {"Polygon": 0, "Point": 0, "LineString": 0}

    for feature in featcol.get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        if geometry_type in geometry_counts:
            geometry_counts[geometry_type] += 1

    return max(geometry_counts, key=lambda key: geometry_counts[key])


async def check_crs(  # noqa: C901
    input_geojson: Union[dict, geojson.FeatureCollection],
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
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
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )


async def geojson_to_javarosa_geom(geojson_geometry: dict) -> str:
    """Convert a GeoJSON geometry to JavaRosa format string.

    This format is unique to ODK and the JavaRosa XForm processing library.
    Example JavaRosa polygon (semicolon separated):
    -8.38071535576881 115.640801902838 0.0 0.0;
    -8.38074220774489 115.640848633963 0.0 0.0;
    -8.38080128208577 115.640815355738 0.0 0.0;
    -8.38077407987063 115.640767444534 0.0 0.0;
    -8.38071535576881 115.640801902838 0.0 0.0

    Args:
        geojson_geometry (dict): The GeoJSON geometry.

    Returns:
        str: A string representing the geometry in JavaRosa format.
    """
    if geojson_geometry is None:
        return ""

    coordinates = geojson_geometry.get("coordinates", [])
    geometry_type = geojson_geometry["type"]

    # Normalise single geometries into the same structure as multi-geometries
    # We end up with three levels of nesting for the processing below
    if geometry_type == "Point":
        # Format [x, y]
        coordinates = [[coordinates]]
    elif geometry_type in ["LineString", "MultiPoint"]:
        # Format [[x, y], [x, y]]
        coordinates = [coordinates]
    elif geometry_type in ["Polygon", "MultiLineString"]:
        # Format [[[x, y], [x, y]]]
        pass
    elif geometry_type == "MultiPolygon":
        # Format [[[[x, y], [x, y]]]], flatten coords
        coordinates = [coord for poly in coordinates for coord in poly]
    else:
        raise ValueError(f"Unsupported GeoJSON geometry type: {geometry_type}")

    # Prepare the JavaRosa format by iterating over coordinates
    javarosa_geometry = []
    for polygon_or_line in coordinates:
        for lon, lat in polygon_or_line:
            javarosa_geometry.append(f"{lat} {lon} 0.0 0.0")

    return ";".join(javarosa_geometry)


async def javarosa_to_geojson_geom(javarosa_geom_string: str) -> dict:
    """Convert a JavaRosa format string to GeoJSON geometry.

    The geometry type is automatically inferred from the geometry
    coordinate structure.

    Args:
        javarosa_geom_string (str): The JavaRosa geometry.

    Returns:
        dict: A geojson geometry.
    """
    if not javarosa_geom_string or not isinstance(javarosa_geom_string, str):
        return {}

    coordinates = []

    for point_str in javarosa_geom_string.strip().split(";"):
        parts = point_str.strip().split()

        # Expect at least lat and lon
        if len(parts) < MIN_LAT_LON_PARTS:
            continue

        try:
            lat = float(parts[0])
            lon = float(parts[1])
            coordinates.append([lon, lat])
        except ValueError:
            continue  # Skip if conversion fails

    if not coordinates:
        return {}

    # Determine geometry type
    if len(coordinates) == 1:
        geom_type = "Point"
        coordinates = coordinates[0]  # Flatten for Point
    elif (
        coordinates[0] == coordinates[-1] and len(coordinates) >= MIN_POLYGON_POINTS
    ):  # Check if closed loop
        geom_type = "Polygon"
        coordinates = [coordinates]  # Wrap in extra list for Polygon
    else:
        geom_type = "LineString"

    return {"type": geom_type, "coordinates": coordinates}


def multigeom_to_singlegeom(
    featcol: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Converts any Multi(xxx) geometry types to individual geometries."""

    def split_multigeom(geom: dict, properties: dict) -> list:
        """Split multi-geometries into individual geometries."""
        geom_type = geom["type"]
        if geom_type == "GeometryCollection":
            return [
                geojson.Feature(geometry=sub_geom, properties=properties)
                for sub_geom in geom.get("geometries", [])
            ]
        single_type = geom_type[5:]  # Strip "Multi" prefix
        return [
            geojson.Feature(
                geometry={"type": single_type, "coordinates": part},
                properties=properties,
            )
            for part in geom.get("coordinates", [])
        ]

    final_features = []

    for feature in featcol.get("features", []):
        properties = feature.get("properties", {})
        geom = feature.get("geometry")
        if geom is None:
            log.warning(f"Feature has no geometry, skipping: {feature}")
            continue
        geom_type = geom.get("type", "")
        if geom_type.startswith("Multi") or geom_type == "GeometryCollection":
            final_features.extend(split_multigeom(geom, properties))
        else:
            final_features.append(geojson.Feature(geometry=geom, properties=properties))

    return geojson.FeatureCollection(final_features)
