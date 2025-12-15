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
"""The async counterpart to OdkCentral.py, an ODK Central API client."""

import asyncio
import logging
import os
from asyncio import gather
from typing import Any, Optional, TypedDict
from uuid import uuid4

import aiohttp

log = logging.getLogger(__name__)


class EntityIn(TypedDict):
    """Required format for Entity uploads to ODK Central."""

    label: str
    data: dict[str, Any]


class OdkCentral:
    """Helper methods for ODK Central API."""

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
            session (str): Pass in an existing session for reuse.

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

        # Base URL for the REST API
        self.version = "v1"
        self.base = f"{self.url}/{self.version}/"

    def __enter__(self):
        """Sync context manager not allowed."""
        raise RuntimeError("Must be called with async context manager 'async with'")

    def __exit__(self):
        """Sync context manager not allowed."""
        raise RuntimeError("Must be called with async context manager 'async with'")

    async def __aenter__(self):
        """Async object instantiation."""
        # Header enables persistent connection, creates a cookie for this session
        self.session = aiohttp.ClientSession(
            raise_for_status=True,
        )
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Async object close."""
        if self.session:
            await self.session.close()

    async def authenticate(self):
        """Authenticate to an ODK Central server."""
        try:
            async with self.session.post(f"{self.base}sessions", json={"email": self.user, "password": self.passwd}) as response:
                token = (await response.json())["token"]
                self.session.headers.update({"Authorization": f"Bearer {token}"})
        except aiohttp.ClientConnectorError as request_error:
            await self.session.close()
            raise ConnectionError("Failed to connect to Central. Is the URL valid?") from request_error
        except aiohttp.ClientResponseError as response_error:
            await self.session.close()
            if response_error.status == 401:
                raise ConnectionError("ODK credentials are invalid, or may have changed. Please update them.") from response_error
            raise response_error

    async def s3_reset(self) -> None:
        """Reset failed S3 uploads."""
        url = f"{self.base}s3/reset-failed"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                if not response.ok:
                    msg = "Failed to trigger S3 reset in Central"
                    log.error(msg)
                    raise Exception(msg)
        except aiohttp.ClientError as e:
            msg = f"ClientError during S3 reset attempt in Central: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def s3_sync(self) -> None:
        """Trigger the S3 sync system endpoint."""
        url = f"{self.base}s3/sync"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                if not response.ok:
                    msg = "Failed to trigger S3 sync in Central"
                    log.error(msg)
                    raise Exception(msg)
        except aiohttp.ClientError as e:
            msg = f"ClientError during S3 sync attempt in Central: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

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

    async def listForms(self, projectId: int, metadata: bool = False):
        """Fetch a list of forms in a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central

        Returns:
            (list): The list of XForms in this project
        """
        url = f"{self.base}projects/{projectId}/forms"
        headers = {}
        if metadata:
            headers.update({"X-Extended-Metadata": "true"})
        try:
            async with self.session.get(url, ssl=self.verify, headers=headers) as response:
                self.forms = await response.json()
                return self.forms
        except aiohttp.ClientError as e:
            msg = f"Error fetching forms: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getAllProjectSubmissions(self, projectId: int, xforms: list = None, filters: dict = None):
        """Fetch a list of submissions in a project on an ODK Central server.

        Args:
            projectId (int): The ID of the project on ODK Central
            xforms (list): The list of XForms to get the submissions of

        Returns:
            (json): All of the submissions for all of the XForm in a project
        """
        # TODO this function needs more testing!

        log.info(f"Getting all submissions for ODK project ({projectId}) forms ({xforms})")
        submission_data = []

        async with OdkForm(self.url, self.user, self.passwd) as odk_form:
            submission_tasks = [odk_form.listSubmissions(projectId, xform, filters) for xform in xforms or []]

            submissions = await gather(*submission_tasks, return_exceptions=True)

        for submission in submissions:
            if isinstance(submission, Exception):
                log.error(f"Failed to get submissions: {submission}")
                continue
            log.debug(f"There are {len(submission['value'])} submissions")
            submission_data.extend(submission["value"])

        return submission_data


class OdkForm(OdkCentral):
    """Class to manipulate a Form on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ) -> None:
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkForm): An instance of this object.
        """
        super().__init__(url, user, passwd)

    async def listFormAttachments(self, projectId: int, xform: str):
        """Fetch a list of attachments listed for upload on a given form.

        Returns data in format:

        [
            {'name': '1731673738156.jpg', 'exists': False},
        ]

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list[dict]): The list of form attachments.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/attachments"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            msg = f"Error fetching form attachments: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getFormAttachmentUrls(
        self,
        projectId: int,
        xform: str,
    ) -> dict[str, Optional[str | bytes]]:
        """Get a dictionary of form attachment names to pre-signed S3 URLs or raw binary content.

        Args:
            projectId (int): The ID of the project on ODK Central.
            xform (str): The XForm ID to get attachments from.

        Returns:
            dict[str, Optional[Union[str, bytes]]]: A mapping from attachment names to either:
                - a pre-signed S3 URL (str), or
                - raw bytes (if file was returned directly),
                - or None if the attachment couldn't be fetched.
        """
        attachments = await self.listFormAttachments(projectId, xform)
        if not attachments:
            return {}

        # Filter out dataset attachments
        filtered_attachments = [
            att for att in attachments if not att.get("datasetExists")
        ]

        async def fetch_url(attachment: dict) -> tuple[str, Optional[str | bytes]]:
            filename = attachment["name"]
            url = f"{self.base}projects/{projectId}/forms/{xform}/attachments/{filename}"

            try:
                result = await self.session.get(url, ssl=self.verify, allow_redirects=False)

                if result.status >= 400:
                    log.warning(
                        f"Failed to fetch form attachment '{filename}' "
                        f"(status {result.status}) from form '{xform}' (project {projectId})"
                    )
                    return filename, None

                s3_url = result.headers.get("Location")
                if s3_url:
                    return filename, s3_url

                # If not a redirect, assume raw binary data is returned
                try:
                    content = await result.read()
                except Exception as read_err:
                    log.warning(
                        f"Failed to read binary data for attachment '{filename}' "
                        f"on form '{xform}' (project {projectId}): {read_err}"
                    )
                    return filename, None

                return filename, content

            except Exception as e:
                log.warning(
                    f"Exception while fetching form attachment '{filename}' "
                    f"from form '{xform}' (project {projectId}): {e}"
                )
                return filename, None

        urls = await gather(*(fetch_url(att) for att in filtered_attachments))
        return {filename: url_or_bytes for filename, url_or_bytes in urls}

    async def listSubmissions(self, projectId: int, xform: str):
        """Fetch a list of submission instances for a given form.

        NOTE this does not use the OData endpoint, but instead opts to use the standard
        Central POST endpoint

        Returns data in format:

        [{
            instanceId: "uuid:e83db2b4-5e82-4e61-bc32-04750e511aff"
            ...
        },]

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central

        Returns:
            (list[dict]): The list of submissions.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            msg = f"Error fetching submissions: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getSubmissionXml(
        self,
        projectId: int,
        xform: str,
        submissionUuid: str,
    ):
        """Retrieve the XML content of a submission.

        Args:
            projectId (int): The ID of the project on ODK Central.
            xform (str): The XForm ID on ODK Central.
            submissionUuid (str): The UUID of the submission.

        Returns:
            Optional[str]: The XML content as a string.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions/{submissionUuid}.xml"

        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.text()
        except Exception as e:
            log.error(f"Failed to fetch submission XML for {submissionUuid}: {e}")
            return None

    async def listSubmissionAttachments(self, projectId: int, xform: str, submissionUuid: str):
        """Fetch a list of attachments listed for upload on a given submission.

        Returns data in format:

        [
            {'name': '1731673738156.jpg', 'exists': False},
        ]

        Args:
            projectId (int): The ID of the project on ODK Central
            xform (str): The XForm to get the details of from ODK Central
            submissionUuid (str): The submission UUID from ODK Central

        Returns:
            (list[dict]): The list of submission attachments.
        """
        url = f"{self.base}projects/{projectId}/forms/{xform}/submissions/{submissionUuid}/attachments"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            msg = f"Error fetching submissions: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getSubmissionAttachmentUrls(
        self,
        projectId: int,
        xform: str,
        submissionUuid: str,
    ) -> dict[str, str]:
        """Get a dictionary of attachment names and their pre-signed URLs.

        Args:
            projectId (int): The ID of the project on ODK Central.
            xform (str): The XForm to get the details of from ODK Central.
            submissionUuid (str): The UUID of the submission on ODK Central.

        Returns:
            dict[str, str]: A dictionary mapping attachment names to URLs.
        """
        attachments = await self.listSubmissionAttachments(projectId, xform, submissionUuid)
        if not attachments:
            return {}

        async def fetch_url(attachment: dict) -> tuple[str, Optional[str]]:
            """Fetch the pre-signed URL for a given attachment filename."""
            filename = attachment["name"]
            url = f"{self.base}projects/{projectId}/forms/{xform}/submissions/{submissionUuid}/attachments/{filename}"

            # Prevent the redirect and blob download, instead get the S3 URL
            result = await self.session.get(url, ssl=self.verify, allow_redirects=False)

            if result.status in (301, 302, 303, 307, 308):  # is a redirect to the S3 URL
                s3_url = result.headers.get("Location")
                if not s3_url:
                    try:
                        text_body = await result.text()
                    except UnicodeDecodeError:
                        text_body = "[Binary data]"
                    log.error(
                        f"No 'Location' response header for {filename} from Central: "
                        f"{text_body}"
                    )
                    return filename, None
            else:
                try:
                    log.error(
                        f"Incorrect response code for {filename} from Central: "
                        f"{await result.text()}"
                    )
                except UnicodeDecodeError:
                    log.error(f"Central response code: {result.status}")
                    log.error(
                        "Central appears to be returning the binary data instead "
                        "of the S3 URL. Is Central configured to use S3 storage? "
                        "Or perhaps the file is simply not uploaded to S3 yet."
                    )

                return filename, None

            return filename, s3_url

        urls = await gather(*(fetch_url(attachment) for attachment in attachments))

        return {filename: url for filename, url in urls if url is not None}


