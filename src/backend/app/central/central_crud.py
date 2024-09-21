# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
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
"""Logic for interaction with ODK Central & data."""

import csv
import json
from asyncio import gather
from io import BytesIO, StringIO
from typing import Optional, Union

import geojson
from defusedxml import ElementTree
from fastapi import HTTPException
from loguru import logger as log
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from osm_fieldwork.update_xlsform import append_mandatory_fields
from pyxform.xls2xform import convert as xform_convert
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.central import central_deps, central_schemas
from app.config import encrypt_value, settings
from app.db.postgis_utils import (
    geojson_to_javarosa_geom,
    javarosa_to_geojson_geom,
    parse_geojson_file_to_featcol,
)
from app.models.enums import HTTPStatus, TaskStatus, XLSFormType
from app.projects import project_schemas


def get_odk_project(odk_central: Optional[project_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkProject with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        project = OdkProject(url, user, pw)

    except ValueError as e:
        log.error(e)
        raise HTTPException(
            status_code=401,
            detail="""
            ODK credentials are invalid, or may have been updated. Please update them.
            """,
        ) from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return project


def get_odk_form(odk_central: project_schemas.ODKCentralDecrypted):
    """Helper function to get the OdkForm with credentials."""
    url = odk_central.odk_central_url
    user = odk_central.odk_central_user
    pw = odk_central.odk_central_password

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkForm(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def get_odk_app_user(odk_central: Optional[project_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkAppUser with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkAppUser(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def list_odk_projects(
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """List all projects on a remote ODK Server."""
    project = get_odk_project(odk_central)
    return project.listProjects()


def create_odk_project(
    name: str, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """Create a project on a remote ODK Server.

    Appends FMTM to the project name to help identify on shared servers.
    """
    project = get_odk_project(odk_central)

    try:
        log.debug(f"Attempting ODKCentral project creation: FMTM {name}")
        result = project.createProject(f"FMTM {name}")

        # Sometimes createProject returns a list if fails
        if isinstance(result, dict):
            if result.get("code") == 401.2:
                raise HTTPException(
                    status_code=500,
                    detail="Could not authenticate to odk central.",
                )

        log.debug(f"ODKCentral response: {result}")
        log.info(f"Project {name} available on the ODK Central server.")
        return result
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e


async def delete_odk_project(
    project_id: int, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """Delete a project from a remote ODK Server."""
    # FIXME: when a project is deleted from Central, we have to update the
    # odkid in the projects table
    try:
        project = get_odk_project(odk_central)
        result = project.deleteProject(project_id)
        log.info(f"Project {project_id} has been deleted from the ODK Central server.")
        return result
    except Exception:
        return "Could not delete project from central odk"


def delete_odk_app_user(
    project_id: int,
    name: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Delete an app-user from a remote ODK Server."""
    odk_app_user = get_odk_app_user(odk_central)
    result = odk_app_user.delete(project_id, name)
    return result


def create_odk_xform(
    odk_id: int,
    xform_data: BytesIO,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> str:
    """Create an XForm on a remote ODK Central server.

    Args:
        odk_id (str): Project ID for ODK Central.
        xform_data (BytesIO): XForm data to set.
        odk_credentials (ODKCentralDecrypted): Creds for ODK Central.

    Returns:
        form_name (str): ODK Central form name for the API.
    """
    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    xform_id = xform.createForm(odk_id, xform_data, publish=True)
    if not xform_id:
        namespaces = {
            "h": "http://www.w3.org/1999/xhtml",
            "odk": "http://www.opendatakit.org/xforms",
            "xforms": "http://www.w3.org/2002/xforms",
        }
        # Get the form id from the XML
        root = ElementTree.fromstring(xform_data.getvalue())
        xml_data = root.findall(".//xforms:data[@id]", namespaces)
        extracted_name = "Not Found"
        for dt in xml_data:
            extracted_name = dt.get("id")
        msg = f"Failed to create form on ODK Central: ({extracted_name})"
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from None
    return xform_id


def delete_odk_xform(
    project_id: int,
    xform_id: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Delete an XForm from a remote ODK Central server."""
    xform = get_odk_form(odk_central)
    result = xform.deleteForm(project_id, xform_id)
    # FIXME: make sure it's a valid project id
    return result


def list_odk_xforms(
    project_id: int,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
    metadata: bool = False,
):
    """List all XForms in an ODK Central project."""
    project = get_odk_project(odk_central)
    xforms = project.listForms(project_id, metadata)
    # FIXME: make sure it's a valid project id
    return xforms


def get_form_full_details(
    odk_project_id: int,
    form_id: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Get additional metadata for ODK Form."""
    form = get_odk_form(odk_central)
    form_details = form.getFullDetails(odk_project_id, form_id)
    return form_details


def get_odk_project_full_details(
    odk_project_id: int, odk_central: project_schemas.ODKCentralDecrypted
):
    """Get additional metadata for ODK project."""
    project = get_odk_project(odk_central)
    project_details = project.getFullDetails(odk_project_id)
    return project_details


def list_submissions(
    project_id: int, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """List all submissions for a project, aggregated from associated users."""
    project = get_odk_project(odk_central)
    xform = get_odk_form(odk_central)
    submissions = list()
    for user in project.listAppUsers(project_id):
        for subm in xform.listSubmissions(project_id, user["displayName"]):
            submissions.append(subm)

    return submissions


async def get_form_list(db: Session) -> list:
    """Returns the list of {id:title} for XLSForms in the database."""
    try:
        include_categories = [category.value for category in XLSFormType]

        sql_query = text(
            """
            SELECT id, title FROM xlsforms
            WHERE title IN
                (SELECT UNNEST(:categories));
            """
        )

        result = db.execute(sql_query, {"categories": include_categories}).fetchall()
        result_list = [{"id": row.id, "title": row.title} for row in result]
        return result_list

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


async def read_and_test_xform(input_data: BytesIO) -> None:
    """Read and validate an XForm.

    Args:
        input_data (BytesIO): form to be tested.

    Returns:
        BytesIO: the converted XML representation of the XForm.
    """
    try:
        log.debug("Parsing XLSForm --> XML data")
        # NOTE pyxform.xls2xform.convert returns a ConvertResult object
        return BytesIO(xform_convert(input_data).xform.encode("utf-8"))
    except Exception as e:
        log.error(e)
        msg = f"XLSForm is invalid: {str(e)}"
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from e


async def append_fields_to_user_xlsform(
    xlsform: BytesIO,
    form_category: str = "buildings",
    additional_entities: list[str] = None,
    task_count: int = None,
    existing_id: str = None,
) -> BytesIO:
    """Helper to return the intermediate XLSForm prior to convert."""
    log.debug("Appending mandatory FMTM fields to XLSForm")
    return await append_mandatory_fields(
        xlsform,
        form_category=form_category,
        additional_entities=additional_entities,
        task_count=task_count,
        existing_id=existing_id,
    )


async def validate_and_update_user_xlsform(
    xlsform: BytesIO,
    form_category: str = "buildings",
    additional_entities: list[str] = None,
    task_count: int = None,
    existing_id: str = None,
) -> BytesIO:
    """Wrapper to append mandatory fields and validate user uploaded XLSForm."""
    updated_file_bytes = await append_fields_to_user_xlsform(
        xlsform,
        form_category=form_category,
        additional_entities=additional_entities,
        task_count=task_count,
        existing_id=existing_id,
    )

    # Validate and return the form
    log.debug("Validating uploaded XLS form")
    return await read_and_test_xform(updated_file_bytes)


async def update_project_xform(
    xform_id: str,
    odk_id: int,
    xlsform: BytesIO,
    category: str,
    task_count: int,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> None:
    """Update and publish the XForm for a project.

    Args:
        xform_id (str): The UUID of the existing XForm in ODK Central.
        odk_id (int): ODK Central form ID.
        xlsform (UploadFile): XForm data.
        category (str): Category of the XForm.
        task_count (int): The number of tasks in a project.
        odk_credentials (project_schemas.ODKCentralDecrypted): ODK Central creds.

    Returns: None
    """
    xform_bytesio = await read_and_test_xform(xlsform)

    xform_obj = get_odk_form(odk_credentials)

    # NOTE calling createForm for an existing form will update it
    xform_obj.createForm(
        odk_id,
        xform_bytesio,
        form_name=xform_id,
    )
    # The draft form must be published after upload
    # NOTE we can't directly publish existing forms
    # in createForm and need 2 steps
    xform_obj.publishForm(odk_id, xform_id)


async def convert_geojson_to_odk_csv(
    input_geojson: BytesIO,
) -> StringIO:
    """Convert GeoJSON features to ODK CSV format.

    Used for form upload media (dataset) in ODK Central.

    Args:
        input_geojson (BytesIO): GeoJSON file to convert.

    Returns:
        feature_csv (StringIO): CSV of features in XLSForm format for ODK.
    """
    parsed_geojson = parse_geojson_file_to_featcol(input_geojson.getvalue())

    if not parsed_geojson:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Conversion GeoJSON --> CSV failed",
        )

    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    header = ["osm_id", "tags", "version", "changeset", "timestamp", "geometry"]
    csv_writer.writerow(header)

    features = parsed_geojson.get("features", [])
    for feature in features:
        geometry = feature.get("geometry")
        javarosa_geom = await geojson_to_javarosa_geom(geometry)

        properties = feature.get("properties", {})
        osm_id = properties.get("osm_id")
        tags = properties.get("tags")
        version = properties.get("version")
        changeset = properties.get("changeset")
        timestamp = properties.get("timestamp")

        csv_row = [osm_id, tags, version, changeset, timestamp, javarosa_geom]
        csv_writer.writerow(csv_row)

    # Reset buffer position to start to .read() works
    csv_buffer.seek(0)

    return csv_buffer


def flatten_json(data: dict, target: dict):
    """Flatten json properties to a single level.

    Removes any existing GeoJSON data from captured GPS coordinates in
    ODK submission.

    Usage:
        new_dict = {}
        flatten_json(original_dict, new_dict)
    """
    for k, v in data.items():
        if isinstance(v, dict):
            if "type" in v and "coordinates" in v:
                # GeoJSON object found, skip it
                continue
            flatten_json(v, target)
        else:
            target[k] = v


async def convert_odk_submission_json_to_geojson(
    input_json: Union[BytesIO, list],
) -> geojson.FeatureCollection:
    """Convert ODK submission JSON file to GeoJSON.

    Used for loading into QGIS.

    Args:
        input_json (BytesIO): ODK JSON submission list.

    Returns:
        geojson (BytesIO): GeoJSON format ODK submission.
    """
    if isinstance(input_json, list):
        submission_json = input_json
    else:
        submission_json = json.loads(input_json.getvalue())

    if not submission_json:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Project contains no submissions yet",
        )

    all_features = []
    for submission in submission_json:
        keys_to_remove = ["meta", "__id", "__system"]
        for key in keys_to_remove:
            submission.pop(key)

        data = {}
        flatten_json(submission, data)

        geojson_geom = await javarosa_to_geojson_geom(
            data.pop("xlocation", {}), geom_type="Polygon"
        )

        feature = geojson.Feature(geometry=geojson_geom, properties=data)
        all_features.append(feature)

    return geojson.FeatureCollection(features=all_features)


async def feature_geojson_to_entity_dict(
    feature: geojson.Feature,
) -> central_schemas.EntityDict:
    """Convert a single GeoJSON to an Entity dict for upload."""
    if not isinstance(feature, (dict, geojson.Feature)):
        log.error(f"Feature not in correct format: {feature}")
        raise ValueError(f"Feature not in correct format: {type(feature)}")

    feature_id = feature.get("id")

    geometry = feature.get("geometry", {})
    if not geometry:
        msg = "'geometry' data field is mandatory"
        log.debug(msg)
        raise ValueError(msg)

    javarosa_geom = await geojson_to_javarosa_geom(geometry)

    # NOTE all properties MUST be string values for Entities, convert
    properties = {
        str(key): str(value) for key, value in feature.get("properties", {}).items()
    }
    # Set to TaskStatus enum READY value (0)
    properties["status"] = "0"

    task_id = properties.get("task_id")
    entity_label = f"Task {task_id} Feature {feature_id}"

    return {"label": entity_label, "data": {"geometry": javarosa_geom, **properties}}


async def task_geojson_dict_to_entity_values(
    task_geojson_dict: dict[int, geojson.Feature],
) -> list[central_schemas.EntityDict]:
    """Convert a dict of task GeoJSONs into data for ODK Entity upload."""
    log.debug("Converting dict of task GeoJSONs to Entity upload format")

    asyncio_tasks = []
    for _, geojson_dict in task_geojson_dict.items():
        # Extract the features list and pass each Feature through
        features = geojson_dict.get("features", [])
        asyncio_tasks.extend(
            [feature_geojson_to_entity_dict(feature) for feature in features if feature]
        )

    return await gather(*asyncio_tasks)


async def create_entity_list(
    odk_creds: project_schemas.ODKCentralDecrypted,
    odk_id: int,
    dataset_name: str = "features",
    properties: list[str] = None,
    entities_list: list[central_schemas.EntityDict] = None,
) -> None:
    """Create a new Entity list in ODK."""
    if properties is None:
        # Get the default properties for FMTM project
        properties = central_schemas.entity_fields_to_list()
        log.debug(f"Using default FMTM properties for Entity creation: {properties}")

    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        # Step 1: create the Entity list, with properties
        await odk_central.createDataset(
            odk_id, datasetName=dataset_name, properties=properties
        )
        # Step 2: populate the Entities
        if entities_list:
            await odk_central.createEntities(
                odk_id,
                dataset_name,
                entities_list,
            )


async def get_entities_geojson(
    odk_creds: project_schemas.ODKCentralDecrypted,
    odk_id: int,
    dataset_name: str = "features",
    minimal: Optional[bool] = False,
) -> geojson.FeatureCollection:
    """Get the Entity details for a dataset / Entity list.

    Uses the OData endpoint from ODK Central.

    Currently it is not possible to filter via OData filters on custom params.
    TODO in the future filter by task_id via the URL,
    instead of returning all and filtering.

    Response GeoJSON format:
    {
        "type": "FeatureCollection",
        "features": [
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [xxx]
            },
            "id": uuid_of_entity,
            "properties": {
                "updated_at": "2024-04-11T18:23:30.787Z",
                "project_id": "1",
                "task_id": "1",
                "osm_id": "2",
                "tags": "xxx",
                "version": "1",
                "changeset": "1",
                "timestamp": "2024-12-20",
                "status": "LOCKED_FOR_MAPPING"
            }
        ]
    }


    Response GeoJSON format, minimal:
    {
        "type": "FeatureCollection",
        "features": [
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [xxx]
            },
            "id": uuid_of_entity,
            "properties": {
                "osm_id": "0044554",
                "updated_at": "2024-04-11T18:23:30.787Z",
                "status": "LOCKED_FOR_MAPPING"
            }
        ]
    }

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        minimal (bool): Remove all fields apart from id, updated_at, and status.

    Returns:
        dict: Entity data in OData JSON format.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entities = await odk_central.getEntityData(
            odk_id,
            dataset_name,
            url_params="$select=__id, __system/updatedAt, geometry, osm_id, status"
            if minimal
            else None,
        )

    all_features = []
    for entity in entities:
        flattened_dict = {}
        flatten_json(entity, flattened_dict)

        javarosa_geom = flattened_dict.pop("geometry") or ""
        geojson_geom = await javarosa_to_geojson_geom(
            javarosa_geom, geom_type="Polygon"
        )

        feature = geojson.Feature(
            geometry=geojson_geom,
            id=flattened_dict.pop("__id"),
            properties=flattened_dict,
        )
        all_features.append(feature)

    return geojson.FeatureCollection(features=all_features)


async def get_entities_data(
    odk_creds: project_schemas.ODKCentralDecrypted,
    odk_id: int,
    dataset_name: str = "features",
    fields: str = "__system/updatedAt, osm_id, status, task_id",
) -> list:
    """Get all the entity mapping statuses.

    No geometries are included.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        fields (str): Extra fields to include in $select filter.
            __id is included by default.

    Returns:
        list: JSON list containing Entity info. If updated_at is included,
            the format is string 2022-01-31T23:59:59.999Z.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entities = await odk_central.getEntityData(
            odk_id,
            dataset_name,
            url_params=f"$select=__id{',' if fields else ''} {fields}",
        )

    all_entities = []
    for entity in entities:
        flattened_dict = {}
        flatten_json(entity, flattened_dict)

        # Rename '__id' to 'id'
        flattened_dict["id"] = flattened_dict.pop("__id")

        # convert empty str osm_id to None
        # when new entities are created osm_id will be empty
        if flattened_dict.get("osm_id", "") == "":
            flattened_dict["osm_id"] = None

        all_entities.append(flattened_dict)

    return all_entities


def entity_to_flat_dict(
    entity: Optional[dict],
    odk_id: int,
    entity_uuid: str,
    dataset_name: str = "features",
) -> dict:
    """Convert returned Entity from ODK Central to flattened dict."""
    if not entity:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=(
                f"Entity ({entity_uuid}) not found in ODK project ({odk_id}) "
                f"and dataset ({dataset_name})"
            ),
        )

    # Remove dataReceived prior to flatten to avoid conflict with currentVersion
    entity.get("currentVersion", {}).pop("dataReceived")
    flattened_dict = {}
    flatten_json(entity, flattened_dict)

    # Rename 'uuid' to 'id'
    flattened_dict["id"] = flattened_dict.pop("uuid")

    return flattened_dict


async def get_entity_mapping_status(
    odk_creds: project_schemas.ODKCentralDecrypted,
    odk_id: int,
    entity_uuid: str,
    dataset_name: str = "features",
) -> dict:
    """Get an single entity mapping status.

    No geometries are included.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        dataset_name (str): The dataset / Entity list name in ODK Central.
        entity_uuid (str): The unique entity UUID for ODK Central.

    Returns:
        dict: JSON containing Entity: id, status, updated_at.
            updated_at is in string format 2022-01-31T23:59:59.999Z.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entity = await odk_central.getEntity(
            odk_id,
            dataset_name,
            entity_uuid,
        )
    return entity_to_flat_dict(entity, odk_id, entity_uuid, dataset_name)


async def update_entity_mapping_status(
    odk_creds: project_schemas.ODKCentralDecrypted,
    odk_id: int,
    entity_uuid: str,
    label: str,
    status: TaskStatus,
    dataset_name: str = "features",
) -> dict:
    """Update the Entity mapping status.

    This includes both the 'label' and 'status' data field.

    Args:
        odk_creds (ODKCentralDecrypted): ODK credentials for a project.
        odk_id (str): The project ID in ODK Central.
        entity_uuid (str): The unique entity UUID for ODK Central.
        label (str): New label, with emoji prepended for status.
        status (TaskStatus): New TaskStatus to assign, in string form.
        dataset_name (str): Override the default dataset / Entity list name 'features'.

    Returns:
        dict: All Entity data in OData JSON format.
    """
    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entity = await odk_central.updateEntity(
            odk_id,
            dataset_name,
            entity_uuid,
            label=label,
            data={
                "status": status,
            },
        )
    return entity_to_flat_dict(entity, odk_id, entity_uuid, dataset_name)


def upload_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    xform.uploadMedia(project_id, xform_id, filespec)


def download_media(
    project_id: int,
    xform_id: str,
    filename: str = "test",
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    xform.getMedia(project_id, xform_id, filename)


# FIXME replace osm_fieldwork.CSVDump with osm_fieldwork.ODKParsers
# def convert_csv(
#     filespec: str,
#     data: bytes,
# ):
#     """Convert ODK CSV to OSM XML and GeoJson."""
#     csvin = CSVDump("/xforms.yaml")

#     osmoutfile = f"{filespec}.osm"
#     csvin.createOSM(osmoutfile)

#     jsonoutfile = f"{filespec}.geojson"
#     csvin.createGeoJson(jsonoutfile)

#     if len(data) == 0:
#         log.debug("Parsing csv file %r" % filespec)
#         # The yaml file is in the package files for osm_fieldwork
#         data = csvin.parse(filespec)
#     else:
#         csvdata = csvin.parse(filespec, data)
#         for entry in csvdata:
#             log.debug(f"Parsing csv data {entry}")
#             if len(data) <= 1:
#                 continue
#             feature = csvin.createEntry(entry)
#             # Sometimes bad entries, usually from debugging XForm design, sneak in
#             if len(feature) > 0:
#                 if "tags" not in feature:
#                     log.warning("Bad record! %r" % feature)
#                 else:
#                     if "lat" not in feature["attrs"]:
#                         import epdb

#                         epdb.st()
#                     csvin.writeOSM(feature)
#                     # This GeoJson file has all the data values
#                     csvin.writeGeoJson(feature)
#                     pass

#     csvin.finishOSM()
#     csvin.finishGeoJson()

#     return True


async def get_appuser_token(
    xform_id: str,
    project_odk_id: int,
    odk_credentials: project_schemas.ODKCentralDecrypted,
    db: Session,
):
    """Get the app user token for a specific project.

    Args:
        db: The database session to use.
        odk_credentials: ODK credentials for the project.
        project_odk_id: The ODK ID of the project.
        xform_id: The ID of the XForm.

    Returns:
        The app user token.
    """
    try:
        appuser = get_odk_app_user(odk_credentials)
        odk_project = get_odk_project(odk_credentials)
        odk_app_user = odk_project.listAppUsers(project_odk_id)

        # delete if app_user already exists
        if odk_app_user:
            app_user_id = odk_app_user[0].get("id")
            appuser.delete(project_odk_id, app_user_id)

        # create new app_user
        appuser_name = "fmtm_user"
        log.info(
            f"Creating ODK appuser ({appuser_name}) for ODK project ({project_odk_id})"
        )
        appuser_json = appuser.create(project_odk_id, appuser_name)
        appuser_token = appuser_json.get("token")
        appuser_id = appuser_json.get("id")

        odk_url = odk_credentials.odk_central_url

        # Update the user role for the created xform
        log.info("Updating XForm role for appuser in ODK Central")
        response = appuser.updateRole(
            projectId=project_odk_id,
            xform=xform_id,
            actorId=appuser_id,
        )
        if not response.ok:
            try:
                json_data = response.json()
                log.error(json_data)
            except json.decoder.JSONDecodeError:
                log.error(
                    "Could not parse response json during appuser update. "
                    f"status_code={response.status_code}"
                )
            finally:
                msg = f"Failed to update appuser for formId: ({xform_id})"
                log.error(msg)
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
                ) from None
        odk_token = encrypt_value(
            f"{odk_url}/v1/key/{appuser_token}/projects/{project_odk_id}"
        )
        return odk_token

    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the app user token.",
        ) from e
