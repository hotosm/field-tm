#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

#
# This script converts a collection of XYZ map tiles of sat imagery
# and creates an mbtiles file for use with ODK based data collection.
# A boundary file is supplied to select only the tiles withint that
# area, since the tile store may be huge. This assumes all the tiles
# have already been download to disk.
#
from yamlfile import YamlFile
import logging
import epdb
import argparse
import sys
from pymbtiles import MBtiles, Tile
import geodex


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create mbtiles for ODK from XYZ tiles')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help='The boundary to select tiles in')
    parser.add_argument("-o", "--outfile", required=True, help='The output file for ODK')
    parser.add_argument("-x", "--xyz", required=True, help='The path to the top level XYZ tiles')
    parser.add_argument("-z", "--zoom", nargs='+', help='The zoom levels')
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

# TODO

# Open the GeoJson boundary file, make sure it's a valid geometry

# See if the zoom levels specified with --zoom exist in the XYZ tile store

# Get the list of tiles at each zoom level

# Open the each tile and write it to the mbtiles file.

