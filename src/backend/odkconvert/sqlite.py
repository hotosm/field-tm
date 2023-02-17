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
from sys import argv
import sqlite3
import locale
import mercantile



class MapTile(object):
    def __init__(self, x=None, y=None, z=None, filespec=None, tile=None, suffix="jpg"):
        """This is a simple wrapper around mercantile.tile to associate a
        filespec with the grid coordinates."""
        if tile:
            self.x = tile.x
            self.y = tile.y
            self.z = tile.z
        else:
            self.x = x
            self.y = y
            self.z = z
        self.blob = None
        self.filespec = None
        if not filespec and self.z:
            self.filespec = f"{self.z}/{self.y}/{self.x}.{suffix}"
        elif filespec:
            self.filespec = filespec
            tmp = filespec.split("/")
            self.z = tmp[0]
            self.x = tmp[2]
            self.y = tmp[1].replace("." + suffix, "")

    def readImage(self, base="./"):
        file = f"{base}/{self.filespec}"
        logging.debug("Adding tile image: %s" % file)
        if os.path.exists(file):
            size = os.path.getsize(file)
            file = open(file, "rb")
            self.blob = file.read(size)

    def dump(self):
        if self.z:
            print("Z: %r" % self.z)
        if self.x:
            print("X: %r" % self.x)
        if self.y:
            print("Y: %r" % self.y)
        print("Filespec: %s" % self.filespec)
        if self.blob:
            print("Tile size is: %d" % len(self.blob))

class DataFile(object):
    def __init__(self, dbname=None, suffix="jpg"):
        """Handle the sqlite3 database file"""
        self.db = None
        self.cursor = None
        if dbname:
            self.createDB(dbname)
        self.dbname = dbname
        self.metadata = None
        self.toplevel = None
        self.suffix = suffix

    def addBounds(self, bounds=None):
        """Mbtiles has a bounds field, Osmand doesn't"""
        entry = str(bounds)
        entry = entry[1:len(entry)-1].replace(" ", "")
        self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('bounds', '{entry}')")
        # self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('minzoom', '9')")
        # self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('maxzoom', '15')")

    def createDB(self, dbname=None):
        """Create and sqlitedb in either mbtiles or Osman sqlitedb format"""
        suffix = os.path.splitext(dbname)[1]

        if os.path.exists(dbname):
            os.remove(dbname)

        self.db = sqlite3.connect(dbname)
        self.cursor = self.db.cursor()
        if suffix == '.mbtiles':
            self.cursor.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
            self.cursor.execute("CREATE INDEX tiles_idx on tiles (zoom_level, tile_column, tile_row)")
            self.cursor.execute("CREATE TABLE metadata (name text, value text)")
            # These get populated later
            name = dbname
            description = "Created by odkconvert/basemapper.py"
            bounds = None
            self.cursor.execute("CREATE UNIQUE INDEX metadata_idx  ON metadata (name)")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('version', '1.1')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('type', 'baselayer')")
            self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('name', '{name}')")
            self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('description', '{description}')")
            #self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('bounds', '{bounds}')")
            self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('format', 'jpg')")
        elif suffix == '.sqlitedb':
            # s is always 0
            self.cursor.execute("CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));")
            self.cursor.execute("CREATE INDEX IND on tiles (x,y,z,s)")
            # Info is simple "2|4" for example, it gets populated later
            self.cursor.execute("CREATE TABLE info (maxzoom Int, minzoom Int);")
            # the metadata is the locale as a string
            loc = locale.getlocale()[0]
            self.cursor.execute(f"CREATE TABLE  android_metadata ({loc})")
        self.db.commit()
        logging.info("Created database file %s" % dbname)

    def writeTiles(self, tiles=list(), base="./"):
        for tile in tiles:
            xyz = MapTile(tile=tile)
            xyz.readImage(base)
            #xyz.dump()
            self.writeTile(xyz)

    def writeTile(self, tile=None):
        if tile.blob is None:
            logging.error("Map tile has no image data!")
            #tile.dump()
            return False
        suffix = os.path.splitext(self.dbname)[1]
        if suffix == ".sqlitedb":
            # Osmand tops out at zoom level 16, so the real zoom level is inverse,
            # and can go negative for really high zoom levels.
            z = 17 - tile.z
            self.db.execute("INSERT INTO tiles (x, y, z, s, image) VALUES (?, ?, ?, ?, ?)", [tile.x, tile.y, z, 0, sqlite3.Binary(tile.blob)])
        elif suffix ==".mbtiles":
            y = (1 << tile.z) - tile.y - 1
            self.db.execute("INSERT INTO tiles (tile_row, tile_column, zoom_level, tile_data) VALUES (?, ?, ?, ?)", [y, tile.x, tile.z, sqlite3.Binary(tile.blob)])

        self.db.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an mbtiles basemap for ODK Collect')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-d", "--database", default="test.mbtiles", help='Database file name')
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

        outfile = DataFile(args.database, "jpg")
        toplevel = "/var/www/html/topotiles/"
        foo = "15/12744/6874.png"
        tmp = foo.split("/")
        z = tmp[0]
        x = tmp[1]
        y = tmp[2].replace(".jpg", "")

        # file = "10/388/212.jpg"
        # tile1 = MapTile(x=x, y=y, z=z)
        # tile2 = MapTile(filespec=file)
        # tile2.readImage(f'{toplevel}/{foo}')
        # outfile.writeTile(tile2)

        tile3 = mercantile.Tile(388, 211, 10)
        xyz = MapTile(tile=tile3)
        xyz.readImage(toplevel)
        xyz.dump()
        