class OdkDataset(OdkCentral):
    """Class to manipulate a Entity on an ODK Central server."""

    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
    ) -> None:
        """Args:
            url (str): The URL of the ODK Central
            user (str): The user's account name on ODK Central
            passwd (str):  The user's account password on ODK Central.

        Returns:
            (OdkDataset): An instance of this object.
        """
        super().__init__(url, user, passwd)

    async def listDatasets(
        self,
        projectId: int,
    ) -> list:
        """Get all Entity datasets (entity lists) for a project.

        JSON response:
        [
            {
                "name": "people",
                "createdAt": "2018-01-19T23:58:03.395Z",
                "projectId": 1,
                "approvalRequired": true
            }
        ]

        Args:
            projectId (int): The ID of the project on ODK Central.

        Returns:
            list: a list of JSON dataset metadata.
        """
        url = f"{self.base}projects/{projectId}/datasets/"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            msg = f"Error fetching datasets: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def createDataset(
        self,
        projectId: int,
        datasetName: Optional[str] = "features",
        properties: Optional[list[str]] = [],
    ):
        """Creates a dataset for a given project.

        Args:
            projectId (int): The ID of the project to create the dataset for.
            datasetName (str): The name of the dataset to be created.
            properties (list[str]): List of property names to create.
                Alternatively call createDatasetProperty for each property manually.

        Returns:
            dict: The JSON response containing information about the created dataset.

        Raises:
            aiohttp.ClientError: If an error occurs during the dataset creation process.
        """
        # Validation of properties param
        if properties and (not isinstance(properties, list) or not isinstance(properties[-1], str)):
            msg = "The properties must be a list of string values to create a dataset"
            log.error(msg)
            raise ValueError(msg)

        # Create the dataset
        url = f"{self.base}projects/{projectId}/datasets"
        payload = {"name": datasetName}
        try:
            log.info(f"Creating dataset ({datasetName}) for ODK project ({projectId})")
            async with self.session.post(
                url,
                ssl=self.verify,
                json=payload,
            ) as response:
                if response.status not in (200, 201):
                    error_message = await response.text()
                    log.error(f"Failed to create Dataset: {error_message}")
                log.info(f"Successfully created Dataset {datasetName}")
                dataset = await response.json()
        except aiohttp.ClientError as e:
            msg = f"Failed to create Dataset: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

        if not properties:
            return dataset

        # Add the properties, if specified
        # FIXME this is a bit of a hack until ODK Central has better support
        # FIXME for adding dataset properties in bulk
        try:
            log.debug(f"Creating properties for dataset ({datasetName}): {properties}")
            for field in properties:
                try:
                    await self.createDatasetProperty(projectId, field, datasetName)
                    await asyncio.sleep(0.1)
                except aiohttp.ClientError as e:
                    log.error(f"Failed to create property ({field}) for dataset {datasetName}: {e}")
                    continue
        except aiohttp.ClientError as e:
            msg = f"Failed to create properties: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

        # Manually append to prevent another API call
        dataset["properties"] = properties
        return dataset

    async def createDatasetProperty(
        self,
        projectId: int,
        field_name: str,
        datasetName: Optional[str] = "features",
    ):
        """Create a property for a dataset.

        Args:
            projectId (int): The ID of the project.
            datasetName (str): The name of the dataset.
            field (dict): A dictionary containing the field information.

        Returns:
            dict: The response data from the API.

        Raises:
            aiohttp.ClientError: If an error occurs during the API request.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/properties"
        payload = {
            "name": field_name,
        }

        try:
            log.debug(f"Creating property ({field_name}) for dataset {datasetName}")
            async with self.session.post(url, ssl=self.verify, json=payload) as response:
                response_data = await response.json()
                if response.status not in (200, 201):
                    log.warning(f"Failed to create properties: {response.status}, message='{response_data}'")
                log.debug(f"Successfully created property ({field_name}) for dataset {datasetName}")
                return response_data
        except aiohttp.ClientError as e:
            msg = f"Failed to create properties: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getEntity(
        self,
        projectId: int,
        datasetName: str,
        entityUuid: str,
    ) -> dict:
        """Get a single Entity by it's UUID for a project.

        JSON response:
        {
        "uuid": "a54400b6-49fe-4787-9ab8-7e2f56ff52bc",
        "createdAt": "2024-04-15T09:26:08.209Z",
        "creatorId": 5,
        "updatedAt": null,
        "deletedAt": null,
        "conflict": null,
        "currentVersion": {
            "createdAt": "2024-04-15T09:26:08.209Z",
            "current": true,
            "label": "test entity",
            "creatorId": 5,
            "userAgent": "Python/3.10 aiohttp/3.9.3",
            "data": {
                "osm_id": "1",
                "geometry": "test"
            },
            "version": 1,
            "baseVersion": null,
            "dataReceived": {
                "label": "test entity",
                "osm_id": "1",
                "geometry": "test"
            },
            "conflictingProperties": null
        }
        }

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (str): The name of a dataset, specific to a project.
            entityUuid (str): Unique itentifier of the entity in the dataset.

        Returns:
            dict: the JSON entity details, for a specific dataset.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities/{entityUuid}"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            # NOTE skip raising exception on HTTP 404 (not found)
            log.error(f"Error fetching entity: {e}")
            return {}

    # NOTE we removed a bunch of methods here, replacing with pyodk._endpoints.entities impl
    # - listEntities
    # - createEntity
    # - updateEntity
    # - deleteEntity

    async def createEntities(
        self,
        projectId: int,
        datasetName: str,
        entities: list[EntityIn],
    ) -> dict:
        """Bulk create Entities in a project dataset (entity list).

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.
            entities (list[EntityIn]): A list of Entities to insert.
                Format: {"label": "John Doe", "data": {"firstName": "John", "age": "22"}}

        Returns:
            # list: A list of Entity detail JSONs.
            #     The 'uuid' field includes the unique entity identifier.
            dict: {'success': true}
                When creating bulk entities ODK Central return this for now.
        """
        # Validation
        if not isinstance(entities, list):
            raise ValueError("Entities must be a list")

        log.info(f"Bulk uploading ({len(entities)}) Entities for ODK project ({projectId}) dataset ({datasetName})")
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}/entities"
        payload = {"entities": entities, "source": {"name": "features.csv"}}

        try:
            async with self.session.post(url, ssl=self.verify, json=payload) as response:
                response.raise_for_status()
                log.info(f"Successfully created entities for ODK project ({projectId}) in dataset ({datasetName})")
                return await response.json()
        except aiohttp.ClientError as e:
            msg = f"Failed to create Entities: {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

    async def getEntityCount(
        self,
        projectId: int,
        datasetName: str,
    ) -> int:
        """Get only the count of the Entity entries.

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.

        Returns:
            int: All entity data for a project dataset.
        """
        # NOTE returns no entity data (value: []), only the count
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}.svc/Entities?%24top=0&%24count=true"
        try:
            async with self.session.get(url, ssl=self.verify) as response:
                count = (await response.json()).get("@odata.count", None)
        except aiohttp.ClientError as e:
            msg = f"Failed to get Entity count for ODK project ({projectId}): {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e

        if count is None:
            log.debug(f"Project ({projectId}) has no Entities in dataset ({datasetName})")
            return 0

        return count

    async def getEntityData(
        self,
        projectId: int,
        datasetName: str,
        url_params: Optional[str] = None,
        include_metadata: Optional[bool] = False,
    ) -> dict | list:
        """Get a lightweight JSON of the entity data fields in a dataset.

        Be sure to check the latest docs to see which fields are supported for
        OData filtering:
        https://docs.getodk.org/central-api-odata-endpoints/#id3

        Example response list (include_metadata=False):
        [
            {
                "__id": "523699d0-66ec-4cfc-a76b-4617c01c6b92",
                "label": "the_label_you_defined",
                "__system": {
                    "createdAt": "2024-03-24T06:30:31.219Z",
                    "creatorId": "7",
                    "creatorName": "fmtm@hotosm.org",
                    "updates": 4,
                    "updatedAt": "2024-03-24T07:12:55.871Z",
                    "version": 5,
                    "conflict": null
                },
                "geometry": "javarosa format geometry",
                "user_defined_field2": "text",
                "user_defined_field2": "text",
                "user_defined_field3": "test"
            }
        ]

        Example response JSON where:
        - url_params="$top=205&$count=true"
        - include_metadata=True automatically due to use of $top param

        {
        "value": [
            {
            "__id": "523699d0-66ec-4cfc-a76b-4617c01c6b92",
            "label": "the_label_you_defined",
            "__system": {
                "createdAt": "2024-03-24T06:30:31.219Z",
                "creatorId": "7",
                "creatorName": "fmtm@hotosm.org",
                "updates": 4,
                "updatedAt": "2024-03-24T07:12:55.871Z",
                "version": 5,
                "conflict": null
            },
            "geometry": "javarosa format geometry",
            "user_defined_field2": "text",
            "user_defined_field2": "text",
            "user_defined_field3": "test"
            }
        ]
        "@odata.context": (
            "https://URL/v1/projects/6/datasets/buildings.svc/$metadata#Entities",
        )
        "@odata.nextLink": (
            "https://URL/v1/projects/6/datasets/buildings.svc/Entities"
            "?%24top=250&%24count=true&%24skiptoken=returnedtokenhere%3D"
        "@odata.count": 667
        }

        Info on OData URL params:
        http://docs.oasis-open.org
        /odata/odata/v4.01/odata-v4.01-part1-protocol.html#_Toc31358948

        Args:
            projectId (int): The ID of the project on ODK Central.
            datasetName (int): The name of a dataset, specific to a project.
            url_params (str): Any supported OData URL params, such as 'filter'
                or 'select'. The ? is not required.
            include_metadata (bool): Include additional metadata.
                If true, returns a dict, if false, returns a list of Entities.
                If $top is included in url_params, this is enabled by default to get
                the "@odata.nextLink" field.

        Returns:
            list | dict: All (or filtered) entity data for a project dataset.
        """
        url = f"{self.base}projects/{projectId}/datasets/{datasetName}.svc/Entities"
        if url_params:
            url += f"?{url_params}"
            if "$top" in url_params:
                # Force enable metadata, as required for pagination
                include_metadata = True

        try:
            async with self.session.get(url, ssl=self.verify) as response:
                response_json = await response.json()
                if not include_metadata:
                    return response_json.get("value", [])
                return response_json
        except aiohttp.ClientError as e:
            msg = f"Failed to get Entity data for ODK project ({projectId}): {e}"
            log.error(msg)
            raise aiohttp.ClientError(msg) from e
