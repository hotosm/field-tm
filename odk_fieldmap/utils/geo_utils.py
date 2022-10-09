#!/usr/bin/python3
"""
Various utilities for using GDAL in python
"""
import sys, os
import subprocess

from osgeo import ogr

def get_ogr_driver(extension):
    """Load a driver from GDAL for the input file. 
       Only GeoJSON guaranteed to work.
    """
    driver = None
    if extension.lower() == '.shp':
        driver = ogr.GetDriverByName('ESRI Shapefile')
    elif extension.lower() == '.geojson':
        driver = ogr.GetDriverByName('GeoJSON')
    elif extension.lower() == '.kml':
        driver = ogr.GetDriverByName('KML')
    elif extension.lower() == '.gpkg':
        driver = ogr.GetDriverByName('GPKG')
    else:
        print(f'Check input file format for {extension}')
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
        print('Something went wrong with the ogr driver')
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
        return f'{ymin},{xmin},{ymax},{xmax}'
    except Exception as e:
        print('Something went wrong with the ogr driver')
        print(e)
        exit(1)

def make_centroids(infile):
    """
    Expects a GeoJSON file of polygons
    Creates a GeoJSON file of centroids.
    Retains all fields from the original polygon file.
    """
    p = subprocess.run(["ogr2ogr", '-f', 'PostgreSQL',
                        f'dbname=fmtm user=fmtm', infile],
                       capture_output=True, encoding='utf-8')
    r = p.stdout
    print(r)

    
#    (infilepath, ext) = os.path.splitext(infile)
#    outfn = (infilepath + '_centroids' + ext)
#    inDriver = get_ogr_driver(ext)
#    inDatasource = inDriver.Open(infile, 0)
#    inLayer = inDatasource.GetLayer()
#
#    outDriver = get_ogr_driver('.geojson')
#    outDataSource = outDriver.CreateDataSource(outfn)
#    outLayer = outDataSource.CreateLayer("centroids",
#                                         geom_type=ogr.wkbPoint)
#    # Add input Layer Fields to the output Layer
#    inLayerDefn = inLayer.GetLayerDefn()
#    for i in range(0, inLayerDefn.GetFieldCount()):
#        fieldDefn = inLayerDefn.GetFieldDefn(i)
#        outLayer.CreateField(fieldDefn)
#        
#    outLayerDefn = outLayer.GetLayerDefn()
#    
#    # Add features to the ouput Layer
#    for inFeature in inLayer:
#        outFeature = ogr.Feature(outLayerDefn)
#        geom = inFeature.GetGeometryRef()
#        centroid = geom.Centroid()
#        outFeature.SetGeometry(centroid)
#        outLayer.CreateFeature(outFeature)
#
def osm_json_to_geojson(infile):
    """Accept a raw JSON file of data from an Overpass API query.
    Return a GeoJSON string of the same data, after converting all polygons
    to points. USING THE NODE MODULE FROM OVERPASS, WHICH MUST BE INSTALLED
    USING sudo npm install -g osmtogeojson
    This is because the Python module osm2geojson
    returns geojson that is unusable in ODK.
    """
    try:
        print(f'Trying to turn {infile} into geojson')
        p = subprocess.run(["osmtogeojson", infile],
                           capture_output=True, encoding='utf-8')
        geojsonstring = p.stdout
        print(f'The osmtogeojson module accepted {infile} and '\
              f'returned something of type {type(geojsonstring)}')
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
        print('Something went wrong with the ogr driver')
        print(e)
        exit(1)
