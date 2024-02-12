# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""PostGIS and geometry handling helper funcs."""

import datetime
import logging
from json import dumps as json_dumps
from typing import Optional, Union

from fastapi import HTTPException
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from geojson import FeatureCollection
from geojson import loads as geojson_loads
from geojson_pydantic import Feature
from shapely.geometry import mapping
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


def timestamp():
    """Get the current time.

    Used to insert a current timestamp into Pydantic models.
    """
    return datetime.datetime.utcnow()


def geometry_to_geojson(
    geometry: WKBElement, properties: Optional[dict] = None, id: Optional[int] = None
) -> Union[Feature, dict]:
    """Convert SQLAlchemy geometry to GeoJSON."""
    if geometry:
        shape = to_shape(geometry)
        geojson = {
            "type": "Feature",
            "geometry": mapping(shape),
            "properties": properties,
            "id": id,
            # "bbox": shape.bounds,
        }
        return Feature(**geojson)
    return {}


def get_centroid(
    geometry: WKBElement, properties: Optional[dict] = None, id: Optional[int] = None
):
    """Convert SQLAlchemy geometry to Centroid GeoJSON."""
    if geometry:
        shape = to_shape(geometry)
        point = shape.centroid
        geojson = {
            "type": "Feature",
            "geometry": mapping(point),
            "properties": properties,
            "id": id,
        }
        return Feature(**geojson)
    return {}


async def geojson_to_flatgeobuf(
    db: Session, geojson: FeatureCollection
) -> Optional[bytes]:
    """From a given FeatureCollection, return a memory flatgeobuf obj.

    Args:
        db (Session): SQLAlchemy db session.
        geojson (FeatureCollection): a geojson.FeatureCollection object.

    Returns:
        flatgeobuf (bytes): a Python bytes representation of a flatgeobuf file.
    """
    # FIXME make this with with properties / tags
    # FIXME this is important
    # sql = """
    #     DROP TABLE IF EXISTS public.temp_features CASCADE;

    #     CREATE TABLE IF NOT EXISTS public.temp_features(
    #         geom geometry,
    #         osm_id integer,
    #         changeset integer,
    #         timestamp timestamp
    #     );

    # WITH data AS (SELECT CAST(:geojson AS json) AS fc)
    # INSERT INTO public.temp_features (geom, osm_id, changeset, timestamp)
    # SELECT
    #     ST_SetSRID(ST_GeomFromGeoJSON(feat->>'geometry'), 4326) AS geom,
    #     COALESCE((feat->'properties'->>'osm_id')::integer, -1) AS osm_id,
    #     COALESCE((feat->'properties'->>'changeset')::integer, -1) AS changeset,
    #     CASE
    #         WHEN feat->'properties'->>'timestamp' IS NOT NULL
    #         THEN (feat->'properties'->>'timestamp')::timestamp
    #         ELSE NULL
    #     END AS timestamp
    # FROM (
    #     SELECT json_array_elements(fc->'features') AS feat
    #     FROM data
    # ) AS f;

    #     -- Second param = generate with spatial index
    #     SELECT ST_AsFlatGeobuf(geoms, true)
    #     FROM (SELECT * FROM public.temp_features) AS geoms;
    # """
    sql = """
        DROP TABLE IF EXISTS public.temp_features CASCADE;

        CREATE TABLE IF NOT EXISTS public.temp_features(
            geom geometry
        );

        WITH data AS (SELECT CAST(:geojson AS json) AS fc)
        INSERT INTO public.temp_features (geom)
        SELECT
            ST_SetSRID(ST_GeomFromGeoJSON(feat->>'geometry'), 4326) AS geom
        FROM (
            SELECT json_array_elements(fc->'features') AS feat
            FROM data
        ) AS f;

        SELECT ST_AsFlatGeobuf(fgb_data)
        FROM (SELECT * FROM public.temp_features as geoms) AS fgb_data;
    """
    # Run the SQL
    result = db.execute(text(sql), {"geojson": json_dumps(geojson)})
    # Get a memoryview object, then extract to Bytes
    flatgeobuf = result.first()

    # Cleanup table
    # db.execute(text("DROP TABLE IF EXISTS public.temp_features CASCADE;"))

    if flatgeobuf:
        return flatgeobuf[0].tobytes()

    # Nothing returned (either no features passed, or failed)
    return None


