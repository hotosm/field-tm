# Copyright (c) Humanitarian OpenStreetMap Team
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#

#!/usr/bin/python3

import argparse
import json
import os
import subprocess
from datetime import datetime

import requests


def query(query_string, overpass_url):
    """Accept a query in Overpass API query language,
    return a dict from json of the data from an Overpass server,
    which can be dumped as a json file or used as a dict.
    """
    try:
        response = requests.get(overpass_url, params={"data": query_string})
    except:
        print("overpass did not want to answer that one\n")
    if response.status_code == 200:
        print(
            f"The overpass API at {overpass_url} accepted the query and "
            f"returned something."
        )
        data = response.json()
        return data
    else:
        print(response)
        print(
            "Yeah, that didn't work. We reached the Overpass API but "
            "something went wrong on the server side."
        )


def osm_json_to_geojson(infile):
    """Accept a raw JSON file of data from an Overpass API query.
    Return a GeoJSON string of the same data, after converting all polygons
    to points. USING THE NODE MODULE FROM OVERPASS, WHICH MUST BE INSTALLED
    USING sudo npm install -g osmtogeojson.
    """
    try:
        print(f"Trying to turn {infile} into geojson")
        p = subprocess.run(
            ["osmtogeojson", infile], capture_output=True, encoding="utf-8"
        )
        geojsonstring = p.stdout
        print(
            f"The osmtogeojson module accepted {infile} and "
            f"returned something of type {type(geojsonstring)}"
        )
        return geojsonstring
    except Exception as e:
        print(e)


def centroid_and_merge_to_points(geojson_in, geojson_out):
    """Accept a GeoJSON file containing polygons and points,
    return a GeoJSON containing only points with centroids for polygons.
    Lines are ignored.
    """
    pass


if __name__ == "__main__":
    """return a file of raw JSON data from Overpass API from an input file
    of text containing working Overpass Query Language
    """
    p = argparse.ArgumentParser(usage="usage: attachments [options]")
    p.add_argument("infile", help="Text file in overpass query language")
    p.add_argument(
        "-url",
        "--overpass_url",
        help="Overpass API server URL",
        default="https://overpass.kumi.systems/api/interpreter",
    )
    args = p.parse_args()

    (directory, basename) = os.path.split(args.infile)
    (basename_no_ext, extension) = os.path.splitext(basename)
    (basefilename, extension) = os.path.splitext(args.infile)
    date = datetime.now().strftime("%Y_%m_%d")
    dirdate = os.path.join(directory, date)
    rawdatafilepath = f"{dirdate}_{basename_no_ext}.json"
    geojsonfilepath = f"{dirdate}_{basename_no_ext}.geojson"

    with open(args.infile) as inf:
        data = query(inf.read(), args.overpass_url)

        with open(rawdatafilepath, "w") as of:
            of.writelines(json.dumps(data))

        geojson = osm_json_to_geojson(rawdatafilepath)

        with open(geojsonfilepath, "w") as of:
            of.write(geojson)
