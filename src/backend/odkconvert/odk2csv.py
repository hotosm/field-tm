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
import sys
import re
from collections import OrderedDict
import csv
from pathlib import Path
from datetime import tzinfo, datetime


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ODK XML instance file to CSV format')
    parser.add_argument("-v", "--verbose", nargs="?",const="0", help="verbose output")
    parser.add_argument("-i","--instance", help='The instance file(s) from ODK Collect')
    # parser.add_argument("-d","--directories", help='A local directory pato to instance files.')
    #parser.add_argument("-o","--outfile", default='tmp.csv', help='The output file for JOSM')
    args = parser.parse_args()

    # if verbose, dump to the termina
    if not args.verbose:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    xmlfiles = list()
    if args.instance.find("*") >= 0:
        toplevel = Path()
        for dir in toplevel.glob(args.instance):
            if dir.is_dir():
                xml = os.listdir(dir)
                # There is always only one XML file per instance
                full = os.path.join(dir, xml[0])
                xmlfiles.append(full)
    else:
        toplevel = Path(args.instance)
        if toplevel.is_dir():
            # There is always only one XML file per instance
            full = os.path.join(toplevel, os.path.basename(toplevel))
            xmlfiles.append(full + ".xml")

    print(xmlfiles)

    rows = list()
    for instance in xmlfiles:
        logging.info("Processing instance file: %s" % instance)
        with open(instance, 'rb') as file:
            # Instances are small, read the whole file        
            xml = file.read(os.path.getsize(instance))
            doc = xmltodict.parse(xml)
            fields = list()
            tags = dict()
            # import epdb; epdb.st()
            data = doc['data']
            for i, j in data.items():
                if j is None:
                    continue
                print(i, j)
                pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
                if pat.match(str(j)):
                    fields.append("lat")
                    gps = j.split(' ')
                    tags["lat"] = gps[0]
                    fields.append("lon")
                    tags["lon"] = gps[1]
                    continue
                if type(j) == OrderedDict:
                    for ii, jj in j.items():
                        if jj is None:
                            continue
                        if ii[0:1] != "@":
                            fields.append(ii)
                        if type(jj) == OrderedDict:
                            for iii, jjj in jj.items():
                                if jjj is not None:
                                    fields.append(iii)
                                    tags[iii] = jjj
                                    # print(iii, jjj)
                        else:
                            # print(ii, jj)
                            tags[ii] = jj
                else:
                    if i[0:1] != "@":
                        fields.append(i)
                        tags[i] = j
        rows.append(tags)

    xml = os.path.basename(xmlfiles[0])
    tmp = xml.split("_")
    now = datetime.now()
    timestamp = f'_{now.year}_{now.hour}_{now.minute}'
    outfile = tmp[0] + timestamp + ".csv"
    with open(outfile, 'w', newline='') as csvfile:
        csv = csv.DictWriter(csvfile, dialect='excel',fieldnames=fields)
        csv.writeheader()
        for row in rows:
            csv.writerow(row)

    print("Wrote: %s" % outfile)
