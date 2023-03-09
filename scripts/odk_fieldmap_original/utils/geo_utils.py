# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

#!/usr/bin/python3
"""
Various utilities for using GDAL in python
"""
import os
import subprocess
import sys

from osgeo import ogr


def get_ogr_driver(extension):
    """Load a driver from GDAL for the input file.
       Only GeoJSON guaranteed to work.
    """
    driver = None
    if extension.lower() == ".shp":
        driver = ogr.GetDriverByName("ESRI Shapefile")
    elif extension.lower() == ".geojson":
        driver = ogr.GetDriverByName("GeoJSON")
    elif extension.lower() == ".kml":
        driver = ogr.GetDriverByName("KML")
    elif extension.lower() == ".gpkg":
        driver = ogr.GetDriverByName("GPKG")
    else:
        print(f"Check input file format for {extension}")
        sys.exit()
    return driver


def get_extent(infile, extension):
    try:
        driver = get_ogr_driver(extension)
        datasource = driver.Open(infile, 0)
        layer = datasource.GetLayer()
        extent = layer.GetExtent()
        (xmin, xmax, ymin, ymax) = (extent[0], extent[1], extent[2], extent[3])
        return (xmin, xmax, ymin, ymax)
    except Exception as e:
        print("Something went wrong with the ogr driver")
        print(e)
        exit(1)


def get_extent_bbox(infile, extension):
    """
    Returns a string in the format of a bbox that
    works with an Overpass query.
    """
    try:
        driver = get_ogr_driver(extension)
        datasource = driver.Open(infile, 0)
        layer = datasource.GetLayer()
        extent = layer.GetExtent()
        (xmin, xmax, ymin, ymax) = (extent[0], extent[1], extent[2], extent[3])
        return f"{ymin},{xmin},{ymax},{xmax}"
    except Exception as e:
        print("Something went wrong with the ogr driver")
        print(e)
        exit(1)


def make_centroids(infile):
    """
    Expects a GeoJSON file of polygons
    Creates a GeoJSON file of centroids.
    Retains all fields from the original polygon file.
    """
    # TODO Implement me
    pass

def osm_json_to_geojson(infile):
    """Accept a raw JSON file of data from an Overpass API query.
    Return a GeoJSON string of the same data, after converting all polygons
    to points. USING THE NODE MODULE FROM OVERPASS, WHICH MUST BE INSTALLED
    USING sudo npm install -g osmtogeojson
    This is because the Python module osm2geojson
    returns geojson that is unusable in ODK.
    """
    try:
        print(f"Trying to turn {infile} into geojson")
        p = subprocess.run(
            ["osmtogeojson", infile], capture_output=True, encoding="utf-8"
        )
        geojsonstring = p.stdout
        print(
            f"The osmtogeojson module accepted {infile} and "
            f"returned something of type {type(geojsonstring)}"
        )
        return geojsonstring
    except Exception as e:
        print(e)


def get_geomcollection(infile, extension):
    try:
        driver = get_ogr_driver(extension)
        datasource = driver.Open(infile, 0)
        layer = datasource.GetLayer()
        extent = layer.GetExtent()
        (xmin, xmax, ymin, ymax) = (extent[0], extent[1], extent[2], extent[3])
        featurecount = layer.GetFeatureCount()
        geomcollection = ogr.Geometry(ogr.wkbGeometryCollection)

        # using a horrible range iterator to work around an apparent bug in OGR
        # (layer won't iterate in some versions of OGR)
        for i in range(featurecount):
            feature = layer.GetNextFeature()
            geomcollection.AddGeometry(feature.GetGeometryRef())
        return geomcollection
    except Exception as e:
        print("Something went wrong with the ogr driver")
        print(e)
        exit(1)
