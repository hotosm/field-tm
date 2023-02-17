#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os
import logging
import sys
import epdb
import geojson
from sys import argv
import mercantile
from osgeo import ogr, osr
from pySmartDL import SmartDL
from cpuinfo import get_cpu_info
from codetiming import Timer
import queue
import concurrent.futures
import threading
import glob
from pymbtiles import MBtiles, Tile
import sqlite3
from sqlite import MapTile, DataFile


def dlthread(dest, mirrors, tiles):
    """Thread to handle downloads for Queue"""
    if len(tiles) == 0:
        #epdb.st()
        return
    # counter = -1
    errors = 0

    # start = datetime.now()

    # totaltime = 0.0
    logging.info("Downloading %d tiles in thread %d to %s" % (len(tiles), threading.get_ident(), dest))
    for tile in tiles:
        filespec = f"{tile[2]}/{tile[1]}/{tile[0]}"
        for site in mirrors:
            if site['source'] != 'topo':
                filespec += "." + site['suffix']
            url = site['url']
            remote = url % filespec
            print("Getting file from: %s" % remote)
            # Create the subdirectories as pySmartDL doesn't do it for us
            if os.path.isdir(dest) is False:
                tmp = ""
                paths = dest.split('/')
                for i in paths[1:]:
                    tmp += '/' + i
                    if os.path.isdir(tmp):
                        continue
                    else:
                        os.mkdir(tmp)
                        logging.debug("Made %s" % tmp)

        try:
            if site['source'] == 'topo':
                filespec += "." + site['suffix']
            outfile = dest + "/" + filespec
            if not os.path.exists(outfile):
                dl = SmartDL(remote, dest=outfile, connect_default_logger=False)
                dl.start()
            else:
                logging.debug("%s exists!" % (outfile))
        except:
            logging.error("Couldn't download from %r: %s" %  (filespec, dl.get_errors()))

class BaseMapper(object):
    def __init__(self, filespec=None, base=None, source=None):
        """Create an mbtiles basemap for ODK Collect"""
        geom = ogr.Open(filespec)
        layer = geom.GetLayer()
        x_min, x_max, y_min, y_max = layer.GetExtent()
        srs = layer.GetSpatialRef()

        self.bbox = self.makeBbox(layer)
        self.tiles = list()
        self.base = base
        # sources for imagery
        self.source = source
        self.sources = dict()

        # Bing hybrid imagery
        url = "http://ecn.t0.tiles.virtualearth.net/tiles/h%s.png?g=129&mkt=en&stl=H"
        source = {'name': "Bing Maps Hybrid", 'url': url, 'suffix': 'png', 'source': 'bing'}
        self.sources['bing'] = source

        # ERSI imagery
        url = "http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/%s"
        source = {'name': "ESRI World Imagery", 'url': url, 'suffix': 'jpg', 'source': 'ersi'}
        self.sources['ersi'] = source

        # USGS Topographical map
        url = "https://basemap.nationalmap.gov/ArcGIS/rest/services/USGSTopo/MapServer/tile/%s"
        source = {'name': "USGS Topographic Map", 'url': url, 'suffix': 'jpg', 'source': 'topo'}
        self.sources['topo'] = source

        # Google Hybrid
        url = "https://mt0.google.com/vt?lyrs=h&x={x}&s=&y={y}&z={z}"
        source = {'name': "Google Hybrid", 'url': url, 'suffix': 'png', 'source': 'google'}
        self.sources['google'] = source

        # OpenArialMap
        url = "https://tiles.openaerialmap.org/63962d0d9f665400075759be/0/63962d0d9f665400075759bf/{z}/{x}/{y}"
        source = {'name': "Open Aerial Map", 'url': url, 'suffix': 'png', 'source': 'oam'}
        self.sources['oam'] = source

    def getFormat(self):
        return  self.sources[self.source]['suffix']

    def getTiles(self, zoom=None):
        """Get a list of tiles for the specifed zoom level"""
        info = get_cpu_info()
        cores = info['count']

        self.tiles = list(mercantile.tiles(self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3], zoom))
        total = len(self.tiles)        
        logging.info("%d tiles for zoom level %d" % (len(self.tiles), zoom))
        chunk =  round(len(self.tiles)/cores)
        threads = queue.Queue(maxsize=cores)
        logging.info("%d threads, %d tiles" % (cores, total))

        mirrors = [self.sources[self.source]]
        # epdb.st()
        if len(self.tiles) < chunk or chunk == 0:
            dlthread(self.base, mirrors, self.tiles)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
                block = 0
                while block <= len(self.tiles):
                    future = executor.submit(dlthread, self.base, mirrors, self.tiles[block:block+chunk])
                    logging.debug("Dispatching Block %d:%d" % (block, block + chunk))
                    block += chunk
                executor.shutdown()
            # logging.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), os.path.basename(self.base)))

        return len(self.tiles)

    def tileExists(self, tile=list()):
        """See if a map tile already exists"""
        filespec = f"{self.base}{tile[2]}/{tile[1]}/{tile[0]}.{self.sources[{self.source}]['suffix']}"
        if os.path.exists(filespec):
            logging.debug("%s exists" % filespec)
            return True
        else:
            logging.debug("%s doesn't exists" % filespec)
            return False

    def makeBbox(self, layer=None):
        """Make a bounding box from a layer"""
        # left, bottom, right, top
        # minX: %d, minY: %d, maxX: %d, maxY: %d" %(env[0],env[2],env[1],env[3])
        for feature in layer:
            bbox = list(feature.GetGeometryRef().GetEnvelope())
            bbox = (bbox[0],bbox[2],bbox[1],bbox[3])
            print(bbox)
        return bbox

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an mbtiles basemap for ODK Collect')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-b", "--boundary", help='The boundary for the area you want')
    parser.add_argument("-z", "--zooms", default="12-17", help='The Zoom levels')
    parser.add_argument("-o", "--outfile", help='Output file name')
    parser.add_argument("-d", "--outdir", help='Output directory name for tile cache')
    parser.add_argument("-s", "--source", default="ersi", choices=["ersi", "bing", "topo", "google", 'oam'], help='Imagery source')
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)


# Get all the zoom levels we want
zooms = list()
if args.zooms:
    if args.zooms.find("-") > 0:
        start = int(args.zooms.split('-')[0])
        end = int(args.zooms.split('-')[1])
        x = range(start, end)
        for i in x:
            zooms.append(i)
    elif args.zooms.find(",") > 0:
        levels = args.zooms.split(',')
        for level in levels:
            zooms.append(int(level))
    else:
        zooms.append(int(args.zooms))

# Make a bounding box from the boundary file
if not args.boundary:
    logging.error("You need to specify a boundary file!")
    parser.print_help()
    quit()

if not args.outdir:
    base = "/var/www/html"
else:
    base = args.outdir
base = f"{base}/{args.source}tiles"

if args.source:
    basemap = BaseMapper(args.boundary, base, args.source)
else:
    logging.error("You need to specify a source!")
    quit()

outf = DataFile(args.outfile, basemap.getFormat())
suffix = os.path.splitext(args.outfile)[1]
if suffix == '.mbtiles':
    outf.addBounds(basemap.bbox)
for level in zooms:
    basemap.getTiles(level)
    if args.outfile:
        # Create output database and specify image format, png, jpg, or tif
        outf.writeTiles(basemap.tiles, base)
    else:
        logging.info("Only downloading tiles to %s!" % base)
