#!/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
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

# The origins of this file was called odk_request.py, and gave me the
# idea to do a much enhanced version. Contributors to the original are:
# Author: hcwinsemius <h.c.winsemius@gmail.com>
# Author: Ivan Gayton <ivangayton@gmail.com>
# Author: Reetta Valimaki <reetta.valimaki8@gmail.com>


import logging
import epdb
import argparse
import sys, os
import requests
from requests.auth import HTTPBasicAuth
import json
import zlib
import codecs
import urllib
from datetime import tzinfo, datetime
import qrcode
from base64 import b64encode
import codecs
import segno
import zlib


class OdkCentral(object):
    def __init__(self, url=None, user=None, passwd=None):
        """A Class for accessing an ODK Central server via it's REST API"""
        self.url = url
        self.user = user
        self.passwd = passwd
        # These are settings used by ODK Collect
        self.general = {
            "form_update_mode": "match_exactly",
            "autosend": "wifi_and_cellular",
        }
        # If their is a config file with authentication setting, use that
        # so we don't have to supply this all the time.
        home = os.getenv("HOME")
        config = ".odkcentral"
        filespec = home + "/" + config
        if os.path.exists(filespec):
            file = open(filespec, "r")
            for line in file:
                # Support embedded comments
                if line[0] == "#":
                    continue
                # Read the config file for authentication settings
                tmp = line.split("=")
                if tmp[0] == "url":
                    self.url = tmp[1].strip ('\n')
                if tmp[0] == "user":
                    self.user = tmp[1].strip ('\n')
                if tmp[0] == "passwd":
                    self.passwd = tmp[1].strip ('\n')
        else:
            logging.warning("You can put authentication settings in %s" % filespec)
        # Base URL for the REST API
        self.version = "v1"
        self.base = self.url + "/" + self.version + "/"

        # Authentication data
        self.auth = HTTPBasicAuth(self.user, self.passwd)

        # Use a persistant connect, better for multiple requests
        self.session = requests.Session()

        # These are just cached data from the queries
        self.projects = dict()
        self.users = None

    def authenticate(self, url=None, user=None, passwd=None):
        """Setup authenticate to an ODK Central server"""
        if not self.url:
            self.url = url
        if not self.user:
            self.user = user
        if not self.passwd:
            self.passwd = passwd
        # Enable persistent connection, create a cookie for this session
        self.session.headers.update({'accept': 'odkcentral'})

        # Connect to the server
        return self.session.get(self.url, auth=self.auth)

    def listProjects(self):
        """Fetch a list of projects from an ODK Central server, and
        store it as an indexed list."""
        logging.info("Getting a list of projects from %s" % self.url)
        url = self.base + "projects"
        result = self.session.get(url, auth=self.auth)
        projects = result.json()
        for project in projects:
            self.projects[project['id']] = project
        return projects

    def createProject(name=None):
        """Create a new project on an ODK Central server"""
        url = f'{self.base}/v1/projects'
        result = self.session.post(url, auth=self.auth, json={'name': name})

    def listUsers(self):
        """Fetch a list of users on the ODK Central server"""
        logging.info("Getting a list of users from %s" % self.url)
        url = self.base + "users"
        result = self.session.get(url, auth=self.auth)
        self.users = result.json()
        return self.users
        
    def dump(self):
        """Dump internal data structures, for debugging purposes only"""
        # print("URL: %s" % self.url)
        # print("User: %s" % self.user)
        # print("Passwd: %s" % self.passwd)
        print("REST URL: %s" % self.base)
        print("There are %d projects on this server" % len(self.projects))
        for id, data in self.projects.items():
            print("\t %s: %s" % (id, data['name']))
        if self.users:
            print("There are %d users on this server" % len(self.users))
            for data in self.users:
                print("\t %s: %s" % (data['id'], data['email']))
        else:
            print("There are no users on this server")


