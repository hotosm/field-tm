#!/usr/bin/python3
"""

TODO: move this documentation to README.md
TODO: move functions that logically combine several requests to a new module

Utilities for interacting with ODK Central API

These are functions that return replies from an ODK Central server. https://docs.getodk.org/central-intro/

These functions mostly return requests.Response() objects. That object contains status code of the request (200, 404, etc), and the data itself, as well as a number of other attributes.

Here's a great reference on how to use the returned objects: https://www.w3schools.com/python/ref_requests_response.asp

The base_url parameter is just the URL of the ODK Central server. The extra characters needed to actually reach the API ('/v1/') are built into the functions.

The aut parameter is a tuple of the username and password used to authenticate the requester on the server, in the form (username, password). The passwords are in plain text; ideally this should be a hash but I haven't gotten around to that.

Simple usage:
If you want to see if a server is working and you are able to reach it, use the projects function:

url = 'https://3dphotocollect.org'
aut = ('myusername', 'mypassword')
r = fetch.projects(url, aut)
r.status_code

If all went well, that'll return '200'. If you got the username/password wrong (or aren't authorized on the server for whatever reason) it'll return '401', or '404' if the server isn't found at all.

To see the data:

r.json()

That'll return a JSON-formatted string with information about the projects on the server.

To see the information on a single project:

r.json()[0]

That'll return a dictionary with the attributes of the first project on the server.

To see the name of the first project:

r.json()[0]['name']

"""

import codecs
import json
import os
import sys
import zlib
# QR code stuff
from base64 import b64encode

import requests

import segno


def projects(base_url, aut):
    """Fetch a list of projects on an ODK Central server."""
    url = f"{base_url}/v1/projects"
    return requests.get(url, auth=aut)


def project(base_url, aut, pid):
    """Fetch details of a specific project on an ODK Central server"""
    url = f"{base_url}/v1/projects/{pid}"
    return requests.get(url, auth=aut)


def project_id(base_url, aut, projectName):
    """Fetch the id of a project based on the name on an ODK Central server."""
    url = f"{base_url}/v1/projects"
    projects = requests.get(url, auth=aut).json()
    pid = [p for p in projects if p["name"] == projectName][0]["id"]
    return pid


def forms(base_url, aut, pid):
    """Fetch a list of forms in a project."""
    url = f"{base_url}/v1/projects/{pid}/forms"
    return requests.get(url, auth=aut)


def form(base_url, aut, pid, formId):
    """Fetch a specific form in a project."""
    url = f"{base_url}/v1/projects/{pid}/forms/{formId}"
    return requests.get(url, auth=aut)


def form_attachments(base_url, aut, pid, formId):
    """Find out what attachments are expected by the form"""
    url = f"{base_url}/v1/projects/{pid}/forms/" f"{formId}/draft/attachments"
    # TODO: do (may not be necessary but fgood for safety)


def submissions(base_url, aut, pid, formId):
    """Fetch a list of submission instances for a given form."""
    url = f"{base_url}/v1/projects/{pid}/forms/{formId}/submissions"
    return requests.get(url, auth=aut)


def users(base_url, aut):
    """Fetch a list of users."""
    url = f"{base_url}/v1/users"
    return requests.get(url, auth=aut)


def app_users(base_url, aut, pid):
    """Fetch a list of app-users."""
    url = f"{base_url}/v1/projects/{pid}/app-users"
    return requests.get(url, auth=aut)


# Should work with ?media=false appended but doesn't.
# Probably a bug in ODK Central. Use the odata version; it works.
def csv_submissions(base_url, aut, pid, formId):
    """Fetch a CSV file of the submissions to a survey form."""
    url = f"{base_url}/v1/projects/{pid}/forms/{formId}/submissions.csv.zip"
    return requests.get(url, auth=aut)


def odata_submissions(base_url, aut, pid, formId):
    """
    Fetch the submissions using the odata api. 
    use submissions.json()['value'] to get a list of dicts, wherein 
    each dict is a single submission with the form question names as keys.
    """
    url = f"{base_url}/v1/projects/{pid}/forms/{formId}.svc/Submissions"
    submissions = requests.get(url, auth=aut)
    return submissions


