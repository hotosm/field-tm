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

import logging
import string
import epdb
import argparse
from yamlfile import YamlFile
import pytest

parser = argparse.ArgumentParser(description='Read and parse a YAML file')
parser.add_argument("--infile", default="../xforms.yaml", help='The YAML input file')
args = parser.parse_args()

data = YamlFile(args.infile)

def test_validate():
    """Tests for things under validate"""
    foo = data.getValues("validate")
    bar = foo[1]['leisure']
    assert "firepit" in bar


def test_bool_good():
    assert data.getValues("bear box") is True


def test_bool_bad():
    assert data.getValues("bad keyword") is not True


def test_value():
    assert data.getKeyword("caravans") == "tourism"


if __name__ == '__main__':
    test_validate()
    test_bool_good()
    test_bool_bad()
    test_value()
