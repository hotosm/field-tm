#!/usr/bin/python3

#
#   Copyright (C) 2020, 2021, 2022 Humanitarian OpenstreetMap Team
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

import logging
import argparse
import xmltodict
import os
import re
import epdb
import sys
from collections import OrderedDict


class ODKForm(object):
    """Support for parsing an XLS Form"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()
        self.groups = dict()
        self.ignore = ('label', '@appearance', 'hint', 'upload')

    def parseSelect(self, select=dict()):
        print("parseSelect %r" % type(select))
        newsel = dict()
        if 'item' in select:
            data = self.parseItems(select['item'])
            ref = os.path.basename(select['@ref'])
            for key in data:
                if key in self.ignore:
                    continue
                newsel[ref] = data
            print("\tQQQQQ %r" % (newsel))
        return newsel

    def parseItems(self, items):
        print("\tparseItems: %r: %r" % (type(items), items))
        newitems = list()
        newdata = dict()
        group = None
        subgroup = None
        label = None
        # if type(items) == OrderedDict:
        #     data = list()
        #     data.append(items)
        # else:
        #     data = items

        for values in items:
            newitems.append(values['value'])

            # if type(values) == str:
            #     continue

        #     val = values['label']['@ref'].replace("/data/", "")
        #     tmp = val.split('/')
        #     group = tmp[0].replace("jr:itext(\'", "")
        #     fields = len(tmp)
        #     if fields > 2:
        #         subgroup = tmp[1]
        #         label = tmp[2].replace(":label\')", "")
        #     else:
        #         subgroup = None
        #         label = tmp[1].replace(":label\')", "")
        #     # print("VALUES: %r / %r / %r" % (group, subgroup, label))
        #     if subgroup not in newdata:
        #         newdata[subgroup] = list()
        #     #newdata[subgroup].append(label)
        #     newitems.append(label)
        # return group, subgroup, newitems
        return newitems

    def parseGroup(self, group=dict()):
        print("\tparseGroup %r" % (type(group)))
        newgrp = dict()
        if type(group) == list:
            for val in group:
                for k in group:
                    print("\nZZZZ1 %r" % (k))
        else:                   # it's a list
            for keyword, data in group.items():
                ref = None
                # FIXME: for now,. ignore media files
                if keyword in self.ignore:
                    continue
                print("WWW3 %r, %r" % (keyword, type(data)))
                #pat = re.compile('select[0-9]*')
                #if pat.match(keyword):
                if keyword[0:6] == 'select':
                    print("WWW4 select")
                    select = self.parseSelect(data)
                    #self.groups[] =

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert CSV from ODK Central to OSM XML')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", help='The input file downloaded from ODK Central')
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

    odkform = ODKForm()
    odkform.parse(args.infile)

    print("---------------------------")
    odkform.dump()
    print("---------------------------")
