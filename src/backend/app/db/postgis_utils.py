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
from geojson_pydantic import Feature
from shapely.geometry import mapping


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
