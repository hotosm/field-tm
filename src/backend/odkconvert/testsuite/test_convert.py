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
from convert import Convert

parser = argparse.ArgumentParser(description='Read and convert a CSV file from ODK Central')
parser.add_argument("--infile", default="test.csv", help='The CSV input file')
args = parser.parse_args()


if os.path.exists("xforms.yaml"):
    csv = Convert("xforms.yaml")
elif os.path.exists("../xforms.yaml"):
    csv = Convert("../xforms.yaml")


def test_get_keyword():
    """Convert a feature"""
    result = csv.getKeyword("sac_scale")
    assert result == "path"


def test_no_keyword():
    """Convert a feature that doesn't exist"""
    result = csv.getKeyword("doesnt exist")
    assert result == "doesnt exist"


def test_convert_list():
    """Convert a list of features"""
    features = list()
    features.append("firepit")
    features.append("parking")
    features.append("viewpoint")
    result = csv.convertList(features)
    assert result[0]['leisure'] == "firepit" and result[1]['amenity'] == "parking" and result[2]['tourism'] == "viewpoint"

def test_bool_keyword():
    """Convert a feature"""
    result = csv.getKeyword("bear box")
    assert result == "bear box"


def test_convert_tag():
    tmp1 = csv.convertTag("altitude")
    tmp2 = csv.convertTag("foobar")
    assert tmp1 == "ele" and tmp2 == "foobar"


# Run standalone for easier debugging when not under pytest
if __name__ == '__main__':
    test_get_keyword()
    test_no_keyword()
    test_convert_list()
    test_bool_keyword()
    test_convert_tag()
