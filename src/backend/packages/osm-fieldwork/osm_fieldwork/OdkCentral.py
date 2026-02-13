# Copyright (c) Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     OSM-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

# The origins of this file was called odk_request.py, and gave me the
# idea to do a much enhanced version. Contributors to the original are:
# Author: hcwinsemius <h.c.winsemius@gmail.com>
# Author: Ivan Gayton <ivangayton@gmail.com>
# Author: Reetta Valimaki <reetta.valimaki8@gmail.com>

# NOTE while there is some unique functionality in this module not available
# NOTE in getodk/pyodk, for most use cases it would be recommended to use
# NOTE pyodk instead.
#
# NOTE If async functionality is required, then OdkCentralAsync is available,
# NOTE as pyodk does not support async workflows.

import json
import logging
import os
import zlib
from base64 import b64encode
from datetime import datetime
from xml.etree import ElementTree
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import requests
import segno

log_level = os.getenv("LOG_LEVEL", default="INFO")
# Set log level for urllib
logging.getLogger("urllib3").setLevel(log_level)

log = logging.getLogger(__name__)


def _pyodk_replacement_stub(legacy_method: str, replacement: str):
    """Raise a clear migration error for APIs replaced by pyodk."""
    raise NotImplementedError(
        f"`{legacy_method}` has been removed from osm-fieldwork. "
        f"Use pyodk instead: {replacement}"
    )


class OdkCentral:
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """A Class for accessing an ODK Central server via it's REST API.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (OdkCentral): An instance of this class
        """
        if not url:
            url = os.getenv("ODK_CENTRAL_URL", default=None)
        self.url = url
        if not user:
            user = os.getenv("ODK_CENTRAL_USER", default=None)
        self.user = user
        if not passwd:
            passwd = os.getenv("ODK_CENTRAL_PASSWD", default=None)
        self.passwd = passwd
        verify = os.getenv("ODK_CENTRAL_SECURE", default=True)
        if type(verify) == str:
            self.verify = verify.lower() in ("true", "1", "t")
        else:
            self.verify = verify
        # Set cert bundle path for requests in environment
        if self.verify:
            os.environ["REQUESTS_CA_BUNDLE"] = "/etc/ssl/certs/ca-certificates.crt"
        # These are settings used by ODK Collect
        self.general = {
            "form_update_mode": "match_exactly",
            "autosend": "wifi_and_cellular",
        }
        # If there is a config file with authentication setting, use that
        # so we don't have to supply this all the time. This is only used
        # when odk_client is used, and no parameters are passed in.
        if not self.url:
            # log.debug("Configuring ODKCentral from file .odkcentral")
            home = os.getenv("HOME")
            config = ".odkcentral"
            filespec = home + "/" + config
            if os.path.exists(filespec):
                file = open(filespec)
                for line in file:
                    # Support embedded comments
                    if line[0] == "#":
                        continue
                    # Read the config file for authentication settings
                    tmp = line.split("=")
                    if tmp[0] == "url":
                        self.url = tmp[1].strip("\n")
                    if tmp[0] == "user":
                        self.user = tmp[1].strip("\n")
                    if tmp[0] == "passwd":
                        self.passwd = tmp[1].strip("\n")
            else:
                log.warning(f"Authentication settings missing from {filespec}")
        else:
            log.debug(f"ODKCentral configuration parsed: {self.url}")
        # Base URL for the REST API
        self.version = "v1"
        # log.debug(f"Using {self.version} API")
        self.base = self.url + "/" + self.version + "/"

        # Use a persistent connect, better for multiple requests
        self.session = requests.Session()

        # Hook into the session's request method to log the URL that is called
        original_request = self.session.request
        def logging_request(method, url, *args, **kwargs):
            log.debug(f"ODKCentral request: {method.upper()} {url}")
            return original_request(method, url, *args, **kwargs)
        self.session.request = logging_request

        # Authentication with session token
        self.authenticate()

        # These are just cached data from the queries
        self.projects = dict()
        self.users = list()

    def authenticate(
        self,
        url: str = None,
        user: str = None,
        passwd: str = None,
    ):
        """Setup authenticate to an ODK Central server.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (requests.Response): A response from ODK Central after auth
        """
        if not self.url:
            self.url = url
        if not self.user:
            self.user = user
        if not self.passwd:
            self.passwd = passwd

        # Get a session token
        try:
            response = self.session.post(
                f"{self.base}sessions",
                json={
                    "email": self.user,
                    "password": self.passwd,
                },
            )
        except requests.exceptions.ConnectionError as request_error:
            # URL does not exist
            raise ConnectionError("Failed to connect to Central. Is the URL valid?") from request_error

        if response.status_code == 401:
            # Unauthorized, invalid credentials
            raise ConnectionError("ODK credentials are invalid, or may have changed. Please update them.") from None
        elif not response.ok:
            # Handle other errors
            response.raise_for_status()

        self.session.headers.update({"Authorization": f"Bearer {response.json().get('token')}"})

        # Connect to the server
        return self.session.get(self.url, verify=self.verify)

    def listProjects(self):
        """Fetch a list of projects from an ODK Central server, and
        store it as an indexed list.

        Returns:
            (list): A list of projects on a ODK Central server
        """
        return _pyodk_replacement_stub(
            "OdkCentral.listProjects",
            "Client(...).projects.list()",
        )

    def findProject(
        self,
        name: str = None,
        project_id: int = None,
    ):
        """Get the project data from Central.

        Args:
            name (str): The name of the project

        Returns:
            (dict): the project data from ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkCentral.findProject",
            "Client(...).projects.list()/projects.get() and filter in caller",
        )

    def createProject(
        self,
        name: str,
    ) -> dict:
        """Create a new project on an ODK Central server if it doesn't
        already exist.

        Args:
            name (str): The name for the new project

        Returns:
            (json): The response from ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkCentral.createProject",
            "Client(...).session.post(f'{client.session.base_url}/v1/projects', json={'name': ...})",
        )

    def deleteProject(
        self,
        project_id: int,
    ):
        """Delete a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central

        Returns:
            (str): The project name
        """
        return _pyodk_replacement_stub(
            "OdkCentral.deleteProject",
            "Client(...).session.delete(f'{client.session.base_url}/v1/projects/{project_id}')",
        )


