#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     ODKConvert is free software: you can redistribute it and/or modify
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

import yaml
import epdb
import argparse
import logging
import sys
from pprint import pprint

"""This parses a yaml file into a dictionary for easy access."""


class YamlFile(object):
    """Config file in YAML format"""
    def __init__(self, filespec=None):
        self.filespec = filespec
        self.file = open(filespec, 'rb').read()
        #print(self.file)
        self.yaml = yaml.load(self.file, Loader=yaml.Loader)
        # pprint(self.yaml)

    def privateData(self, keyword):
        """See if a keyword is in the private data category"""
        return keyword in self.yaml['private']

    def ignoreData(self, keyword):
        """See if a keyword is in the ignore data category"""
        return keyword in self.yaml['ignore']

    def tagsData(self, keyword):
        """See if a keyword is in the tags completness section"""
        return keyword in self.yaml['tags']

    def hasList(self, keyword=None):
        for tags in self.yaml['tags']:
            logging.debug(type(tags))

    def dump(self):
        """Dump the contents of the yaml file"""
        print("YAML file: %s" % self.filespec)

#
# This script can be run standalone for debugging purposes. It's easier to debug
# this way than using pytest,
#
if __name__ == '__main__':
    # Enable logging to the terminal by default
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    parser = argparse.ArgumentParser(description='Read and parse a YAML file')
    parser.add_argument("-i", "--infile", default="./xforms.yaml", help='The YAML input file')
    args = parser.parse_args()

    yaml = YamlFile(args.infile)
