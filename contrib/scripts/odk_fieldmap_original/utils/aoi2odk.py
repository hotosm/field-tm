# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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

#!/bin/python3

import json
import os
import sys

from geo_utils import get_extent_bbox, make_centroids, osm_json_to_geojson
from overpass import query


def get_buildings(aoi_file: str) -> dict:
    """Given a GeoJSON AOI polygon, returns a centroid for every
    OSM building polygon within it.

    Args:
        aoi_file (str): Filepath of the AOI GeoJSON polygon.

    Returns:
        dict: JSON response from Overpass API containing building data.
    """

    (infilepath, extension) = os.path.splitext(aoi_file)
    extent = get_extent_bbox(aoi_file, extension)
    querystring = (
        f"[out:json][timeout:200];"
        f'(wr["building"]({extent}););'
        f"out body;>;out body;"
    )
    overpass_url = "https://overpass.kumi.systems" "/api/interpreter"
    overpass_json = query(querystring, overpass_url)
    return overpass_json


def get_roads(aoi_file: str) -> dict:
    """Given a GeoJSON AOI polygon, returns roads.

    Args:
        aoi_file (str): Filepath of the AOI GeoJSON polygon.

    Returns:
        dict: JSON response from Overpass API containing road data.
    """
    
    (infilepath, extension) = os.path.splitext(aoi_file)
    extent = get_extent_bbox(aoi_file, extension)
    querystring = (
        f"[out:json][timeout:200];("
        f'wr["highway"]({extent});'
        f'wr["waterway"]({extent});'
        f'wr["railway"]({extent});'
        f");out body;>;out body;"
    )
    overpass_url = "https://overpass.kumi.systems" "/api/interpreter"
    overpass_json = query(querystring, overpass_url)
    return overpass_json


def aoi2project(AOIfile: str) -> None:
    """Takes a GeoJSON file with an aoi polygon, creates
    - A GeoJSON of all the OSM building polygons in it
    - A GeoJSON of the centroids thereof
    -.

    Args:
        AOIfile (str): Filepath of the AOI GeoJSON polygon.
    """
    (AOIpath, ext) = os.path.splitext(AOIfile)
    buildings = get_buildings(AOIfile)

    buildings_json = AOIpath + "_buildings.json"
    with open(buildings_json, "w") as bj:
        json.dump(buildings, bj)

    buildings_geojson = AOIpath + "_buildings.geojson"
    geojson = osm_json_to_geojson(buildings_json)
    with open(buildings_geojson, "w") as of:
        of.write(geojson)
    # Use the Node-based osmtogeojson module
    # Why? Horrifying details in geo_utils docstring
    make_centroids(buildings_geojson)

    roads = get_roads(AOIfile)

    roads_json = AOIpath + "_roads.json"
    with open(roads_json, "w") as rj:
        json.dump(roads, rj)

    roads_geojson = AOIpath + "_roads.geojson"
    geojson = osm_json_to_geojson(roads_json)
    with open(roads_geojson, "w") as of:
        of.write(geojson)
    # Use the Node-based osmtogeojson module
    # Why? Horrifying details in geo_utils docstring
    make_centroids(roads_geojson)


if __name__ == "__main__":
    """
    If run from CLI, attempts to convert a GeoJSON
    AOI into a project on an ODK Central server
    with multiple forms corresponding to sub-areas
    of the AOI.
    """
    AOIfile = sys.argv[1]
    aoi2project(AOIfile)
