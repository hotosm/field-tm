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
from io import BytesIO, StringIO
from typing import Optional, Union
from xml.etree.ElementTree import Element, SubElement

import geojson
from defusedxml import ElementTree
from fastapi import HTTPException
from loguru import logger as log
from osm_fieldwork.CSVDump import CSVDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.builder import create_survey_element_from_dict
from pyxform.xls2json import parse_file_to_json
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.postgis_utils import (
    geojson_to_javarosa_geom,
    javarosa_to_geojson_geom,
    parse_and_filter_geojson,
)
from app.models.enums import HTTPStatus, XLSFormType
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

    form_name = xform.createForm(odk_id, xform_data, publish=True)
    if not form_name:
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

    return form_name


def delete_odk_xform(
    project_id: int,
    xform_id: str,
    filespec: str,
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


async def get_form_list(db: Session) -> dict:
    """Returns the dict of {id:title} for XLSForms in the database."""
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

        result_dict = {row.id: row.title for row in result}

        return result_dict

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


async def update_project_xform(
    task_ids: list[int],
    odk_id: int,
    xform_data: BytesIO,
    form_file_ext: str,
    project_name: str,
    category: str,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> None:
    """Update and publish the XForm for a project.

    Args:
        task_ids (List[int]): List of task IDs.
        odk_id (int): ODK Central form ID.
        xform_data (BytesIO): XForm data.
        form_file_ext (str): Extension of the form file.
        project_name (str): Name (title) of the project.
        category (str): Category of the XForm.
        odk_credentials (project_schemas.ODKCentralDecrypted): ODK Central creds.
    """
    # TODO in the future we may possibly support multiple forms per project.
    # TODO to faciliate this we need to add the _{category} suffix and track.
    # TODO this in the new xforms.category field/table.
    form_name = project_name

    xform_data = await read_and_test_xform(
        xform_data,
        form_file_ext,
        return_form_data=True,
    )
    updated_xform_data = await update_survey_xform(
        xform_data,
        form_name,
        category,
        task_ids,
    )

    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    # NOTE calling createForm with the form_name specified should update
    xform.createForm(
        odk_id,
        updated_xform_data,
        form_name,
    )
    # The draft form must be published after upload
    xform.publishForm(odk_id, form_name)


def download_submissions(
    project_id: int,
    xform_id: str,
    submission_id: Optional[str] = None,
    get_json: bool = True,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Download all submissions for an XForm."""
    xform = get_odk_form(odk_central)
    # FIXME: should probably filter by timestamps or status value
    data = xform.getSubmissions(project_id, xform_id, submission_id, True, get_json)
    fixed = str(data, "utf-8")
    return fixed.splitlines()


async def read_and_test_xform(
    input_data: BytesIO,
    form_file_ext: str,
    return_form_data: bool = False,
) -> Union[BytesIO, dict]:
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
            log.debug("Converting xlsform -> xform")
            json_data = parse_file_to_json(
                path="/dummy/path/with/file/ext.xls",
                file_object=input_data,
            )
            generated_xform = create_survey_element_from_dict(json_data)
            # NOTE do not enable validate=True, as this requires Java to be installed
            xform_bytesio = BytesIO(
                generated_xform.to_xml(
                    validate=False,
                ).encode("utf-8")
            )
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


async def update_entity_registration_xform(
    form_data: BytesIO,
    category: str,
) -> BytesIO:
    """Update fields in entity registration to name dataset.

    The CSV media must be named the same as the dataset (entity list).

    Args:
        form_data (str): The input registration form data.
        category (str): The form category, used to name the dataset (entity list)
            and the .csv file containing the geometries.

    Returns:
        BytesIO: The XForm data.
    """
    log.debug(f"Updating XML keys in Entity Registration XForm: {category}")

    # Parse the XML
    root = ElementTree.fromstring(form_data.getvalue())

    # Define namespaces
    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "xforms": "http://www.w3.org/2002/xforms",
        "jr": "http://openrosa.org/javarosa",
        "ns3": "http://www.opendatakit.org/xforms/entities",
        "odk": "http://www.opendatakit.org/xforms",
    }

    # Update the dataset name within the meta section
    for meta_elem in root.findall(".//xforms:entity[@dataset]", namespaces):
        meta_elem.set("dataset", category)

    # Update the attachment name to {category}.csv, to link to the entity list
    for instance_elem in root.findall(".//xforms:instance[@src]", namespaces):
        src_value = instance_elem.get("src", "")
        if src_value.endswith(".csv"):
            instance_elem.set("src", f"jr://file/{category}.csv")

    return BytesIO(ElementTree.tostring(root))


async def update_survey_xform(
    form_data: BytesIO,
    form_name: str,
    category: str,
    task_ids: list,
) -> BytesIO:
    """Update fields in the XForm to work with FMTM.

    Updates the 'id' and 'name' fields for the form.
    Updates the csv filename to match the dataset name.

    Args:
        form_data (str): The input form data.
        form_name (str): Name of the XForm to set.
        category (str): The form category, used to name the dataset (entity list)
            and the .csv file containing the geometries.
        task_ids (list): List of task IDs to insert as choices in form.

    Returns:
        BytesIO: The XForm data.
    """
    log.debug(f"Updating XML keys in survey XForm: {category}")

    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
        "entities": "http://www.opendatakit.org/xforms/entities",
    }

    # Parse the XML
    root = ElementTree.fromstring(form_data.getvalue())

    # Update id attribute to equal the form name to be generated
    xform_data = root.findall(".//xforms:data[@id]", namespaces)
    for dt in xform_data:
        dt.set("id", form_name)

    # Update the form title (displayed in ODK Collect)
    existing_title = root.find(".//h:title", namespaces)
    if existing_title is not None:
        existing_title.text = form_name

    # Update the attachment name to {category}.csv, to link to the entity list
    xform_instance_src = root.findall(".//xforms:instance[@src]", namespaces)
    for inst in xform_instance_src:
        src_value = inst.get("src", "")
        if src_value.endswith(".csv"):
            inst.set("src", f"jr://file/{category}.csv")

    # <instance> must be defined inside <model></model> key
    model_element = root.find(".//xforms:model", namespaces)
    instance_task_ids = Element("instance", id="task_id")
    # Create sub-elements for each task ID, <name> <label> pairs
    for task_id in task_ids:
        item = SubElement(instance_task_ids, "item")
        name = SubElement(item, "name")
        name.text = str(task_id)
        label = SubElement(item, "label")
        label.text = str(task_id)
    model_element.append(instance_task_ids)

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
    parsed_geojson = parse_and_filter_geojson(input_geojson.getvalue(), filter=False)

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


async def convert_odk_submission_json_to_geojson(
    input_json: BytesIO,
) -> BytesIO:
    """Convert ODK submission JSON file to GeoJSON.

    Used for loading into QGIS.

    Args:
        input_json (BytesIO): ODK JSON submission list.

    Returns:
        geojson (BytesIO): GeoJSON format ODK submission.
    """

    def flatten_submission(data, target):
        """Flatten geojson properties to a single level.

        Removes any existing GeoJSON data from captured GPS coordinates.
        """
        for k, v in data.items():
            if isinstance(v, dict):
                if "type" in v and "coordinates" in v:
                    # GeoJSON object found, skip it
                    continue
                flatten_submission(v, target)
            else:
                target[k] = v

    submission_json = json.loads(input_json.getvalue())

    if not submission_json:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Loading JSON submission failed",
        )

    all_features = []
    for submission in submission_json:
        keys_to_remove = ["meta", "__id", "__system"]
        for key in keys_to_remove:
            submission.pop(key)

        data = {}
        flatten_submission(submission, data)

        geojson_geom = await javarosa_to_geojson_geom(
            data.get("xlocation", {}), geom_type="Polygon"
        )

        feature = geojson.Feature(geometry=geojson_geom, properties=data)
        all_features.append(feature)

    featcol = geojson.FeatureCollection(features=all_features)

    return BytesIO(json.dumps(featcol).encode("utf-8"))


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
    filespec: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    filename = "test"
    xform.getMedia(project_id, xform_id, filename)


def convert_csv(
    filespec: str,
    data: bytes,
):
    """Convert ODK CSV to OSM XML and GeoJson."""
    csvin = CSVDump("/xforms.yaml")

    osmoutfile = f"{filespec}.osm"
    csvin.createOSM(osmoutfile)

    jsonoutfile = f"{filespec}.geojson"
    csvin.createGeoJson(jsonoutfile)

    if len(data) == 0:
        log.debug("Parsing csv file %r" % filespec)
        # The yaml file is in the package files for osm_fieldwork
        data = csvin.parse(filespec)
    else:
        csvdata = csvin.parse(filespec, data)
        for entry in csvdata:
            log.debug(f"Parsing csv data {entry}")
            if len(data) <= 1:
                continue
            feature = csvin.createEntry(entry)
            # Sometimes bad entries, usually from debugging XForm design, sneak in
            if len(feature) > 0:
                if "tags" not in feature:
                    log.warning("Bad record! %r" % feature)
                else:
                    if "lat" not in feature["attrs"]:
                        import epdb

                        epdb.st()
                    csvin.writeOSM(feature)
                    # This GeoJson file has all the data values
                    csvin.writeGeoJson(feature)
                    pass

    csvin.finishOSM()
    csvin.finishGeoJson()

    return True