async def flatgeobuf_to_geojson(
    db: Session, flatgeobuf: bytes
) -> Optional[FeatureCollection]:
    """Converts FlatGeobuf data to GeoJSON.

    Args:
        db (Session): SQLAlchemy db session.
        flatgeobuf (bytes): FlatGeobuf data in bytes format.

    Returns:
        FeatureCollection: A GeoJSON FeatureCollection object.
    """
    sql = text(
        """
        DROP TABLE IF EXISTS public.temp_fgb CASCADE;

        SELECT ST_FromFlatGeobufToTable('public', 'temp_fgb', :fgb_bytes);

        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(feature)
        ) AS feature_collection
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(fgb_data.geom)::jsonb,
                'properties', fgb_data.properties::jsonb
            ) AS feature
            FROM (
            SELECT *,
                NULL as properties
                FROM ST_FromFlatGeobuf(null::temp_fgb, :fgb_bytes)
            ) AS fgb_data
        ) AS features;
    """
    )

    try:
        result = db.execute(sql, {"fgb_bytes": flatgeobuf})
        feature_collection = result.first()
    except ProgrammingError as e:
        log.error(e)
        log.error(
            "Attempted flatgeobuf --> geojson conversion, but duplicate column found"
        )
        return None

    if feature_collection:
        return geojson_loads(json_dumps(feature_collection[0]))

    return None


async def parse_and_filter_geojson(geojson_str: str) -> Optional[FeatureCollection]:
    """Parse geojson string and filter out incomaptible geometries."""
    log.debug("Parsing geojson file")
    geojson_parsed = geojson_loads(geojson_str)
    if isinstance(geojson_parsed, FeatureCollection):
        log.debug("Already in FeatureCollection format, skipping reparse")
        featcol = geojson_parsed
    elif isinstance(geojson_parsed, Feature):
        log.debug("Converting Feature to FeatureCollection")
        featcol = FeatureCollection(geojson_parsed)
    else:
        log.debug("Converting geometry to FeatureCollection")
        featcol = FeatureCollection[Feature(geometry=geojson_parsed)]

    # Validating Coordinate Reference System
    check_crs(featcol)

    geom_type = await get_featcol_main_geom_type(featcol)

    # Filter out geoms not matching main type
    features_filtered = [
        feature
        for feature in featcol.get("features", [])
        if feature.get("geometry", {}).get("type", "") == geom_type
    ]

    return FeatureCollection(features_filtered)


async def get_featcol_main_geom_type(featcol: FeatureCollection) -> str:
    """Get the predominant geometry type in a FeatureCollection."""
    geometry_counts = {"Polygon": 0, "Point": 0, "Polyline": 0}

    for feature in featcol.get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        if geometry_type in geometry_counts:
            geometry_counts[geometry_type] += 1

    return max(geometry_counts, key=geometry_counts.get)


async def check_crs(input_geojson: Union[dict, FeatureCollection]):
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
            raise HTTPException(status_code=400, detail=error_message)
        return

    if input_geojson_type := input_geojson.get("type") == "FeatureCollection":
        features = input_geojson.get("features", [])
        coordinates = (
            features[-1].get("geometry", {}).get("coordinates", []) if features else []
        )
    elif input_geojson_type := input_geojson.get("type") == "Feature":
        coordinates = input_geojson.get("geometry", {}).get("coordinates", [])

    geometry_type = (
        features[0].get("geometry", {}).get("type")
        if input_geojson_type == "FeatureCollection" and features
        else input_geojson.get("geometry", {}).get("type", "")
    )
    if geometry_type == "MultiPolygon":
        first_coordinate = coordinates[0][0] if coordinates and coordinates[0] else None
    elif geometry_type == "Point":
        first_coordinate = coordinates if coordinates else None

    elif geometry_type == "LineString":
        first_coordinate = coordinates[0] if coordinates else None

    else:
        first_coordinate = coordinates[0][0] if coordinates else None

    if not is_valid_coordinate(first_coordinate):
        log.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