def attachment_list(base_url, aut, pid, formId, instanceId):
    """Fetch an individual media file attachment."""
    url = (
        f"{base_url}/v1/projects/{pid}/forms/{formId}/submissions/"
        f"{instanceId}/attachments"
    )
    return requests.get(url, auth=aut)


def attachment(base_url, aut, pid, formId, instanceId, filename):
    """Fetch a specific attachment by filename from a submission to a form."""
    url = (
        f"{base_url}/v1/projects/{pid}/forms/{formId}/submissions/"
        f"{instanceId}/attachments/{filename}"
    )
    return requests.get(url, auth=aut)


def assignments_to_a_form(base_url, aut, pid, fid):
    """List the actors and assignments on a particular form."""
    url = f"{base_url}/v1/projects/{pid}/forms/{fid}/assignments"
    return requests.get(url, auth=aut)


def all_assignments(base_url, aut):
    url = f"{base_url}/v1/assignments"
    return requests.get(url, auth=aut)


def app_users(base_url, aut, pid):
    url = f"{base_url}/v1/projects/{pid}/app-users"
    return requests.get(url, auth=aut)


#################################################
# POST
#################################################


def create_project(base_url, aut, project_name):
    """Create a new project on an ODK Central server"""
    # TODO definitely should complain if project
    # already exists. Currently it just creates
    # another with the same name but a different
    # project ID.
    url = f"{base_url}/v1/projects"
    return requests.post(url, auth=aut, json={"name": project_name})


def create_app_user(base_url, aut, pid, app_user_name="Surveyor"):
    """
    Create a new project on an ODK Central server

    Atm. you can create multiple app users with the same name, 
    this should probably be illegal? 
    """
    url = f"{base_url}/v1/projects/{pid}/app-users"
    return requests.post(url, auth=aut, json={"displayName": app_user_name})


def update_role_app_user(base_url, aut, pid, fid, actorId, roleId=2):
    """Give specified app-user specified role for given project"""
    url = f"{base_url}/v1/projects/{pid}/forms/{fid}/" f"assignments/{roleId}/{actorId}"
    return requests.post(url, auth=aut)


def create_form(base_url, aut, pid, name, form):
    """Create a new form on an ODK Central server
    Does not publish the form because we may need to
    add attachments, so it must be published later."""
    basename = os.path.splitext(os.path.basename(form))[0]
    headers = {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"X-XlsForm-FormId-Fallback": name,
    }
    url = f"{base_url}/v1/projects/{pid}/forms" f"?ignoreWarnings=true&publish=false"
    return requests.post(url, auth=aut, data=form, headers=headers)


def attach_to_form(base_url, aut, pid, fid, name, att):
    """
    """
    basename = os.path.basename(name)
    # TODO it might not always be geojson!
    # Take the application type as a parameter.
    headers = {"Content-Type": "application/vnd.geo+json"}
    url = f"{base_url}/v1/projects/{pid}/forms/" f"{fid}/draft/attachments/{basename}"

    return requests.post(url, auth=aut, data=att, headers=headers)


def publish_form(base_url, aut, pid, fid):
    """Publish a form thats in draft state on server
    """

    url = f"{base_url}/v1/projects/{pid}/forms/" f"{fid}/draft/publish?version=yeahgo"
    return requests.post(url, auth=aut)


def qr_code(base_url, aut, pid, pname, form, token, outdir):
    """
    Based on the info at 
    https://docs.getodk.org/collect-import-export/
    """
    settings = {
        "general": {
            "server_url": f"{base_url}/v1/key/{token}/projects/{pid}",
            "form_update_mode": "match_exactly",
            "basemap_source": "mapbox",
            "autosend": "wifi_and_cellular",
        },
        "project": {"name": f"{pname}"},
        "admin": {},
    }

    qr_data = b64encode(zlib.compress(json.dumps(settings).encode("utf-8")))
    code = segno.make(qr_data, micro=False)
    outpath = os.path.join(outdir, form)
    code.save(f"{outpath}.png", scale=5)


def delete_project(base_url, aut, pid):
    """Permanently delete project from an ODK Central server. Probably don't."""
    url = f"{base_url}/v1/projects/{pid}"
    return requests.delete(url, auth=aut)


###########################################

if __name__ == "__main__":
    # For now it is a library for other modules to use
    pass
