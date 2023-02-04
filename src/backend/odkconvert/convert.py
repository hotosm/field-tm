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

from yamlfile import YamlFile
import logging
import epdb
import argparse
import sys

class Convert(YamlFile):
    """A class to apply a YAML config file and convert ODK to OSM"""
    def __init__(self, xform=None):
        if xform is None:
            xform = "xforms.yaml"
        self.yaml = YamlFile(xform)
        self.filespec = xform
        # Parse the file contents into a data structure to make it
        # easier to retrieve values
        self.convert = dict()
        self.ignore = list()
        self.private = list()
        for item in self.yaml.yaml['convert']:
            key = list(item.keys())[0]
            value = item[key]
            # print("ZZZZ: %r, %r" % (key, value))
            if type(value) is str:
                self.convert[key] = value
            elif type(value) is list:
                vals = dict()
                for entry in value:
                    if type(entry) is str:
                        # epdb.st()
                        tag = entry
                    else:
                        tag = list(entry.keys())[0]
                        vals[tag] = entry[tag]
                self.convert[key] = vals
        self.ignore = self.yaml.yaml['ignore']
        self.private = self.yaml.yaml['private']
        self.multiple = self.yaml.yaml['multiple']

    def privateData(self, keyword):
        """See is a keyword is in the private data category"""
        return keyword in self.private

    def convertData(self, keyword):
        """See is a keyword is in the convert data category"""
        return keyword in self.convert

    def ignoreData(self, keyword):
        """See is a keyword is in the convert data category"""
        return keyword in self.ignore

    def escape(self, value):
        """Escape characters like embedded quotes in text fields"""
        tmp = value.replace(" ", "_")
        return tmp.replace("'", "&apos;")

    def getKeyword(self, value):
        """Get the value for a keyword from the yaml file"""
        key = self.yaml.getValues(value)
        if type(key) == bool:
            return value
        if len(key) == 0:
            key = self.yaml.getKeyword(value)
        return key

    def getValues(self, tag=None):
        """Get the values for a primary key"""
        if tag is not None:
            if tag in self.convert:
                return self.convert[tag]
        else:
            return None

    # def convertList(self, values=list()):
    #     """Convert a python list of tags"""
    #     features = list()
    #     entry = dict()
    #     for value in values:
    #         entry[self.yaml.getKeyword(value)] = value
    #         features.append(entry)
    #     return features

    def convertEntry(self, tag=None, value=None):
        """Convert a tag and value from the ODK represention to an OSM one"""
        all = list()

        # If it's not in any conversion data, pass it through unchanged.
        if tag not in self.convert and tag not in self.ignore and tag not in self.private:
            return tag, value

        newtag = None
        newval = None
        # If the tag is in the config file, convert it.
        if self.convertData(tag):
            newtag = self.convertTag(tag)
            if newtag != tag:
                logging.debug("Converted Tag for entry \'%s\' to \'%s\'" % (tag, newtag))

        if newtag is None:
            newtag = tag
        # Truncate the elevation, as it's really long
        if newtag == 'ele':
            value = value[:7]
        newval = self.convertValue(newtag, value)
        if newval != value:
            logging.debug("Converted Value for entry \'%s\' to \'%s\'" % (value, newval))
            for i in newval:
                key = list(i.keys())[0]
                newtag = key
                newval = i[key]
                all.append( { newtag: newval } )
        else:
            all.append( { newtag: newval } )

        # if newtag not in self.tags:
        #     tmp = { newtag: None }
        #     key = list()
        #     all.append(tmp)
        # else:
        #     val = self.tags[newtag]
        #     key = list(val.keys())[0]
        #     logging.debug("Converted Value for entry %s to %s" % (tag, value))
        #     # all = self.Value(tag, value)
        return all

    def convertValue(self, tag=None, value=None):
        """Convert a single tag value"""
        all = list()

        vals = self.getValues(tag)
        # There is no conversion data for this tag
        if vals is None:
            return value

        if type(vals) is dict:
            if value not in vals:
                all.append({ tag: value })
                return all
            if type(vals[value]) is bool:
                entry = dict()
                if vals[value]:
                    entry[tag] = "yes"
                else:
                    entry[tag] = "no"
                all.append(entry)
                return all
            for item in vals[value].split(","):
                entry = dict()
                tmp =  item.split("=")
                if len(tmp) == 1:
                    entry[tag] = vals[value]
                else:
                    entry[tmp[0]] =  tmp[1]
                    logging.debug("\tValue %s converted to %s" % (value, entry))
                all.append(entry)
        return all

    def convertTag(self, tag=None):
        """Convert a single tag"""
        if tag in self.convert:
            newtag = self.convert[tag]
            if type(newtag) is str:
                logging.debug("\tTag \'%s\' converted to \'%s\'" % (tag, newtag))
                tmp = newtag.split("=")
                if len(tmp) > 1:
                    newtag = tmp[0]
            elif type(newtag) is list:
                logging.error("FIXME: list()")
                # epdb.st()
                return tag
            elif type(newtag) is dict:
                # logging.error("FIXME: dict()")
                return tag
            return newtag
        else:
            return tag

    def dump(self):
        """Dump the contents of the yaml file"""
        print("YAML file: %s" % self.filespec)
        for key, val in self.convert.items():
            if type(val) is list:
                print("Tag %s is" % key)
                for data in val:
                    print("\t%r" % data)
            else:
                print("Tag %s is %s" % (key, val))

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
    parser.add_argument("-x", "--xform", default="xform.yaml", help="Default Yaml file")
    parser.add_argument("-i", "--infile", default="XForms/Ruwa/ruwanigerproject_waterpoint_form.csv", help='The YAML input file')
    args = parser.parse_args()

    # convert = Convert(args.xform)
    convert = Convert("xforms.yaml")
    print("-----")
    # tag = convert.convertTag("waterpoint_seasonal")
    # entry = convert.convertEntry("waterpoint_seasonal")
    # print("YY: %r" % entry)

    # print(convert.convertTag("tourism"))
    # entry = convert.convertEntry("tourism")
    # print(entry)
    # value = convert.convertEntry("waterpoint_seasonal")
    # print(value)
    # print("===============")

    # tag = convert.convertTag("waterpoint")
    # print(tag)
    # value = convert.convertValue("waterpoint", "well")
    # print(value)
    # value = convert.convertValue("power", "solar")

    entry = convert.convertEntry("waterpoint", "faucet")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("operational_status", "closed")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("seasonal", "wet")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("seasonal", "rainy")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("power", "solar")
    for i in entry:
        print("XX: %r" % i)
