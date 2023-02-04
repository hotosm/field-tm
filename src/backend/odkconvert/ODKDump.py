#!/usr/bin/python3

#
# Copyright (C) 2020, 2021, 2022 Humanitarian OpenstreetMap Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import sys
import ODKForm
from ODKInstance import ODKInstance
import argparse
from datetime import datetime
from osmfile import OsmFile
from convert import Convert
import logging
import re
from shapely.geometry import Point, LineString, Polygon


if __name__ != '__main__':
    print("This is not a loadable python module!")
    exit

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
parser.add_argument("-x", "--xform", required=True, help="input xform file in XML format")
parser.add_argument("-i", "--infile", required=True, help="input data in XML format")
parser.add_argument("-o", "--outdir", help="Output Directory (defaults to $PWD)")
args = parser.parse_args()

# if verbose, dump to the terminal as well as the logfile.
if not args.verbose:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

# Get the basename without the suffix
xform = args.xform.replace(".xml", "")
xinst = args.infile.replace(".xml", "")

# This is the output file in OSM format
osmfile = OsmFile(filespec=xinst + ".osm")
osmfile.header()

# Read in the XML config file from ODK Collect
odkform = ODKForm.ODKForm()
odkform.parse(xform + ".xml")

# Read the YAML config file for this XForm
yaml = Convert(xform + ".yaml")
yaml.dump()

# Read the data instance
inst = ODKInstance()
data = inst.parse(args.infile)

out = ""
groups = dict()
tags = dict()
node = dict()
way = dict()
for x in data:
    # print(data[x])
    lat = ""
    lon = ""
    reg = re.compile("group*")
    # There should be only one timestamp we want, namely 'end'
    if odkform.getNodeType(x) == "dateTime":
        dt = data[x][:data[x].find(".")]
        timestamp = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
        groups['timestamp'] = timestamp
        node['timestamp'] = timestamp
        continue
    elif reg.match(x):
        groups[x] = data[x]
        for key, value in data[x].items():
            if odkform.getNodeType(x, key) == "geotrace":
                ln = "LINESTRING("
                ln += groups[x][key] + ")"
                groups[x][key] = ln
            if odkform.getNodeType(x, key) == "geoshape":
                #print(odkform.getNodeType(x, key))
                py = "POLYGON("
                py += groups[x][key] + ")"
                groups[x][key] = py
            elif odkform.getNodeType(x, key) == "geopoint":
                #print(odkform.getNodeType(x, key))
                tmp = data[x][key].split(" ")
                lat = tmp[0]
                lon = tmp[1]
                node['lat'] = tmp[0]
                node['lon'] = tmp[1]
            elif odkform.getNodeType(x, key) == "list":
                space = data[x][key].find(" ")
                if space <= 0:
                    values = yaml.getKeyword(data[x][key])
                    tags[key] = values
                else:
                    for item in data[x][key].split(" "):
                        if key == "name" or key == "alt_name":
                            tags[key] = data[x][key]
                        else:
                            values = yaml.getKeyword(item)
                            if key in tags:
                                tags[key] = tags[key] + ";" + item
                            else:
                                tags[key] = values
            elif odkform.getNodeType(x, key) == "image":
                pass
            elif odkform.getNodeType(x, key) == "binary":
                pass
            elif odkform.getNodeType(x, key) == "int":
                if data[x][key] is not None:
                    tags[key] = data[x][key]
            elif odkform.getNodeType(x, key) == "string":
                if data[x][key] is not None:
                    tags[key] = data[x][key]
            #else:
            #    tags[x] = key

node['lat'] = lat
node['lon'] = lon
node['tags'] = tags
print("FOO: %r" % node)
out += osmfile.createNode(node)

# We're done
osmfile.write(out)
osmfile.footer()

print("Output file: %s" % xinst + ".osm")
#print(groups)
