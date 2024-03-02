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

import os
from asyncio import gather
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from defusedxml import ElementTree
from fastapi import HTTPException
from loguru import logger as log
from osm_fieldwork.CSVDump import CSVDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.xls2xform import xls2xform_convert
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import HTTPStatus
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
    geojson_file_name: str,
    geojson_data: BytesIO,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> str:
    """Create an XForm on a remote ODK Central server.

    Args:
        odk_id (str): Project ID for ODK Central.
        xform_data (BytesIO): XForm data to set.
        geojson_file_name (str): Name of the attached geojson media file.
        geojson_data (BytesIO): GeoJSON data to set.
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
        # Parse the XML
        root = ElementTree.fromstring(xform_data.getvalue())
        # Update id attribute to equal the form name to be generated
        xml_data = root.findall(".//xforms:data[@id]", namespaces)
        extracted_name = "Not Found"
        for dt in xml_data:
            extracted_name = dt.get("id")
        msg = f"Failed to create form on ODK Central: ({extracted_name})"
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from None

    # This modifies an existing published XForm to be in draft mode.
    # An XForm must be in draft mode to upload an attachment.
    # Upload the geojson of features to be modified
    # NOTE the form is automatically republished
    result = xform.uploadMedia(
        odk_id,
        form_name,
        geojson_data,
        filename=geojson_file_name,
    )
    if not result:
        msg = f"Failed to upload file ({geojson_file_name}) to form ({form_name})"
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


def get_form_list(db: Session, skip: int, limit: int):
    """Returns the list of id and title of xforms from the database."""
    try:
        categories_to_filter = [
            "amenities",
            "camping",
            "cemeteries",
            "education",
            "nature",
            "places",
            "wastedisposal",
            "waterpoints",
        ]

        sql_query = text(
            """
            SELECT id, title FROM xlsforms
            WHERE title NOT IN
                (SELECT UNNEST(:categories));
            """
        )

        result = db.execute(sql_query, {"categories": categories_to_filter}).fetchall()

        result_dict = [{"id": row.id, "title": row.title} for row in result]

        return result_dict

    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


async def update_odk_xforms(
    task_list: list[int],
    odk_id: int,
    xform_data: BytesIO,
    form_file_ext: str,
    form_name_prefix: str,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> bool:
    """Asyncio update XForm data for each ODK Form in project.

    Args:
        task_list (List[int]): List of task IDs.
        odk_id (int): ODK Central form ID.
        xform_data (BytesIO): XForm data.
        form_file_ext (str): Extension of the form file.
        form_name_prefix (str): Prefix for the form name in ODK Central.
        odk_credentials (project_schemas.ODKCentralDecrypted): ODK Central creds.

    Returns:
        bool: True if the update is successful.
    """
    coroutines = []

    for task_id in task_list:
        coro = update_and_publish_form(
            task_id,
            odk_id,
            xform_data,
            form_file_ext,
            form_name_prefix,
            odk_credentials,
        )
        coroutines.append(coro)

    await gather(*coroutines)

    return True


async def update_and_publish_form(
    task_id: int,
    odk_id: int,
    xform_data: BytesIO,
    form_file_ext: str,
    form_name_prefix: str,
    odk_credentials: project_schemas.ODKCentralDecrypted,
) -> None:
    """Update and publish the XForm for a specific task.

    Args:
        task_id (int): Task ID.
        odk_id (int): ODK Central form ID.
        xform_data (BytesIO): XForm data.
        form_file_ext (str): Extension of the form file.
        form_name_prefix (str): Prefix for the form name in ODK Central.
        odk_credentials (project_schemas.ODKCentralDecrypted): ODK Central creds.
    """
    odk_form_name = f"{form_name_prefix}_task_{task_id}"
    xform_data = await read_and_test_xform(
        xform_data,
        form_file_ext,
        return_form_data=True,
    )
    updated_xform_data = await update_xform_info(
        xform_data,
        odk_form_name,
        f"{odk_form_name}.geojson",
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
        odk_form_name,
    )
    # The draft form must be published after upload
    xform.publishForm(odk_id, odk_form_name)


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
    # TODO xls2xform_convert requires files on disk
    # TODO create PR to accept BytesIO?

    # Read from BytesIO object
    input_content = input_data.getvalue()
    file_ext = form_file_ext.lower()

    input_path = Path(f"/tmp/fmtm_form_input_tmp{file_ext}")
    # This file will store xml contents of an xls form
    # NOTE a file on disk is required by xls2xform_convert
    output_path = Path("/tmp/fmtm_xform_temp.xml")

    if file_ext == ".xml":
        # Create output file to write to
        output_path.touch(exist_ok=True)
        # Write input_content to a temporary file
        with open(output_path, "wb") as f:
            f.write(input_content)
    else:
        # Create input file to write to
        input_path.touch(exist_ok=True)
        with open(input_path, "wb") as f:
            f.write(input_content)
        try:
            log.debug(f"Converting xlsform -> xform: {str(output_path)}")
            # FIXME should this be validate=True?
            xls2xform_convert(
                xlsform_path=str(input_path),
                xform_path=str(output_path),
                validate=False,
            )
        except Exception as e:
            log.error(e)
            msg = f"XLSForm is invalid. Possible reason: {str(e)}"
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
            ) from e

    # Parse XForm
    try:
        # TODO for memory object use ElementTree.fromstring()
        xml_parsed = ElementTree.parse(str(output_path))
        if return_form_data:
            xml_bytes = ElementTree.tostring(xml_parsed.getroot())
            return BytesIO(xml_bytes)
    except ElementTree.ParseError as e:
        log.error(e)
        msg = f"Error parsing XForm XML: Possible reason: {str(e)}"
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from e

    # Delete temp files
    if file_ext != ".xml":
        input_path.unlink()
    output_path.unlink()

    if return_form_data:
        return xml_parsed

    # Extract geojson filenames
    try:
        root = xml_parsed.getroot()
        namespaces = {"xforms": "http://www.w3.org/2002/xforms"}
        geojson_list = [
            os.path.splitext(inst.attrib["src"].split("/")[-1])[0]
            for inst in root.findall(".//xforms:instance[@src]", namespaces)
            if inst.attrib.get("src", "").endswith(".geojson")
        ]

        return {"required_media": geojson_list, "message": "Your form is valid"}

    except Exception as e:
        log.error(e)
        msg = f"Error extracting geojson filename: Possible reason: {str(e)}"
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
        ) from e


async def update_xform_info(
    form_data: BytesIO,
    form_name: str,
    geojson_file_name: str,
) -> BytesIO:
    """Update fields in the XForm to work with FMTM.

    Updated the 'id' field as the form name via the API.
    Also updates the geojson filename to match that of the uploaded media.

    Args:
        form_data (str): The input form data.
        form_file_ext (str): Extension from xls, xlsx or xml (xform).
        form_name (str): Name of the XForm to set.
        geojson_file_name (str): Name of the geojson media to set.

    Returns:
        BytesIO: The XForm data.
    """
    log.debug("Updating XML keys in XForm with data extract file & form id")

    # Namespaces definition
    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }

    # Parse the XML
    root = ElementTree.fromstring(form_data.getvalue())

    # Update id attribute to equal the form name to be generated
    xform_data = root.findall(".//xforms:data[@id]", namespaces)
    for dt in xform_data:
        dt.set("id", form_name)

    # # Update the form title if needed
    # existing_title = root.find('.//h:title', namespaces)
    # if existing_title is not None:
    #     existing_title.text = "New Title"

    # Update src attribute for instances ending with .geojson
    xform_instances = root.findall(".//xforms:instance[@src]", namespaces)
    for inst in xform_instances:
        src_value = inst.get("src", "")
        if src_value.endswith(".geojson"):
            inst.set("src", f"jr://file/{geojson_file_name}")

    return BytesIO(ElementTree.tostring(root))


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
