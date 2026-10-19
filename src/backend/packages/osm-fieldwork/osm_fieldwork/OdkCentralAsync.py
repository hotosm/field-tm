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
"""Minimal async ODK Central client for datasets (Entities)."""

import asyncio
import logging
import os
from typing import Optional

import aiohttp

log = logging.getLogger(__name__)


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


    # NOTE we removed a bunch of methods here, replacing with pyodk._endpoints.entities impl
    # - listEntities
    # - createEntity
    # - updateEntity
    # - deleteEntity


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
                    "creatorName": "field-tm@hotosm.org",
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
                "creatorName": "field-tm@hotosm.org",
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
