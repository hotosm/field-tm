#!/usr/bin/python3

# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     Underpass is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
import argparse
from osmfile import OsmFile

parser = argparse.ArgumentParser(description='Read and parse a CSV file from ODK Central')
parser.add_argument("--infile", default="test.csv", help='The CSV input file')
args = parser.parse_args()

# Delete the test output file
if os.path.exists("test.osm"):
    os.remove("test.osm")

osm = OsmFile(filespec="test.osm")


def test_init():
    """Make sure the OSM file is initialized"""
    assert os.path.exists("test.osm")


def test_header():
    osm.header()
    assert os.stat("test.osm").st_size > 0


def test_footer():
    osm.footer()
    tmp = open("test.osm", 'r')
    lines = tmp.readlines()
    for line in lines:
        last = line
    assert last == "</osm>\n"


def test_create_tag():
    tmp = osm.createTag('foo', 'bar')
    assert tmp['foo'] == 'bar'


def test_create_node_notags():
    node = dict(osm_id=12345, lat=1, lon=2, uid=54321, user='bar')
    tmp = osm.createNode(node).lstrip().split(' ')
    assert tmp[1] == "id='12345'" and tmp[2] == "version='1'" and tmp[3] == "lat='1'"
    # print(tmp)


def test_create_node_modified():
    node = dict(osm_id=12345, lat=1, lon=2, version=2, uid=54321, user='bar')
    tmp = osm.createNode(node, modified=True)
    assert tmp.find("action")
    # print(tmp)


def test_create_node_tags():
    node = dict()
    tags = dict(foo='bar', bar='foo', uid=54321, user='bar')
    node['osm_id'] = 123456
    node['lat'] = 2
    node['lon'] = 3
    node['user'] = 'foo'
    node['uid'] = 12345
    node['tags'] = tags
    tmp = osm.createNode(node)
    assert tmp.find('bar') and tmp.find('foo')
    # print(tmp)


def test_create_way():
    way = dict()
    tags = dict(foo='bar', bar='foo')
    refs = list()
    way['osm_id'] = 123456
    way['user'] = 'foo'
    way['uid'] = 12345
    refs.append(12345)
    refs.append(23456)
    refs.append(34567)
    way['tags'] = tags
    way['refs'] = refs
    tmp = osm.createWay(way)
    # print(tmp)


if __name__ == '__main__':
    test_init()
    test_header()
    test_footer()
    test_create_tag()
    test_create_node_notags()
    test_create_node_tags()
    test_create_way()
    test_create_node_modified()
    # Delete the test output file
    if os.path.exists("test.osm"):
        os.remove("test.osm")