class OdkProject(OdkCentral):
    """Class to manipulate a project on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkProject): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.forms = list()
        self.submissions = list()
        self.data = None
        self.appusers = None
        self.id = None

    def listForms(self, project_id: int, metadata: bool = False):
        """Fetch a list of forms in a project on an ODK Central server.

        Args:
            project_id (int): The ID of the project on ODK Central

        Returns:
            (list): The list of XForms in this project
        """
        return _pyodk_replacement_stub(
            "OdkProject.listForms",
            "Client(...).forms.list(project_id=...)",
        )

    def listAppUsers(
        self,
        projectId: int,
    ):
        """Fetch a list of app users for a project from an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (list): A list of app-users on ODK Central for this project
        """
        return _pyodk_replacement_stub(
            "OdkProject.listAppUsers",
            "ProjectAppUserService(session=client.session, default_project_id=...).list()",
        )

    def getDetails(
        self,
        projectId: int,
    ):
        """Get all the details for a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (json): Get the data about a project on ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkProject.getDetails",
            "Client(...).projects.get(project_id=...)",
        )

    def getFullDetails(
        self,
        projectId: int,
    ):
        """Get extended details for a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (json): Get the data about a project on ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkProject.getFullDetails",
            "Client(...).projects.get(project_id=...)",
        )

    def updateReviewState(self, projectId: int, xmlFormId: str, instanceId: str, review_state: dict) -> dict:
        """Updates the review state of a submission in ODK Central.

        Args:
            projectId (int): The ID of the odk project.
            xmlFormId (str): The ID of the form.
            instanceId (str): The ID of the submission instance.
            review_state (dict): The updated review state.
        """
        return _pyodk_replacement_stub(
            "OdkProject.updateReviewState",
            "Client(...).submissions.review(...) / submissions.edit(...)",
        )


class OdkForm(OdkCentral):
    """Class to manipulate a form on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkForm): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.name = None
        # Draft is for a form that isn't published yet
        self.draft = False
        self.published = False
        # this is only populated if self.getDetails() is called first.
        self.data = {}
        self.attach = []
        self.media = {}
        self.xml = None
        self.submissions = []
        self.appusers = {}

    def getDetails(
        self,
        projectId: int,
        xform: str,
    ) -> dict:
        """Get all the details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        return _pyodk_replacement_stub(
            "OdkForm.getDetails",
            "Client(...).forms.get(form_id=..., project_id=...)",
        )

    def getFullDetails(
        self,
        projectId: int,
        xform: str,
    ):
        """Get the full details for a form on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The data for this XForm
        """
        return _pyodk_replacement_stub(
            "OdkForm.getFullDetails",
            "Client(...).forms.get(form_id=..., project_id=...)",
        )

    def getXml(
        self,
        projectId: int,
        xform: str,
    ):
        """Get the form XML from the ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central.
            xform (str): The XForm to get the details of from ODK Central.

        Returns:
            (str): The raw XML form.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}.xml"
        result = self.session.get(url, verify=self.verify)

        if result.status_code != 200:
            result.raise_for_status()

        return result.text

    def listSubmissions(self, projectId: int, xform: str, filters: dict = None):
        """Fetch a list of submission instances for a given form.

        Returns data in format:

        {
            "value":[],
            "@odata.context": "URL/v1/projects/52/forms/103.svc/$metadata#Submissions",
            "@odata.count":0
        }

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (json): The JSON of Submissions.
        """
        return _pyodk_replacement_stub(
            "OdkForm.listSubmissions",
            "Client(...).submissions.list(project_id=..., form_id=...)",
        )

    def getSubmissions(
        self,
        projectId: int,
        xform: str,
        submission_id: int,
        disk: bool = False,
        json: bool = True,
    ):
        """
        Fetch a JSON submission and recursively populate all @odata.navigationLink fields.
        Internal fields (__id, __Submissions-id) are removed from media items.
        
        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            submission_id (int): The ID of the submissions to download
            disk (bool): Whether to write the downloaded file to disk
            json (bool): Download JSON or CSV format

        Returns:
            dict: Cleaned submission JSON
        """
        now = datetime.now()
        timestamp = f"{now.year}_{now.hour}_{now.minute}"

        if json:
            url = self.base + f"projects/{projectId}/forms/{xform}.svc/Submissions"
            filespec = f"{xform}_{timestamp}.json"
        else:
            url = self.base + f"projects/{projectId}/forms/{xform}/submissions"
            filespec = f"{xform}_{timestamp}.csv"

        if submission_id:
            url += f"('{submission_id}')"

        # Fetch submission
        response = self.session.get(
            url,
            headers={**self.session.headers, "Content-Type": "application/json"},
            verify=self.verify,
        )
        if response.status_code != 200:
            log.error(f"Failed to fetch submission: {response.status_code}")
            return b""

        submission_json = response.json()

        # Save raw JSON if requested
        if disk:
            mode = "xb" if not os.path.exists(filespec) else "wb"
            with open(filespec, mode) as f:
                f.write(response.content)

        def strip_internal_fields(node):
            """
            Recursively strip internal fields ("__id", "__Submissions-id") from a node.

            Args:
                node (dict or list): The node to strip internal fields from.

            Returns:
                dict or list: The node with internal fields stripped.
            """
            if isinstance(node, dict):
                return {k: strip_internal_fields(v) for k, v in node.items() if k not in ("__id", "__Submissions-id")}
            if isinstance(node, list):
                return [strip_internal_fields(i) for i in node]
            return node

        # Recursive OData navigation resolver
        def resolve_links(node):
            """
            Recursively resolve OData navigation links in a node.

            Args:
                node (dict or list): The node to resolve navigation links from.

            Returns:
                dict or list: The node with navigation links resolved.
            """
            if isinstance(node, dict):
                resolved = {}
                for key, value in node.items():
                    # Handle navigation links
                    if key.endswith("@odata.navigationLink"):
                        field_name = key.replace("@odata.navigationLink", "")
                        link_url = f"{self.base}projects/{projectId}/forms/{xform}.svc/{value}"

                        resp = self.session.get(link_url, headers={"Accept": "application/json"}, verify=self.verify)
                        resp.raise_for_status()
                        linked_data = resp.json().get("value", resp.json())

                        # Strip internal fields and recurse
                        resolved[field_name] = resolve_links(strip_internal_fields(linked_data))
                    else:
                        # Regular field: recurse
                        resolved[key] = resolve_links(value)
                return resolved

            if isinstance(node, list):
                return [resolve_links(i) for i in node]

            return node

        # Resolve for single/multi submission formats
        if "value" in submission_json:
            submission_json["value"] = resolve_links(submission_json["value"])
        else:
            submission_json = resolve_links(submission_json)

        return submission_json


    def getSubmissionMedia(
        self,
        projectId: int,
        xform: str,
        filters: dict = {},
    ):
        """Fetch a ZIP file of the submissions with media to a survey form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list): The media file
        """
        url = self.base + f"projects/{projectId}/forms/{xform}/submissions.csv.zip"
        result = self.session.get(url, params=filters, verify=self.verify)
        return result

    def getSubmissionPhoto(
        self,
        projectId: int,
        instanceID: str,
        xform: str,
        filename: str,
    ):
        """Fetch a specific attachment by filename from a submission to a form.

        NOTE this function expects the user has not configured external S3 storage.
        NOTE if S3 storage is configured, the response does not contain the
        NOTE photo content, but instead an S3 pre-signed URL.
        NOTE see OdkCentralAsync.OdkForm.getSubmissionAttachmentUrl

        Args:
            projectId (int): The ID of the project on ODK Central
            instanceID(str): The ID of the submission on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            filename (str): The name of the attachment for the XForm on ODK Central

        Returns:
            (bytes): The media data
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions/{instanceID}/attachments/{filename}"
        result = self.session.get(url, verify=self.verify)
        if result.status_code == 200:
            log.debug(f"fetched {filename} from Central")
        else:
            status = result.json()
            log.error(f"Couldn't fetch {filename} from Central: {status['message']}")
        return result.content

    def validateMedia(self, filename: str) -> bool:
        """Validate the specified filename is present in the XForm."""
        if not self.xml:
            return False
        xform_filenames = []
        namespaces = {
            "h": "http://www.w3.org/1999/xhtml",
            "odk": "http://www.opendatakit.org/xforms",
            "xforms": "http://www.w3.org/2002/xforms",
        }

        root = ElementTree.fromstring(self.xml)
        instances = root.findall(".//xforms:model/xforms:instance[@src]", namespaces)

        for inst in instances:
            src_value = inst.attrib.get("src", "")
            if src_value.startswith("jr://"):
                src_value = src_value[len("jr://") :]  # Remove jr:// prefix
            if src_value.startswith("file/"):
                src_value = src_value[len("file/") :]  # Remove file/ prefix
            xform_filenames.append(src_value)

        if filename not in xform_filenames:
            msg = f"Filename ({filename}) is not present in XForm media: {xform_filenames}"
            log.error(msg)
            raise ValueError(msg)

        return True

    def uploadMedia(
        self,
        projectId: int,
        form_name: str,
        data: Union[str, Path, BytesIO],
        filename: Optional[str] = None,
    ) -> Optional[requests.Response]:
        """Upload a media to the ODK form (e.g. img, audio, video for a question).

        Args:
            projectId (int): The ID of the project on ODK Central
            form_name (str): The XForm to get the details of from ODK Central
            data (str, Path, BytesIO): The file path or BytesIO media file
            filename (str): If BytesIO object used, provide a file name.

        Returns:
            result (requests.Response): The response object.
        """
        # BytesIO memory object
        if isinstance(data, BytesIO):
            if filename is None:
                msg = "Cannot pass BytesIO object and not include the filename arg"
                log.error(msg)
                raise ValueError(msg)
            media = data.getvalue()
        # Filepath
        elif isinstance(data, str) or isinstance(data, Path):
            media_file_path = Path(data)
            if not media_file_path.exists():
                msg = f"File does not exist on disk: {media_file_path}"
                log.error(msg)
                raise ValueError(msg)
            with open(media_file_path, "rb") as file:
                media = file.read()
            filename = str(Path(data).name)

        # Validate filename present in XForm
        if not self.validateMedia(filename):
            msg = f"Uploaded media ({filename}), but is not present as a form field"
            log.error(msg)
            raise ValueError(msg)

        # Must first convert to draft if already published
        if not self.draft or self.published:
            # TODO should this use self.createForm ?
            log.debug(f"Updating form ({form_name}) to draft")
            url = f"{self.base}projects/{projectId}/forms/{form_name}/draft?ignoreWarnings=true"
            result = self.session.post(url, verify=self.verify)
            if result.status_code != 200:
                status = result.json()
                msg = f"Couldn't modify {form_name} to draft: {status['message']}"
                log.error(msg)
                raise ValueError(msg)

        # Upload the media
        url = f"{self.base}projects/{projectId}/forms/{form_name}/draft/attachments/{filename}"
        log.debug(f"Uploading media to URL: {url}")
        result = self.session.post(
            url, data=media, headers=dict({"Content-Type": "*/*"}, **self.session.headers), verify=self.verify
        )

        if result.status_code == 200:
            log.debug(f"Uploaded {filename} to Central")
        else:
            status = result.json()
            msg = f"Couldn't upload {filename} to Central: {status['message']}"
            log.error(msg)
            raise ValueError(msg)

        # Publish draft directly if requested, without using deprecated wrapper.
        if self.published:
            version = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            publish_url = (
                f"{self.base}projects/{projectId}/forms/{form_name}/draft/publish"
                f"?version={version}"
            )
            publish_result = self.session.post(publish_url, verify=self.verify)
            if publish_result.status_code != 200:
                try:
                    status = publish_result.json()
                    log.error(
                        f"Couldn't publish {form_name} on Central: {status.get('message')}"
                    )
                except json.decoder.JSONDecodeError:
                    log.error(
                        f"Couldn't publish {form_name} on Central: "
                        "Error decoding JSON response"
                    )
            else:
                self.draft = False
                self.published = True

        # Add to the form var
        self.media[filename] = media

        return result

    def createForm(
        self,
        projectId: int,
        data: Union[str, Path, BytesIO],
        form_name: Optional[str] = None,
        publish: Optional[bool] = False,
    ) -> Optional[str]:
        """Create a new form on an ODK Central server.

        - If no form_name is passed, the form name is generated by default in draft.
            If the publish param is also passed, then the form is published.
        - If form_name is passed, a new form is created from this in draft state.
            This copies across all attachments.

        Note:
            The form name (xmlFormId) is generated from the id="…" attribute
            immediately inside the <instance> tag of the XForm XML.

        Args:
            projectId (int): The ID of the project on ODK Central
            form_name (str): The user friendly name to provide the form
            data (str, Path, BytesIO): The XForm file path, or BytesIO memory obj
            publish (bool): If the new form should be published.
                Only valid if form_name is not passed, i.e. a new form.

        Returns:
            (str, Optional): The form name, else None if failure.
        """
        return _pyodk_replacement_stub(
            "OdkForm.createForm",
            "Client(...).forms.create(...) or Client(...).forms.update(...)",
        )

    def deleteForm(
        self,
        projectId: int,
        xform: str,
    ):
        """Delete a form from an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
        Returns:
            (bool): did it get deleted
        """
        return _pyodk_replacement_stub(
            "OdkForm.deleteForm",
            "Client(...).session.delete(.../forms/{form_id})",
        )

    def publishForm(
        self,
        projectId: int,
        xform: str,
    ) -> int:
        """Publish a draft form. When creating a form that isn't a draft, it can get published then.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (int): The status code from ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkForm.publishForm",
            "Client(...).forms.update(form_id=..., definition=...) with updated version",
        )

    def formFields(self, projectId: int, xform: str):
        """Retrieves the form fields for a xform from odk central.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            dict: A json object containing the form fields.

        """
        return _pyodk_replacement_stub(
            "OdkForm.formFields",
            "Client(...).session.get(.../forms/{form_id}/fields?odata=true)",
        )


