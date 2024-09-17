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
import os
import uuid
from io import BytesIO, StringIO
from typing import Optional, Union
from xml.etree.ElementTree import Element, SubElement

import geojson
from defusedxml import ElementTree
from fastapi import HTTPException
from loguru import logger as log
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.xls2xform import convert as xform_convert
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.central import central_deps
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


async def update_project_xform(
    xform_id: str,
    odk_id: int,
    xform_data: BytesIO,
    form_file_ext: str,
    category: str,
    task_count: int,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> None:
    """Update and publish the XForm for a project.

    Args:
        xform_id (str): The UUID of the existing XForm in ODK Central.
        odk_id (int): ODK Central form ID.
        xform_data (BytesIO): XForm data.
        form_file_ext (str): Extension of the form file.
        category (str): Category of the XForm.
        task_count (int): The number of tasks in a project.
        odk_credentials (project_schemas.ODKCentralDecrypted): ODK Central creds.
    """
    xform_data = await read_and_test_xform(
        xform_data,
        form_file_ext,
        return_form_data=True,
    )
    updated_xform_data = await modify_xform_xml(
        xform_data,
        category,
        task_count,
        existing_id=xform_id,
    )

    xform_obj = get_odk_form(odk_credentials)

    # NOTE calling createForm for an existing form will update it
    xform_obj.createForm(
        odk_id,
        updated_xform_data,
        form_name=xform_id,
    )
    # The draft form must be published after upload
    xform_obj.publishForm(odk_id, xform_id)


async def read_and_test_xform(
    input_data: BytesIO,
    form_file_ext: str,
    return_form_data: bool = False,
) -> BytesIO | dict:
    """Read and validate an XForm.

    Args:
        input_data (BytesIO): form to be tested.
        form_file_ext (str): type of form (.xls, .xlsx, or .xml).
        return_form_data (bool): return the XForm data.
    """
    # Read from BytesIO object
    file_ext = form_file_ext.lower()

    if file_ext == ".xml":
        xform_bytesio = input_data
        # Parse / validate XForm
        try:
            ElementTree.fromstring(xform_bytesio.getvalue())
        except ElementTree.ParseError as e:
            log.error(e)
            msg = f"Error parsing XForm XML: Possible reason: {str(e)}"
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
            ) from e
    else:
        try:
            log.debug("Parsing XLSForm --> XML data")
            xform_bytesio = BytesIO(xform_convert(input_data).xform.encode("utf-8"))
        except Exception as e:
            log.error(e)
            msg = f"XLSForm is invalid: {str(e)}"
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
            ) from e

    # Return immediately
    if return_form_data:
        return xform_bytesio

    # Load XML
    xform_xml = ElementTree.fromstring(xform_bytesio.getvalue())

    # Extract csv filenames
    try:
        namespaces = {"xforms": "http://www.w3.org/2002/xforms"}
        csv_list = [
            os.path.splitext(inst.attrib["src"].split("/")[-1])[0]
            for inst in xform_xml.findall(".//xforms:instance[@src]", namespaces)
            if inst.attrib.get("src", "").endswith(".csv")
        ]

        # No select_one_from_file defined
        if not csv_list:
            msg = (
                "The form has no select_one_from_file or "
                "select_multiple_from_file field defined for a CSV."
            )
            raise ValueError(msg) from None

        return {"required_media": csv_list, "message": "Your form is valid"}

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


async def modify_xform_xml(
    form_data: BytesIO,
    category: str,
    task_count: int,
    existing_id: Optional[str] = None,
) -> BytesIO:
    """Update fields in the XForm to work with FMTM.

    The 'id' field is set to random UUID (xFormId) unless existing_id is specified
    The 'name' field is set to the category name.
    The upload media must be equal to 'features.csv'.
    The task_filter options are populated as choices in the form.
    The form_category value is also injected to display in the instructions.

    Args:
        form_data (str): The input form data.
        category (str): The form category, used to name the dataset (entity list)
            and the .csv file containing the geometries.
        task_count (int): The number of tasks in a project.
        existing_id (str): An existing XForm ID in ODK Central, for updating.

    Returns:
        BytesIO: The XForm data.
    """
    log.debug(f"Updating XML keys in survey XForm: {category}")

    if existing_id:
        xform_id = existing_id
    else:
        xform_id = uuid.uuid4()

    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
        "entities": "http://www.opendatakit.org/xforms/entities",
    }

    # Parse the XML from BytesIO obj
    root = ElementTree.fromstring(form_data.getvalue())

    xform_data = root.findall(".//xforms:data[@id]", namespaces)
    for dt in xform_data:
        # This sets the xFormId in ODK Central (the form reference via API)
        dt.set("id", str(xform_id))

    # Update the form title (displayed in ODK Collect)
    existing_title = root.find(".//h:title", namespaces)
    if existing_title is not None:
        existing_title.text = category

    # Update the attachment name to {category}.csv, to link to the entity list
    xform_instance_src = root.findall(".//xforms:instance[@src]", namespaces)
    for inst in xform_instance_src:
        src_value = inst.get("src", "")
        if src_value.endswith(".geojson") or src_value.endswith(".csv"):
            # NOTE geojson files require jr://file/features.geojson
            # NOTE csv files require jr://file-csv/features.csv
            inst.set("src", "jr://file-csv/features.csv")

    # NOTE add the task ID choices to the XML
    # <instance> must be defined inside <model></model> root element
    model_element = root.find(".//xforms:model", namespaces)
    # The existing dummy value for task_filter must be removed
    existing_instance = model_element.find(
        ".//xforms:instance[@id='task_filter']", namespaces
    )
    if existing_instance is not None:
        model_element.remove(existing_instance)
    # Create a new instance element
    instance_task_filters = Element("instance", id="task_filter")
    root_element = SubElement(instance_task_filters, "root")
    # Create sub-elements for each task ID, <itextId> <name> pairs
    for task_id in range(1, task_count + 1):
        item = SubElement(root_element, "item")
        SubElement(item, "itextId").text = f"task_filter-{task_id}"
        SubElement(item, "name").text = str(task_id)
    model_element.append(instance_task_filters)

    # Add task_filter choice translations (necessary to be visible in form)
    itext_element = root.find(".//xforms:itext", namespaces)
    if itext_element is not None:
        existing_translations = itext_element.findall(
            ".//xforms:translation", namespaces
        )
        for translation in existing_translations:
            # Remove dummy value from existing translations
            existing_text = translation.find(
                ".//xforms:text[@id='task_filter-0']", namespaces
            )
            if existing_text is not None:
                translation.remove(existing_text)

            # Append new <text> elements for each task_id
            for task_id in range(1, task_count + 1):
                new_text = Element("text", id=f"task_filter-{task_id}")
                value_element = Element("value")
                value_element.text = str(task_id)
                new_text.append(value_element)
                translation.append(new_text)

    # Hardcode the form_category value for the start instructions
    form_category_update = root.find(
        ".//xforms:bind[@nodeset='/data/form_category']", namespaces
    )
    if form_category_update is not None:
        if category.endswith("s"):
            # Plural to singular
            category = category[:-1]
        form_category_update.set("calculate", f"once('{category.rstrip('s')}')")

    return BytesIO(ElementTree.tostring(root))


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
