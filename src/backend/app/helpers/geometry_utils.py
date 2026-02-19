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
from typing import Optional, Union

import geojson
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import unary_union

log = logging.getLogger(__name__)


async def polygon_to_centroid(
    polygon: geojson.Polygon,
) -> Point:
    """Convert GeoJSON to shapely geometry."""
    return shape(polygon).centroid


def normalise_featcol(featcol: geojson.FeatureCollection) -> geojson.FeatureCollection:
    """Normalise a FeatureCollection into a standardised format.

    The final FeatureCollection will only contain:
    - Polygon
    - LineString
    - Point

    Processed:
    - MultiPolygons will be divided out into individual polygons.
    - GeometryCollections wrappers will be stripped out.
    - Removes any z-dimension coordinates, e.g. [43, 32, 0.0]

    Args:
        featcol: A parsed FeatureCollection.

    Returns:
        geojson.FeatureCollection: A normalised FeatureCollection.
    """

    def strip_z_coord(coords):
        if isinstance(coords[0], (int, float)):  # single coordinate [x, y, z?]
            return coords[:2]  # drop z if present
        return [strip_z_coord(c) for c in coords]

    for feat in featcol.get("features", []):
        geom = feat.get("geometry")

        # Strip out GeometryCollection wrappers
        if (
            geom.get("type") == "GeometryCollection"
            and len(geom.get("geometries", [])) == 1
        ):
            feat["geometry"] = geom.get("geometries")[0]

        # Remove any z-dimension coordinates recursively, for any geom type
        coords = geom.get("coordinates")
        if coords is not None:
            geom["coordinates"] = strip_z_coord(coords)

    # Convert MultiPolygon type --> individual Polygons
    return multigeom_to_singlegeom(featcol)


def geojson_to_featcol(geojson_obj: dict) -> geojson.FeatureCollection:
    """Enforce GeoJSON is wrapped in FeatureCollection.

    The type check is done directly from the GeoJSON to allow parsing
    from different upstream libraries (e.g. geojson_pydantic).
    """
    # We do a dumps/loads cycle to strip any extra obj logic
    geojson_type = json.loads(json.dumps(geojson_obj)).get("type")

    if geojson_type == "FeatureCollection":
        log.debug("Already in FeatureCollection format, reparsing")
        features = geojson_obj.get("features")
    elif geojson_type == "Feature":
        log.debug("Converting Feature to FeatureCollection")
        features = [geojson_obj]
    else:
        log.debug("Converting Geometry to FeatureCollection")
        features = [geojson.Feature(geometry=geojson_obj)]

    featcol = geojson.FeatureCollection(features=features)

    return normalise_featcol(featcol)


def parse_geojson_file_to_featcol(
    geojson_raw: Union[str, bytes],
) -> Optional[geojson.FeatureCollection]:
    """Parse geojson string or file content to FeatureCollection."""
    geojson_parsed = geojson.loads(geojson_raw)
    featcol = geojson_to_featcol(geojson_parsed)
    # Exit early if no geoms
    if not featcol.get("features", []):
        return None
    return featcol


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


async def check_crs(input_geojson: Union[dict, geojson.FeatureCollection]):
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
        return -180 <= coord[0] <= 180 and -90 <= coord[1] <= 90

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
        if len(parts) < 2:
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
        coordinates[0] == coordinates[-1] and len(coordinates) >= 4
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

    def split_multigeom(geom, properties):
        """Split multi-geometries into individual geometries."""
        return [
            geojson.Feature(geometry=mapping(single_geom), properties=properties)
            for single_geom in geom.geoms
        ]

    final_features = []

    for feature in featcol.get("features", []):
        properties = feature.get("properties", {})
        try:
            geom = shape(feature["geometry"])
        except ValueError:
            log.warning(f"Geometry is not valid, so was skipped: {feature['geometry']}")
            continue

        if geom.geom_type.startswith("Multi"):
            final_features.extend(split_multigeom(geom, properties))
        else:
            final_features.append(
                geojson.Feature(
                    geometry=mapping(geom),
                    properties=properties,
                )
            )

    return geojson.FeatureCollection(final_features)
