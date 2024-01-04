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

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geojson import FeatureCollection
from geojson_pydantic import Feature
from shapely.geometry import mapping
from sqlalchemy import text
from sqlalchemy.orm import Session


def timestamp():
    """Get the current time.

    Used to insert a current timestamp into Pydantic models.
    """
    return datetime.datetime.utcnow()


def geometry_to_geojson(geometry: Geometry, properties: str = {}, id: int = None):
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


def get_centroid(geometry: Geometry, properties: str = {}, id: int = None):
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


async def geojson_to_flatgeobuf(db: Session, geojson: FeatureCollection) -> bytes:
    """From a given FeatureCollection, return a memory flatgeobuf obj.

    Args:
        db (Session): SQLAlchemy db session.
        geojson (FeatureCollection): a geojson.FeatureCollection object.

    Returns:
        flatgeobuf (bytes): a Python bytes representation of a flatgeobuf file.
    """
    sql = f"""
        DROP TABLE IF EXISTS public.temp_features CASCADE;

        CREATE TABLE IF NOT EXISTS public.temp_features(
            id serial PRIMARY KEY,
            geom geometry
        );

        WITH data AS (SELECT '{geojson}'::json AS fc)
        INSERT INTO public.temp_features (geom)
        SELECT
            ST_AsText(ST_GeomFromGeoJSON(feat->>'geometry')) AS geom
        FROM (
            SELECT json_array_elements(fc->'features') AS feat
            FROM data
        ) AS f;

        WITH thegeom AS
        (SELECT * FROM public.temp_features)
        SELECT ST_AsFlatGeobuf(thegeom.*)
        FROM thegeom;
    """
    # Run the SQL
    result = db.execute(text(sql))
    # Get a memoryview object, then extract to Bytes
    flatgeobuf = result.fetchone()[0]

    # Cleanup table
    db.execute(text("DROP TABLE IF EXISTS public.temp_features CASCADE;"))

    if flatgeobuf:
        return flatgeobuf.tobytes()

    # Nothing returned (either no features passed, or failed)
    return None
