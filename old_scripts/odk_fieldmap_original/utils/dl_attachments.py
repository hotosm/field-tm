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

"""

import os
import sys

from odk_requests import (forms, submissions, csv_submissions)

def project_forms(url, aut, pid):
    """Returns a list of all forms in an ODK project"""
    formsr = forms(url, aut, pid)
    formsl = formsr.json()
    print(f'There are {len(formsl)} forms in project {pid}.')
    return formsl

def project_submissions(url, aut, pid, formsl, outdir):
    """Downloads all of the submissions frm a given ODK Central project"""
    for form in formsl:
        form_id = (form['xmlFormId'])
        print(f'Checking submissions from {form_id}.')
        subs_zip = csv_submissions(url, aut, pid, form_id)
        outfilename = os.path.join(outdir, f'{form_id}.csv.zip')
        outfile = open(outfilename, 'wb')
        outfile.write(subs_zip.content)

if __name__ == "__main__":
    """Downloads all of the submissions from a given ODK Central project"""
    url = sys.argv[1]
    aut = (sys.argv[2], sys.argv[3])
    pid = sys.argv[4]
    outdir = sys.argv[5]
    
    formsl = project_forms(url, aut, pid)
    subs = project_submissions(url, aut, pid, formsl, outdir)
    
