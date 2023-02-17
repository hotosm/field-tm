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

import sys
import csv
import logging
import xmltodict
import argparse
#from shapely.geometry import Point, LineString, Polygon
import epdb                      # FIXME: remove later
from collections import OrderedDict


class ODKObject(object):
    def __init__(self, name=str(), type=str(), data=str()):
        self.name = name
        self.type = type
        self.data = data

    def dump(self):
        print("Name: %s, Type %s" % (self.name,self.type))
        print("\tValue: %s" % self.data)

class ODKInstance(object):
    def __init__(self, file):
        self.odkobjs = list()
#super(ODKInstance, self).__init__()
        self.name = file
        self.odkobjs = list()

    # def parse(self, instance):
    #     print("Parsing Instance: %s" % instance)
    #     with open(instance, 'rb') as file:
    #         xml = file.read(10000)  # Instances are small, read the whole file
    #         doc = xmltodict.parse(xml)
    #     try:
    #         field = doc['data']
    #     except:
    #         logging.warning("No data in this instance")
    #         return False
    #     for field in doc['data']:
    #         if field == 'meta' or field == '@id':
    #             continue
    #         # Get the type of this nodeset
    #         ftype = form.getNodeType(field)
    #         if not ftype:
    #             continue
    #         value = doc['data'][field]
    #         # A Some field types contains multiple internal fields,
    #         # Location - latitude, longitude, altitude, accuracy
    #         print("\tFTYPE = %r" % ftype)
    #         print("\tFVAL = %r" % field)
    #         print("\tVALUE = %r" % value)
    #         obj = ODKObject(field, ftype, value)
    #         if len(ftype) == 0:
    #             continue
    #         elif ftype == 'geotrace':
    #             #gps = doc['data'][field].split(' ')
    #             print("\tGEOTRACE: %r" % doc['data'][field])
    #         elif ftype == 'geopoint':
    #             gps = doc['data'][field].split(' ')
    #             #print("\tGPS: %r" % gps)
    #         elif ftype == 'string':
    #             #logging.debug("\tString: %r" % doc['data'][field])
    #             # tmptag = osm.makeTag(field, doc['data'][field])
    #             if doc['data'][field] is not None:
    #                 # alltags.append(osm.makeTag(field, doc['data'][field]))
    #                 pass
    #         elif ftype == 'int':
    #             number = doc['data'][field]
    #             print('\tInt %r' % number)
    #             if number is not None:
    #                 # alltags.append(osm.makeTag(field, number))
    #                 # Select fields usually are a yes/no.
    #                 pass
    #         elif ftype == 'select':
    #             print('\tMulti Select: %r' % str(doc['data'][field]))
    #             if doc['data'][field]:
    #                 for data in doc['data'][field].split(' '):
    #                     print("DATA1: %r" % data)
    #                     tmptag = osm.makeTag(field, data)
    #                     print("FOOOO1: %r" % tmptag)
    #                     if len(tmptag) > 0:
    #                         # alltags.append(osm.makeTag(field, data))
    #                         pass
    #         elif ftype == 'select1':
    #             print('Select')
    #             if doc['data'][field]:
    #                 for data in doc['data'][field].split(' '):
    #                     print("DATA2: %r" % data)
    #                     tmptag = osm.makeTag(field, data)
    #                     print("FOOOO2: %r" % tmptag)
    #                     # alltags.append(osm.makeTag(field, data))
    #                     #print("FIXME: %r" % (gps, field))

    #     self.odkobjs = list()

    def dump(self):
        print("Dumping ODKInstance: %s" % self.name)
        for obj in self.odkobjs:
            obj.dump()

    def parse(self, instance):
        print("Parsing Instance: %s" % instance)
        with open(instance, 'rb') as file:
            xml = file.read(10000)  # Instances are small, read the whole file
            doc = xmltodict.parse(xml)
        try:
            field = doc['data']
        except:
            logging.warning("No data in this instance")
            return False
        for i, j in field.items():
            print(i, j)
            if type(j) == OrderedDict:
                for ii, jj in j.items():
                    print(ii, jj)

        # for field in doc['data']:
        #     if field == 'meta' or field == '@id':
        #         continue
        #     # Get the type of this nodeset
        #     ftype = form.getNodeType(field)
        #     if not ftype:
        #         continue
        #     value = doc['data'][field]
        #     # A Some field types contains multiple internal fields,
        #     # Location - latitude, longitude, altitude, accuracy
        #     print("\tFTYPE = %r" % ftype)
        #     print("\tFVAL = %r" % field)
        #     print("\tVALUE = %r" % value)
        #     obj = ODKObject(field, ftype, value)
        #     if len(ftype) == 0:
        #         continue
        #     elif ftype == 'geotrace':
        #         #gps = doc['data'][field].split(' ')
        #         print("\tGEOTRACE: %r" % doc['data'][field])
        #     elif ftype == 'geopoint':
        #         gps = doc['data'][field].split(' ')
        #         #print("\tGPS: %r" % gps)
        #     elif ftype == 'string':
        #         #logging.debug("\tString: %r" % doc['data'][field])
        #         # tmptag = osm.makeTag(field, doc['data'][field])
        #         if doc['data'][field] is not None:
        #             # alltags.append(osm.makeTag(field, doc['data'][field]))
        #             pass
        #     elif ftype == 'int':
        #         number = doc['data'][field]
        #         print('\tInt %r' % number)
        #         if number is not None:
        #             # alltags.append(osm.makeTag(field, number))
        #             # Select fields usually are a yes/no.
        #             pass
        #     elif ftype == 'select':
        #         print('\tMulti Select: %r' % str(doc['data'][field]))
        #         if doc['data'][field]:
        #             for data in doc['data'][field].split(' '):
        #                 print("DATA1: %r" % data)
        #                 tmptag = osm.makeTag(field, data)
        #                 print("FOOOO1: %r" % tmptag)
        #                 if len(tmptag) > 0:
        #                     # alltags.append(osm.makeTag(field, data))
        #                     pass
        #     elif ftype == 'select1':
        #         print('Select')
        #         if doc['data'][field]:
        #             for data in doc['data'][field].split(' '):
        #                 print("DATA2: %r" % data)
        #                 tmptag = osm.makeTag(field, data)
        #                 print("FOOOO2: %r" % tmptag)
        #                 # alltags.append(osm.makeTag(field, data))
        #                 #print("FIXME: %r" % (gps, field))

        #     self.odkobjs.append(obj)

        return self.odkobjs

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?",const="0", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="instance data in XML format")
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

    xinst = args.infile
    inst = ODKInstance(xinst)
    data = inst.parse(args.infile)
