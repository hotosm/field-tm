# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

"""
    Accepts:
    - A base URL for an ODK Central server
    - A tuple of username and password to said server
    - An ID number for a project on the server
    - An output directory where the results will be placed

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

import os
import sys

from io import BytesIO, StringIO
from zipfile import ZipFile as zf
import csv

from odk_requests import (forms, submissions, csv_submissions)

def project_forms(url, aut, pid):
    """Returns a list of all forms in an ODK project"""
    formsr = forms(url, aut, pid)
    formsl = formsr.json()
    print(f'There are {len(formsl)} forms in project {pid}.')
    return formsl

def project_submissions_zipped(url, aut, pid, formsl, outdir):
    """Downloads all of the submissions frm a given ODK Central project"""
    for form in formsl:
        form_id = form['xmlFormId']
        print(f'Checking submissions from {form_id}.')
        subs_zip = csv_submissions(url, aut, pid, form_id)
        
        outfilename = os.path.join(outdir, f'{form_id}.csv.zip')
        outfile = open(outfilename, 'wb')
        outfile.write(subs_zip.content)

def expand_geopoints(csv, geopoint_column_name):
    """
    Accepts a list representing a set of CSV ODK submissions and expands 
    a geopoint column to include lon, lat, ele, acc columns for easy 
    import into QGIS or direct conversion to GeoJSON or similar.
    """
    newcsv = []
    try:
        header_row = csv[0]
        column_num = header_row.index(geopoint_column_name)
        print(f'I found {geopoint_column_name} at index {column_num}')
        newheaderrow = header_row[:column_num + 1]
        newheaderrow.extend(['lat', 'lon', 'ele', 'acc'])
        newheaderrow.extend(header_row[column_num + 1:])
        newcsv.append(newheaderrow)
        for row in csv[1:]:
            split_geopoint = row[column_num].split()
            print(split_geopoint)
            if len(split_geopoint) == 4:
                newrow = row[:column_num + 1]
                newrow.extend(split_geopoint)
                newrow.extend(row[column_num + 1:])
            newcsv.append(newrow)
            
    except Exception as e:
        print("Is that the right geopoint column name?")
        print(e)

    return newcsv
    
    

def project_submissions_unzipped(url, aut, pid, formsl, outdir,
                                 collate, expand_geopoint):
    """Downloads and unzips all of the submissions from a given ODK project"""
    if collate:
        collated_outfilepath = os.path.join(outdir, f'_project_{pid}.csv')
        c_outfile = open(collated_outfilepath, 'w')
        cw = csv.writer(c_outfile)
        firstline = True
    for form in formsl:
        form_id = form['xmlFormId']
        print(f'Checking submissions from {form_id}.')
        subs_zip = csv_submissions(url, aut, pid, form_id)
        subs_bytes = BytesIO(subs_zip.content)
        subs_bytes.seek(0)
        subs_unzipped = zf(subs_bytes)
        sub_namelist = subs_unzipped.namelist()
        print(f'Files in submissions from {form_id}:')
        print(sub_namelist)
        for sub_name in sub_namelist:
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
                subs_num = len(subs_list)
                print(f'{sub_name} has {subs_num - 1} submissions')
                if subs_num > 1:
                    subs_to_write = subs_list
                    if expand_geopoint:
                        subs_to_write = expand_geopoints(subs_list,
                                                         expand_geopoint)
                    with open(outfilename, 'w') as outfile:
                        w = csv.writer(outfile)
                        w.writerows(subs_to_write)
                    if collate:
                        if firstline:
                            cw.writerows(subs_to_write)
                            firstline = False
                        else:
                            cw.writerows(subs_to_write[1:])

            else:
                with open(outfilename, 'wb') as outfile:
                    outfile.write(subs_bytes)

if __name__ == "__main__":
    """Downloads all of the submissions from a given ODK Central project"""
    # TODO Add Argparse and make the expand_geopoint function a parameter
    # that accepts and arbitrary column name to expand
    url = sys.argv[1]
    aut = (sys.argv[2], sys.argv[3])
    pid = sys.argv[4]
    outdir = sys.argv[5]
    collate = True
    expand_geopoint = 'all-xlocation'

    formsl = project_forms(url, aut, pid)
    subs = project_submissions_unzipped(url, aut, pid, formsl, outdir,
                                        collate, expand_geopoint)
    
