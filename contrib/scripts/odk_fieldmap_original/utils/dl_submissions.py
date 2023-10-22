# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

#!/bin/python3

"""Accepts:
- A base URL for an ODK Central server
- A tuple of username and password to said server
- An ID number for a project on the server
- An output directory where the results will be placed.

And downloads all of the submissions from that server as CSV

TODO (KNOWN BUGS):
- For now it expects a project with multiple form, but all basically
identical (a single ODK survey with different GeoJSON forms).
If it gets a project with multiple forms, the collated CSV will
be fucked up.
- The geopoint column to be expanded is hard-coded to all-xlocation.
That only works for forms following Rob Savoye's current template.
This needs to be a command line argument.
- Both the geopoint expansion and creation of collated CSV are hardcoded
to yes; not a big deal but should be flags.
"""

import argparse
import csv
import os
from io import BytesIO, StringIO
from zipfile import ZipFile as zf

from odk_requests import csv_submissions, forms


def project_forms(url, aut, pid):
    """Returns a list of all forms in an ODK project."""
    formsr = forms(url, aut, pid)
    formsl = formsr.json()
    # TODO this returns happily with wrong credentials,
    # thinking that the error message actually constitutes
    # data about 2 forms. Should fail noisily.
    print(f"There are {len(formsl)} forms in project {pid}.")
    return formsl


def project_submissions_zipped(url, aut, pid, formsl, outdir):
    """Downloads all of the submissions frm a given ODK Central project."""
    for form in formsl:
        form_id = form["xmlFormId"]
        print(f"Checking submissions from {form_id}.")
        subs_zip = csv_submissions(url, aut, pid, form_id)

        outfilename = os.path.join(outdir, f"{form_id}.csv.zip")
        outfile = open(outfilename, "wb")
        outfile.write(subs_zip.content)


def expand_geopoints(csv, geopoint_column_name):
    """Accepts a list representing a set of CSV ODK submissions and expands
    a geopoint column to include lon, lat, ele, acc columns for easy
    import into QGIS or direct conversion to GeoJSON or similar.
    """
    newcsv = []
    try:
        header_row = csv[0]
        column_num = header_row.index(geopoint_column_name)
        print(f"I found {geopoint_column_name} at index {column_num}")
        newheaderrow = header_row[: column_num + 1]
        newheaderrow.extend(["lat", "lon", "ele", "acc"])
        newheaderrow.extend(header_row[column_num + 1 :])
        newcsv.append(newheaderrow)
        for row in csv[1:]:
            split_geopoint = row[column_num].split()
            print(split_geopoint)
            if len(split_geopoint) == 4:
                newrow = row[: column_num + 1]
                newrow.extend(split_geopoint)
                newrow.extend(row[column_num + 1 :])
            newcsv.append(newrow)

    except Exception as e:
        print("Is that the right geopoint column name?")
        print(e)

    return newcsv
 
def odk_geo2wkt(jrstring, node_delimiter = ';', delimiter = ' '):
    """Takes a Javarosa geo string and converts it into Well-Known-Text.
    Assumes that the string consists of the usual space-delimited 
    lat, lon, elevation, accuracy elements for each node, and nodes are
    semicolon-delimited (as is the case with ODK geowidget output). 
    If there's only one node, it creates a WKT point. If more than one,
    and the last isn't identical to the first, it creates a polyline.
    If more than two, and the last is identical to the first, it creates
    a polygon. In any other cases it should return an error."""
    nodes = [x.strip() for x in jrstring.split(node_delimiter)]
    wkt_feature_type = ''
    end_paren = ')'
    if len(nodes) == 0:
        print("There's nothing in there.")
        return None
    elif len(nodes) == 1:
        wkt_feature_type = 'POINT ('
    elif len(nodes) == 2:
        wkt_feature_type = 'LINESTRING ('
    elif len(nodes) >= 3:
        if nodes[0] == nodes[-1]:
            wkt_feature_type = 'POLYGON (('
            end_paren = '))'
        else:
            wkt_feature_type = 'LINESTRING ('

    
    try:
        positions = []
        for node in nodes:
            coords = node.split(delimiter)
            lat = float(coords[0])
            lon = float(coords[1])
            positions.append(f'{lon} {lat}')
        positions_string = ','.join(positions)
        return (f'{wkt_feature_type}{positions_string}{end_paren}')
    except Exception as e:
        return None
        
        