class OdkProject(OdkCentral):
    """Class to manipulate a project on an ODK Central server"""
    def __init__(self, session=None):
        super().__init__()
        self.forms = None
        self.submissions = None
        self.data = None
        self.appusers = None

    def getData(self, keyword):
        return self.data[keyword]

    def listForms(self, id=None):
        """Fetch a list of forms in a project on an ODK Central server."""
        url = f'{self.base}projects/{id}/forms'
        result = self.session.get(url, auth=self.auth)
        self.forms = result.json()
        return self.forms

    def listAppUsers(self, projectId=None):
        """Fetch a list of app users for a project on an ODK Central server."""
        url = f'{self.base}projects/{projectId}/app-users'
        result = self.session.get(url, auth=self.auth)
        self.appusers = result.json()
        return self.appusers

    def listAssignments(self, projectId=None):
        """List the Role & Actor assignments for users on a project"""
        url = f'{self.base}projects/{projectId}/assignments'
        result = self.session.get(url, auth=self.auth)
        return result.json()

    def getDetails(self, projectId=None):
        """Get all the details for a project on an ODK Central server"""
        url = f'{self.base}projects/{projectId}'
        result = self.session.get(url, auth=self.auth)
        self.data = result.json()
        return self.data

    def dump(self):
        """Dump internal data structures, for debugging purposes only"""
        super().dump()
        print("There are %d forms in this project" % len(self.forms))
        if self.data:
            print("Project ID: %s" % self.data['id'])
        for data in self.forms:
            print("\t %s(%s): %s" % (data['xmlFormId'], data['version'], data['name']))
        print("There are %d submissions in this project" % len(self.submissions))
        for data in self.submissions:
            print("\t%s: %s" % (data['instanceId'], data['createdAt']))
        print("There are %d app users in this project" % len(self.appusers))
        for data in self.appusers:
            print("\t%s: %s" % (data['id'], data['displayName']))

