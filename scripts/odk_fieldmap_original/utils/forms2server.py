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
    Accepts
    - A directory with subdirectories full of:
      - GeoJSON files representing tasks
      - XLSForms corresponding to them
    - A base URL for an ODK Central server
    - A tuple of username and password to said server
    And creates an ODK Central project.
    Project name will be the directory name.

"""

import os
import sys

from odk_requests import (
    app_users,
    attach_to_form,
    create_app_user,
    create_form,
    forms,
    create_project,
    project_id,
    publish_form,
    qr_code,
    update_role_app_user,
)


def get_formlist(indir):
    """
    Converts a directory full of xlsform files into
    a list of form names without the file extension.
    i.e. Dakar_buildings_213.xlsx =-> Dakar_buildings_213

    N.B. Operates on a subdirectory of the input directory
    named '/forms'
    """
    formdir = os.path.join(indir, "forms")
    filelist = os.listdir(formdir)
    forms = [
        os.path.splitext(x)[0]
        for x in filelist
        if os.path.splitext(x)[1].lower() == ".xlsx"
    ]
    return forms


# TODO use formlist instead of traversing directory
def formdir2project(url, aut, indir):
    """
    Accepts
    - A directory full of:
      - GeoJSON files representing tasks
      - XLSForms corresponding to them
    - A base URL for an ODK Central server
    - A tuple of username and password to said server
    And creates an ODK Central project.
    Project name will be the directory name.
    """

    name = os.path.basename(indir.rstrip(os.path.sep))
    print(f"Creating a project called {name}.\n")
    # TODO: first check that project does not exist
    # Create it

    from time import sleep

    sleep(2)

    create_project(url, aut, name)
    # Need its numerical id for future operations
    pid = project_id(url, aut, name)
    print(f"The new project ID is {pid}./n")
    return pid


# TODO use formlist instead of traversing directory
def push_forms(url, aut, pid, indir):
    """
    Push all of the forms in the subdirectory forms
    of the input directory up to the ODK Central server.
    """
    formdir = os.path.join(indir, "forms")

    # Traverse the directory of xlsforms
    filelist = os.listdir(formdir)
    # keep only the files that are xlsx
    # TODO: Maybe reject all non-point input files
    forms = [
        os.path.splitext(x)[0]
        for x in filelist
        if os.path.splitext(x)[1].lower() == ".xlsx"
    ]
    print(f"I found {len(forms)} forms to upload")
    for form in forms:
        print(f"Uploading form {form}.")
        formpath = os.path.join(formdir, f"{form}.xlsx")
        formfile = open(formpath, "rb")
        formdata = formfile.read()
        rf = create_form(url, aut, pid, form, formdata)
        print(rf)
    return "schplonk"


# TODO use formlist instead of traversing the directory
def push_geojson(url, aut, pid, indir):
    """
    Push all of the geojson attachments to their
    corresponsing forms on the ODK Central server.
    The geojson files are expected to be in the
    geojson subdirectory of the input directory.
    """
    # TODO loop over the forms instead of the
    # files in the geojson directory.
    # Not hugely important but more consistent.
    gjdir = os.path.join(indir, "geojson")
    filelist = os.listdir(gjdir)
    attments = [x for x in filelist if os.path.splitext(
        x)[1].lower() == ".geojson"]
    for attment in attments:
        attname = os.path.splitext(os.path.basename(attment))[0]
        print(f"Attaching {attment}.")
        attpath = os.path.join(gjdir, attment)
        attfile = open(attpath, "rb")
        attdata = attfile.read()

        rg = attach_to_form(url, aut, pid, attname, attment, attdata)
        print(rg)
    return "yo"


def publish_forms(url, aut, pid, forms):
    """Iterate through and publish forms.
    """
    for form in forms:
        r = publish_form(url, aut, pid, form)
        print(r)
    return "Holy crap that worked the first try!"


def create_app_users(url, aut, pid, forms):
    """
    Create app users with access to the appropriate
    forms. Each app users will share a name with their
    sole allocated form.
    """
    for name in forms:
        print(f"Creating app user {name}")
        r = create_app_user(url, aut, pid, name)
        print(r)

    return "I guess that might have worked"


def assign_app_users_to_forms(url, aut, pid, forms):
    # First find the goddamned actorIds for the app users
    appusers_r = app_users(url, aut, pid)
    appusers = {}
    for appuser in appusers_r.json():
        displayName = appuser["displayName"]
        appuserid = appuser["id"]
        appusers[displayName] = appuserid
    print("\nShould have the app users in a dict now\n")
    print(appusers)
    for form in forms:
        actorid = appusers[form]
        print(f"Assigning form {form} to actor {actorid}.")
        r = update_role_app_user(url, aut, pid, form, actorid, 2)
        print(r)


def fetch_qr_codes(url, aut, pid, forms, indir):
    pname = os.path.basename(indir.rstrip(os.path.sep))
    qrdir = os.path.join(indir, "QR_codes")
    if not os.path.exists(qrdir):
        os.makedirs(qrdir)
    # TODO create dir if not already there
    appusers_r = app_users(url, aut, pid)
    appusertokens = {}
    for appuser in appusers_r.json():
        displayName = appuser["displayName"]
        usertoken = appuser["token"]
        appusertokens[displayName] = usertoken
    # print(appusertokens)
    for form in forms:
        token = appusertokens[form]
        print(f"Trying to create qr code for {form} with {token}.")
        r = qr_code(url, aut, pid, pname, form, token, qrdir)
        print(r)


if __name__ == "__main__":
    """

    """
    indir = sys.argv[1]
    url = sys.argv[2]
    aut = (sys.argv[3], sys.argv[4])

    print("\nHere goes nothing.\n")
    formlist = get_formlist(indir)
    # print(f'{formlist}\n')

    pid = formdir2project(url, aut, indir)
    print(f"We have a project with id {pid}\n.")

    yabbity = push_forms(url, aut, pid, indir)
    print(yabbity)

    blimey = push_geojson(url, aut, pid, indir)
    print(blimey)

    publish = publish_forms(url, aut, pid, formlist)
    print(publish)
    appusers = create_app_users(url, aut, pid, formlist)

    ass = assign_app_users_to_forms(url, aut, pid, formlist)
    print(ass)

    codies = fetch_qr_codes(url, aut, pid, formlist, indir)