class OdkAppUser(OdkCentral):
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ):
        """A Class for app user data.

        Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central

        Returns:
            (OdkAppUser): An instance of this object
        """
        super().__init__(url, user, passwd)
        self.user = None
        self.qrcode = None
        self.id = None

    def create(
        self,
        projectId: int,
        name: str,
    ):
        """Create a new app-user for a form.

        Example response:

        {
        "createdAt": "2018-04-18T23:19:14.802Z",
        "displayName": "My Display Name",
        "id": 115,
        "type": "user",
        "updatedAt": "2018-04-18T23:42:11.406Z",
        "deletedAt": "2018-04-18T23:42:11.406Z",
        "token": "d1!E2GVHgpr4h9bpxxtqUJ7EVJ1Q$Dusm2RBXg8XyVJMCBCbvyE8cGacxUx3bcUT",
        "projectId": 1
        }

        Args:
            projectId (int): The ID of the project on ODK Central
            name (str): The name of the XForm

        Returns:
            (dict): The response JSON from ODK Central
        """
        return _pyodk_replacement_stub(
            "OdkAppUser.create",
            "ProjectAppUserService(session=client.session, default_project_id=...).create(display_name=...)",
        )

    def delete(
        self,
        projectId: int,
        userId: int,
    ):
        """Create a new app-user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            userId (int): The ID of the user on ODK Central to delete

        Returns:
            (bool): Whether the user got deleted or not
        """
        return _pyodk_replacement_stub(
            "OdkAppUser.delete",
            "Client(...).session.delete(.../projects/{project_id}/app-users/{user_id})",
        )

    def updateRole(
        self,
        projectId: int,
        xform: str,
        roleId: int = 2,
        actorId: Optional[int] = None,
    ):
        """Update the role of an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            roleId (int): The role for the user
            actorId (int): The ID of the user

        Returns:
            (bool): Whether it was update or not
        """
        return _pyodk_replacement_stub(
            "OdkAppUser.updateRole",
            "FormAssignmentService(session=client.session, ...).assign(role_id=..., user_id=...)",
        )

    def grantAccess(self, projectId: int, roleId: int = 2, userId: int = None, xform: str = None, actorId: int = None):
        """Grant access to an app user for a form.

        Args:
            projectId (int): The ID of the project on ODK Central
            roleId (int): The role ID
            userId (int): The user ID of the user on ODK Central
            xform (str):  The XForm to get the details of from ODK Central
            actorId (int): The actor ID of the user on ODK Central

        Returns:
            (bool): Whether access was granted or not
        """
        return _pyodk_replacement_stub(
            "OdkAppUser.grantAccess",
            "FormAssignmentService(session=client.session, ...).assign(role_id=..., user_id=...)",
        )

    def createQRCode(
        self,
        odk_id: int,
        project_name: str,
        appuser_token: str,
        basemap: str = "osm",
        osm_username: str = "svchotosm",
        upstream_task_id: str = "",
        save_qrcode: bool = False,
    ) -> segno.QRCode:
        """Get the QR Code for an app-user.

        Notes on QR code params:

        - form_update_mode: 'manual' allows for easier offline mapping, while
            if set to 'match_exactly', it will attempt sync with Central

        - metadata_email: we 'misuse' this field to add additional metadata,
            in this case a task id from an upstream application (Field-TM).

        Args:
            odk_id (int): The ID of the project on ODK Central
            project_name (str): The name of the project to set
            appuser_token (str): The user's token
            basemap (str): Default basemap to use on Collect.
                Options: "google", "mapbox", "osm", "usgs", "stamen", "carto".
            osm_username (str): The OSM username to attribute to the mapping.
            save_qrcode (bool): Save the generated QR code to disk.

        Returns:
            segno.QRCode: The new QR code object
        """
        log.info(f"Generating QR Code for project ({odk_id}) {project_name}")

        self.settings = {
            "general": {
                "server_url": f"{self.base}key/{appuser_token}/projects/{odk_id}",
                "form_update_mode": "manual",
                "basemap_source": basemap,
                "autosend": "wifi_and_cellular",
                "metadata_username": osm_username,
                "metadata_email": upstream_task_id,
            },
            "project": {"name": f"{project_name}"},
            "admin": {},
        }

        # Base64 encode JSON params for QR code
        qr_data = b64encode(zlib.compress(json.dumps(self.settings).encode("utf-8")))
        # Generate QR code
        self.qrcode = segno.make(qr_data, micro=False)

        if save_qrcode:
            log.debug(f"Saving QR code to {project_name}.png")
            self.qrcode.save(f"{project_name}.png", scale=5)

        return self.qrcode
