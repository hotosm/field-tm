#!/usr/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import argparse
import logging
from sys import argv
import os
import epdb
import sys
from osgeo import ogr
from progress.bar import Bar, PixelBar
from progress.spinner import PixelSpinner
from codetiming import Timer
from osmfile import OsmFile
import shapely.wkb as wkblib
from shapely.geometry import Point, Polygon


class InputFile(object):
    def __init__(self, source=None):
        """Initialize Input Layer"""
        self.datain = None
        self.source = source
        if source[0:3] == "pg:":
            logging.info("Opening database connection to: %s" % source)
            connect = "PG: dbname=" + source[3:]
            # if options.get('dbhost') != "localhost":
            #connect += " host=" + options.get('dbhost')
            self.datain = ogr.Open(connect)
        else:
            logging.info("Opening data file: %s" % source)
            self.datain = ogr.Open(source)

        # Copy the data into memory for better performance
        memdrv = ogr.GetDriverByName("MEMORY")
        self.msmem = memdrv.CreateDataSource('msmem')
        self.msmem.CopyLayer(self.datain.GetLayer(), "msmem")
        self.layer = self.msmem.GetLayer()
        self.fields = self.datain.GetLayer().GetLayerDefn()
        self.memlayer = None
        self.mem = None
        self.tags = dict()
        for i in range(self.fields.GetFieldCount()):
            self.tags[self.fields.GetFieldDefn(i).GetName()] = None

    def clip(self, boundary=None):
        """Clip a data source by a boundary"""
        if boundary:
            logging.info("Clipping %s using %s" % (self.source, boundary))
            memdrv = ogr.GetDriverByName("MEMORY")
            self.mem = memdrv.CreateDataSource("data")
            self.memlayer = self.mem.CreateLayer("data", geom_type=ogr.wkbUnknown)

            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(self.layer, layer, self.memlayer)

    def mergeTags(self, osm=None, odk=None):
        """Merge two sets of tags together"""
        if str(osm) < str(odk):
            # logging.debug("No changes made to tags")
            return None
        else:
            # logging.debug("Changes tags")
            osm.update(odk)
            return osm
        return None

    def getFeature(self, data=None):
        id = data['attrs']['id']
        result = None
        if not id or int(id) < 0:
            if 'name' in data['tags']:
                query = f"SELECT *, ST_AsEWKT(geom) AS wkt FROM nodes WHERE tags->>'name'=\'{data['tags']['name']}\'"
                # print(query)
                result = self.datain.ExecuteSQL(query)
                if result.GetFeatureCount() == 0:
                    logging.debug(f"Feature not found in nodes for ID: {data['tags']['name']}")
                    result = None
                else:
                    logging.debug(f"Feature {data['tags']['name']} found in nodes")
            else:
                return None

        if not result:
            query = f"SELECT *, ST_AsEWKT(geom) AS wkt FROM ways_poly WHERE osm_id=\'{id}\'"
            # print(query)
            result = self.datain.ExecuteSQL(query)
            if result.GetFeatureCount() == 0:
                # print(data)
                if 'name' in data['tags']:
                    query = f"SELECT *, ST_AsEWKT(geom) AS wkt FROM nodes WHERE tags->>'name'=\'{data['tags']['name']}\'"
                    #print(query)
                    result = self.datain.ExecuteSQL(query)
                    if result.GetFeatureCount() == 0:
                        logging.debug(f"Feature not found in ways for ID: {data['tags']['name']}")
                    else:
                        logging.debug(f"Feature found in ways for ID: {data['tags']['name']}")
                return None

        # There is only one feature for an OSM ID
        feature = result.GetFeature(0)
        if feature.GetFieldCount() == 0:
            logging.debug(f"No fields found in feature for ID: {id}")
            return None

        index = feature.GetFieldIndex('tags')
        tags = eval(feature.GetField(index))

        index = feature.GetFieldIndex('version')
        version = feature.GetField(index)

        # Refs are stored as a string with a colon delimiter
        index = feature.GetFieldIndex('refs')
        if index < 0:
            refs = list()
        else:
            refs = eval(feature.GetField(index))

        # There should only be one feature returned from the query
        index = feature.GetFieldIndex('wkt')
        geom = feature.GetField(index)
        #geom = result[0].GetGeometryRef()

        # a ways don't use lat-lon, it uses references to nodes instead
        attrs = {'id': id, 'version': version}
        self.tags = dict()
        for k,v in tags.items():
            self.tags[k] = v
        feature = {'tags': self.tags, 'attrs': attrs, 'refs': refs, 'geom': geom}
        return feature

    def dump(self):
        """Dump internal data"""
        print(f"Data source is: {self.source}")
        if self.layer:
           print("There are %d in the layer" % self.layer.GetFeatureCount())
        if self.memlayer:
           print("There are %d in the layer" % self.memlayer.GetFeatureCount())
        
if __name__ == '__main__':
    # Command Line options
    parser = argparse.ArgumentParser(description='This program conflates ODK data with existing features from OSM.')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-c", "--odkfile", help="ODK CSV file downloaded from ODK Central")
    parser.add_argument("-f", "--osmfile", help="OSM XML file created by odkconvert")
    parser.add_argument("-o", "--outfile", default="tmp.osm", help="Output file from the merge")
    parser.add_argument("-b", "--boundary", help='Boundary polygon to limit the data size')
    args = parser.parse_args()

    # This program needs options to actually do anything
    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

    # This is the existing OSM data, a database or a file
    if args.osmfile:
        osmf = InputFile(args.osmfile)
        # osmf.dump()
        if args.boundary:
            osmf.clip(args.boundary)
        osmf.dump()
    else:
        logging.error("No OSM data source specified!")
        parser.print_help()
        quit()

    # Create an OSM XML handler, which writes to the output file
    odkf = OsmFile(filespec=args.outfile)
    # And also loads the POIs from the ODK Central submission
    odkf.loadFile(args.odkfile)

    for id in odkf.data:
        #print(odkf.data[id])
        feature = osmf.getFeature(odkf.data[id])
        out = list()
        if not feature:
            # logging.debug(f"No feature found for ID {id}")
            # feature = osmf.createFeature(odkf.data[id])
                out.append(odkf.createNode(odkf.data[id], modified=True))
        else:
            tags = osmf.mergeTags(feature['tags'], odkf.data[id]['tags'])
            if tags:
                odkf.data[id]['tags'] = tags
            if 'name' in feature['tags']:
                # if tags and odkf.data[id]['tags']['name'] != feature['tags']['name']:
                if tags:
                    out.append(odkf.createNode(odkf.data[id], modified=True))
            else:
                out.append(odkf.createWay(feature, modified=True))
        odkf.write(out)

    # # FIXME: for now just copy the data file from Central
    # # to test input parsing, and output accuracy.
    # out = list()
    # for id, node in odkf.data.items():
    #     out.append(odkf.createNode(node, modified=True))
    # odkf.write(out)
    odkf.footer()
    logging.info("Wrote %s: " % args.outfile)

# osmoutfile = os.path.basename(args.infile.replace(".csv", ".osm"))
#csvin.createOSM(osmoutfile)