class OdkForm(OdkCentral):
    """Class to manipulate a from on an ODK Central server"""
    def __init__(self, session=None):
        super().__init__()
        self.name = None
        # Draft is for a form that isn't published yet
        self.draft = True
        # this is only populated if self.getDetails() is called first.
        self.data = dict()
        self.attach = list()
        self.publish = True
        self.media = list()
        self.xml = None
        self.submissions = list()
        self.appusers = dict()
        # self.xmlFormId = None
        # self.projectId = None

    def getName(self):
        """Extract the name from a form on an ODK Central server"""
        if 'name' in self.data:
            return self.data['name']
        else:
            logging.warning("Execute OdkForm.getDetails() to get this data.")

    def getFormId(self):
        """Extract the xmlFormId from a form on an ODK Central server"""
        if 'xmlFormId' in self.data:
            return self.data['xmlFormId']
        else:
            logging.warning("Execute OdkForm.getDetails() to get this data.")

    def getDetails(self, projectId=None, xmlFormId=None):
        """Get all the details for a form on an ODK Central server"""
        url = f'{self.base}projects/{projectId}/forms/{xmlFormId}'
        result = self.session.get(url, auth=self.auth)
        self.data = result.json()
        return result

    def listSubmissions(self, projectId, formId):
        """Fetch a list of submission instances for a given form."""
        url = f'{self.base}projects/{projectId}/forms/{formId}/submissions'
        result = self.session.get(url, auth=self.auth)
        self.submissions = result.json()
        return self.submissions

    def listAssignments(self, projectId=None, xmlFormId=None):
        """List the Role & Actor assignments for users on a project"""
        url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/assignments'
        result = self.session.get(url, auth=self.auth)
        return result.json()

    def getSubmission(self, projectId=None, formId=None, disk=False):
        """Fetch a CSV file of the submissions without media to a survey form."""
        instanceId = "uuid:47bda2ec-c282-4cb7-9f37-03dc3bbdf96b: 2022-09-02T17:09:19.648Z"
        url = self.base + f'projects/{projectId}/forms/{formId}/submissions'
        result = self.session.get(url, auth=self.auth)
        if result.status_code == 200:
            if disk:
                now = datetime.now()
                timestamp = f'{now.year}_{now.hour}_{now.minute}'
                # id = self.forms[0]['xmlFormId']
                filespec = f'{formId}_{timestamp}.csv'
                try:
                    file = open(filespec, "xb")
                    file.write(result.content)
                except FileExistsError:
                    file = open(filespec, "wb")
                    file.write(result.content)
                logging.info("Wrote CSV file %s" % filespec)
                file.close()
            return result.content
        else:
            logging.error(f'Submissions for {projectId}, Form {formId}' + "doesn't exist")
            return None

    def getSubmissionMedia(self, projectId, formId):
        """Fetch a ZIP file of the submissions with media to a survey form."""
        url = self.base + f'projects/{projectId}/forms/{formId}/submissions.csv.zip'
        result = self.session.get(url, auth=self.auth)
        return result

    def addMedia(self, media=None, filespec=None):
        """Add a data file to this form"""
        # FIXME: this also needs the data
        self.media[filespec] = media

    def addXMLForm(self, projectId=None, xmlFormId=None, xform=None):
        """Add an XML file to this form"""
        self.xml = xform

    def listMedia(self, projectId=None, xmlFormId=None):
        """List all the attchements for this form"""
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft/attachments'
        else:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/attachments'
        result = self.session.get(url, auth=self.auth)
        self.media = result.json()
        return self.media

    def uploadMedia(self, projectId=None, xmlFormId=None, filespec=None):
        """Upload an attachement to the ODK Central server"""
        file = os.path.basename(filespec)
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft/attachments/{file}'
        else:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/attachments/{file}'

        headers = { 'Content-Type': '*/*' }
        file = open(filespec, "rb")
        media = file.read()
        file.close()
        result = self.session.post(url, auth=self.auth, data=media, headers=headers)
        return result
        
    def getMedia(self, projectId=None, xmlFormId=None, filename=None):
        """Fetch a specific attachment by filename from a submission to a form."""
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft/attachments/{filename}'
        else:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/attachments/{filename}'
        result = self.session.get(url, auth=self.auth)
        self.media = result.content
        return self.media

    def createForm(self, projectId=None, xmlFormId=None, filespec=None, draft=None):
        """Create a new form on an ODK Central server"""
        if draft is not None:
            self.draft = draft
        # headers = {
        #    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        #    f'X-XlsForm-FormId-Fallback': filespec
        # }
        headers = { 'Content-Type': 'application/xml' }
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft?ignoreWarnings=true'
        else:
            url = f'{self.base}projects/{projectId}/forms?ignoreWarnings=true&publish=true'

        # Read the XML or XLS file
        file = open(filespec, "rb")
        xml = file.read()
        file.close()
        logging.info("Read %d bytes from %s" % (len(xml), filespec))

        result = self.session.post(url, auth=self.auth,  data=xml, headers=headers)
        # epdb.st()
        # FIXME: should update self.forms with the new form
        return result

    def deleteForm(self, projectId=None, xmlFormId=None):
        """Delete a form from an ODK Central server"""
        # FIXME: If your goal is to prevent it from showing up on survey clients like ODK Collect, consider
        # setting its state to closing or closed
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft'
        else:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}'
        print(url)
        result = self.session.delete(url, auth=self.auth)
        return result

    def publishForm(self, projectId=None, xmlFormId=None):
        """Publish a draft form. When creating a form that isn't a draft, it can get publised then"""
        version = "newversion"
        if self.draft:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft/publish?version={version}'
            # url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/draft/publish'
        else:
            url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/publish?version={version}'
            # url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/publish'
        result = self.session.get(url, auth=self.auth)
        return result

    def dump(self):
        """Dump internal data structures, for debugging purposes only"""
        # super().dump()
        entries = len(self.media)
        print("Form has %d attachements" % entries)
        for form in self.media:
            if 'name' in form:
                print("Name: %s" % form['name'])