def project_submissions_unzipped(
    url, aut, pid, formsl, outdir, collate, expand_geopoint
):
    """Downloads and unzips all of the submissions from a given ODK project."""
    if collate:

        collated_outfilepath = os.path.join(outdir, f'project_{pid}_submissions'
                                            '_collated.csv')
        c_outfile = open(collated_outfilepath, 'w')
        cw = csv.writer(c_outfile)

        # create a single file to dump all repeat data lines
        # TODO multiple collated files for multiple repeats
        c_repeatfilepath = os.path.join(outdir, f'project_{pid}_repeats'
                                        '_collated.csv')
        c_repeatfile = open(c_repeatfilepath, 'w')
        cr = csv.writer(c_repeatfile)
        
    for fidx, form in enumerate(formsl):
        form_id = form['xmlFormId']
        print(f'Checking submissions from {form_id}.')
        subs_zip = csv_submissions(url, aut, pid, form_id)
        subs_bytes = BytesIO(subs_zip.content)
        subs_bytes.seek(0)
        subs_unzipped = zf(subs_bytes)
        sub_namelist = subs_unzipped.namelist()

        subcount = len(sub_namelist)
        print(f'There are {subcount} files in submissions from {form_id}:')
        print(sub_namelist)

        # Now save the rest of the files
        for idx, sub_name in enumerate(sub_namelist):
            subs_bytes = subs_unzipped.read(sub_name)
            outfilename = os.path.join(outdir, sub_name)

            # Some attachments need a subdirectory
            suboutdir = os.path.split(outfilename)[0]
            if not os.path.exists(suboutdir):
                os.makedirs(suboutdir)

            # If it is a csv, open it and see if it is more than one line
            # This might go wrong if something is encoded in other than UTF-8

            if os.path.splitext(sub_name)[1] == '.csv':
                subs_stringio = StringIO(subs_bytes.decode())
                subs_list = list(csv.reader(subs_stringio))
                # Check if there are CSV lines after the headers
                subs_len = len(subs_list)
                print(f'{sub_name} has {subs_len - 1} submissions')
                if subs_len > 1:
                    subs_to_write = subs_list
                    if expand_geopoint:
                        subs_to_write = expand_geopoints(subs_list, expand_geopoint)
                    with open(outfilename, "w") as outfile:
                        w = csv.writer(outfile)
                        w.writerows(subs_to_write)
                    if collate:
                        if not idx:                            
                            if not fidx:
                                # First form. Include header
                                cw.writerows(subs_to_write)
                            else:
                                # Not first form. Skip first row (header)
                                cw.writerows(subs_to_write[1:])
                        else:
                            # Include header because it's a repeat
                            # TODO actually create a separate collated
                            # CSV output for each repeat in the survey
                            cr.writerows(subs_to_write)
    
            else:
                with open(outfilename, "wb") as outfile:
                    outfile.write(subs_bytes)


if __name__ == "__main__":
    """Downloads all of the submissions from a given ODK Central project"""

    p = argparse.ArgumentParser()

    # Positional args
    p.add_argument("url", help="ODK Central Server URL")
    p.add_argument("username", help="ODK Central username")
    p.add_argument("password", help="ODK Central password")
    p.add_argument("pid", help="ODK Central project id number")
    p.add_argument("outdir", help="Output directory to write submissions")

    # Optional args

    p.add_argument('-gc', '--geopoint_column', default='all-xlocation', help=
                   'The name of the column in the submissions containing '
                   'geometry in Javarosa form for expansion or conversion')

    # Flag args
    p.add_argument(
        "-c",
        "--collate",
        action="store_true",
        help="Attempt to collate the CSV from all submissions "
        "into a single CSV file",
    )
    p.add_argument(
        "-z",
        "--zipped",
        action="store_true",
        help="Don't bother trying to extract and/or collate csv "
        "submissions, just get the zip files",
    )
    p.add_argument(
        "-x",
        "--expand_geopoint",
        action="store_true",
        help="Convert a the column given by -gc, containing a Javarosa "
        "geopoint string, into four columns: "
        "lat, lon, elevation, accuracy",
    )

    a = p.parse_args()

    formsl = project_forms(a.url, (a.username, a.password), a.pid)
    
    if a.zipped:
        subs = project_submissions_zipped(a.url,
                                          (a.username, a.password),
                                          a.pid,
                                          formsl,
                                          a.outdir
                                          )
    else:
        subs = project_submissions_unzipped(a.url,
                                            (a.username, a.password),
                                            a.pid,
                                            formsl,
                                            a.outdir,
                                            a.collate,
                                            a.expand_geopoint
                                            )
    