class OdkAppUser(OdkCentral):
    def __init__(self):
        """A Class for app user data"""
        super().__init__()
        self.user = None
        self.qrcode = None
        self.id = None

    def create(self, projectId=None, name=None):
        """Create a new app-user for a form"""
        url = f'{self.base}projects/{projectId}/app-users'
        result = self.session.post(url, auth=self.auth, json={'displayName': name})
        self.user = name
        return result

    def delete(self, projectId=None, userId=None):
        """Create a new app-user for a form"""
        url = f'{self.base}projects/{projectId}/app-users/{userId}'
        result = self.session.delete(url, auth=self.auth)
        return result

    def updateRole(self, projectId=None, xmlFormId=None, roleId=2, actorId=None):
        """Update the role of an app user for a form"""
        logging.info("Update access to XForm %s for %s" % (xmlFormId, actorId))
        url = f'{self.base}projects/{projectId}/forms/{xmlFormId}/assignments/{roleId}/{actorId}'
        result = self.session.post(url, auth=self.auth)
        return result

    def grantAccess(self, projectId=None, roleId=2, userId=None, xmlFormId=None, actorId=None):
        """Grant access to an app user for a form"""
        kwargs = { "formId": xmlFormId, "actorId": userId, }
        url = f'{self.base}projects/{projectId}/forms/{formId}/assignments/{roleId}/{actorId}'
        result = self.session.post(url, auth=self.auth)
        return result

    def getQRCode(self, projectId=None, token=None, name=None):
        """Get the QR Code for an app-user"""
        url = f'{self.base}key/{token}/projects/{projectId}'
        logging.info("Generating QR Code for app-user \"%s\" for project %s" % (name, projectId))
        self.settings = {"general":
                    {"server_url":f'{self.base}key/{token}/projects/{projectId}',
                     "form_update_mode":"manual",
                     "basemap_source": "OpenStreetMap",
                     "autosend":"wifi_and_cellular"},
                    "project":{"name":f'{name}'},
                    "admin":{}
                    }
        qr_data = (b64encode(zlib.compress(json.dumps(self.settings).encode("utf-8"))))
        self.qrcode = segno.make(qr_data, micro=False)
        self.qrcode.save(f'{name}.png', scale=5)

# This following code is only for debugging purposes, since this is easier
# to use a debugger with instead of pytest.
if __name__ == '__main__':
    # Enable logging to the terminal by default
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Gotta start somewhere...
    project = OdkProject()
    # Start the persistent HTTPS connection to the ODK Central server
    project.authenticate()
    # Get a list of all the projects on this ODK Central server
    project.listProjects()
    # List all the users on this ODK Central server
    project.listUsers()
    # List all the forms for this project. FIXME: don't hardcode the project ID
    project.listForms(4)
    # List all the app users for this project. FIXME: don't hardcode the project ID
    project.listAppUsers(4)
    # List all the submissions for this project. FIXME: don't hardcode the project ID ad form name
    # project.listSubmissions(4, "cemeteries")
    # project.getSubmission(4, "cemeteries")
    # Dump all the internal data
    project.dump()

    # Form management
    form = OdkForm()
    form.authenticate()
    x = form.getDetails(4, 'cemeteries')
    # print(x.json())
    # x = form.listMedia(4, "waterpoints", 'uuid:fbe3ef41-6298-40c1-a694-6c9d25a8c476')
    # Make a new form
    # xml = "/home/rob/projects/HOT/odkconvert.git/XForms/cemeteries.xml"
    # form.addXMLForm(xml)
    # csv1 = "/home/rob/projects/HOT/odkconvert.git/XForms/municipality.csv"
    # csv2 = "/home/rob/projects/HOT/odkconvert.git/XForms/towns.csv"
    # form.addMedia(csv1)
    # form.addMedia(csv2)
    x = form.createForm(4, 'cemeteries', "cemeteries.xls", True)
    print(x.json())
    # x = form.publish(4, 'cemeteries', "cemeteries.xls")
    print(x.json())
    x = form.uploadMedia(4, 'cemeteries', "towns.csv")
    print(x.json())
    x = form.uploadMedia(4, 'cemeteries', "municipality.csv")
    print(x.json())
    x = form.listMedia(4, 'cemeteries')
    print(x.json())
    form.dump()
