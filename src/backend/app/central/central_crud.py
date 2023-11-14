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
import base64
import json
import os
import pathlib
import zlib

# import osm_fieldwork
# Qr code imports
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from loguru import logger as log
from osm_fieldwork.CSVDump import CSVDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.xls2xform import xls2xform_convert
from sqlalchemy.orm import Session

from ..config import settings
from ..db import db_models
from ..projects import project_schemas


def get_odk_project(odk_central: project_schemas.ODKCentral = None):
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
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return project


def get_odk_form(odk_central: project_schemas.ODKCentral = None):
    """Helper function to get the OdkForm with credentials."""
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
        form = OdkForm(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def get_odk_app_user(odk_central: project_schemas.ODKCentral = None):
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


def list_odk_projects(odk_central: project_schemas.ODKCentral = None):
    """List all projects on a remote ODK Server."""
    project = get_odk_project(odk_central)
    return project.listProjects()


def create_odk_project(name: str, odk_central: project_schemas.ODKCentral = None):
    """Create a project on a remote ODK Server."""
    project = get_odk_project(odk_central)

    try:
        log.debug("Attempting ODKCentral project creation")
        result = project.createProject(name)

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


def delete_odk_project(project_id: int, odk_central: project_schemas.ODKCentral = None):
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


def create_appuser(
    project_id: int, name: str, odk_credentials: project_schemas.ODKCentral = None
):
    """Create an app-user on a remote ODK Server.

    If odk credentials of the project are provided, use them to create an app user.
    """
    if odk_credentials:
        url = odk_credentials.odk_central_url
        user = odk_credentials.odk_central_user
        pw = odk_credentials.odk_central_password

    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    app_user = OdkAppUser(url, user, pw)

    log.debug(
        "ODKCentral: attempting user creation: name: " f"{name} | project: {project_id}"
    )
    result = app_user.create(project_id, name)

    log.debug(f"ODKCentral response: {result.json()}")
    return result


def delete_app_user(
    project_id: int, name: str, odk_central: project_schemas.ODKCentral = None
):
    """Delete an app-user from a remote ODK Server."""
    appuser = get_odk_app_user(odk_central)
    result = appuser.delete(project_id, name)
    return result


def upload_xform_media(
    project_id: int, xform_id: str, filespec: str, odk_credentials: dict = None
):
    title = os.path.basename(os.path.splitext(filespec)[0])

    if odk_credentials:
        url = odk_credentials["odk_central_url"]
        user = odk_credentials["odk_central_user"]
        pw = odk_credentials["odk_central_password"]

    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        xform = OdkForm(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.uploadMedia(project_id, title, filespec)
    result = xform.publishForm(project_id, title)
    return result


def create_odk_xform(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_credentials: project_schemas.ODKCentral = None,
    create_draft: bool = False,
    upload_media=True,
    convert_to_draft_when_publishing=True,
):
    """Create an XForm on a remote ODK Central server."""
    title = os.path.basename(os.path.splitext(filespec)[0])
    # result = xform.createForm(project_id, title, filespec, True)
    # Pass odk credentials of project in xform

    if not odk_credentials:
        odk_credentials = project_schemas.ODKCentral(
            odk_central_url=settings.ODK_CENTRAL_URL,
            odk_central_user=settings.ODK_CENTRAL_USER,
            odk_central_password=settings.ODK_CENTRAL_PASSWD,
        )
    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.createForm(project_id, xform_id, filespec, create_draft)

    if result != 200 and result != 409:
        return result
    data = f"/tmp/{title}.geojson"

    # This modifies an existing published XForm to be in draft mode.
    # An XForm must be in draft mode to upload an attachment.
    if upload_media:
        result = xform.uploadMedia(
            project_id, title, data, convert_to_draft_when_publishing
        )

    result = xform.publishForm(project_id, title)
    return result


def delete_odk_xform(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
):
    """Delete an XForm from a remote ODK Central server."""
    xform = get_odk_form(odk_central)
    result = xform.deleteForm(project_id, xform_id, filespec, True)
    # FIXME: make sure it's a valid project id
    return result


def list_odk_xforms(
    project_id: int,
    odk_central: project_schemas.ODKCentral = None,
    metadata: bool = False,
):
    """List all XForms in an ODK Central project."""
    project = get_odk_project(odk_central)
    xforms = project.listForms(project_id, metadata)
    # FIXME: make sure it's a valid project id
    return xforms


def get_form_full_details(
    odk_project_id: int, form_id: str, odk_central: project_schemas.ODKCentral
):
    form = get_odk_form(odk_central)
    form_details = form.getFullDetails(odk_project_id, form_id)
    return form_details


async def get_odk_project_full_details(
    odk_project_id: int, odk_central: project_schemas.ODKCentral
):
    project = get_odk_project(odk_central)
    project_details = project.getFullDetails(odk_project_id)
    return project_details


def list_task_submissions(
    odk_project_id: int, form_id: str, odk_central: project_schemas.ODKCentral = None
):
    project = get_odk_form(odk_central)
    submissions = project.listSubmissions(odk_project_id, form_id)
    return submissions


def list_submissions(project_id: int, odk_central: project_schemas.ODKCentral = None):
    """List submissions from a remote ODK server."""
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
        forms = (
            db.query(db_models.DbXForm.id, db_models.DbXForm.title)
            .offset(skip)
            .limit(limit)
            .all()
        )

        result_dict = []
        for form in forms:
            form_dict = {
                "id": form[0],  # Assuming the first element is the ID
                "title": form[1],  # Assuming the second element is the title
            }
            result_dict.append(form_dict)

        return result_dict

    except Exception as e:
        log.error(e)
        raise HTTPException(e) from e


def download_submissions(
    project_id: int,
    xform_id: str,
    submission_id: str = None,
    get_json: bool = True,
    odk_central: project_schemas.ODKCentral = None,
):
    """Download submissions from a remote ODK server."""
    xform = get_odk_form(odk_central)
    # FIXME: should probably filter by timestamps or status value
    data = xform.getSubmissions(project_id, xform_id, submission_id, True, get_json)
    fixed = str(data, "utf-8")
    return fixed.splitlines()


async def test_form_validity(xform_content: str, form_type: str):
    """Validate an XForm.
    Parameters:
        xform_content: form to be tested
        form_type: type of form (xls or xlsx).
    """
    try:
        xlsform_path = f"/tmp/validate_form.{form_type}"
        outfile = "/tmp/outfile.xml"

        with open(xlsform_path, "wb") as f:
            f.write(xform_content)

        xls2xform_convert(xlsform_path=xlsform_path, xform_path=outfile, validate=False)

        namespaces = {
            "h": "http://www.w3.org/1999/xhtml",
            "odk": "http://www.opendatakit.org/xforms",
            "xforms": "http://www.w3.org/2002/xforms",
        }

        import xml.etree.ElementTree as ET

        with open(outfile, "r") as xml:
            data = xml.read()

        root = ET.fromstring(data)
        instances = root.findall(".//xforms:instance[@src]", namespaces)

        geojson_list = []
        for inst in instances:
            try:
                if "src" in inst.attrib:
                    if (inst.attrib["src"].split("."))[1] == "geojson":
                        parts = (inst.attrib["src"].split("."))[0].split("/")
                        geojson_name = parts[-1]
                        geojson_list.append(geojson_name)
            except Exception:
                continue
        return {"required media": geojson_list, "message": "Your form is valid"}
    except Exception as e:
        return JSONResponse(
            content={"message": "Your form is invalid", "possible_reason": str(e)},
            status_code=400,
        )


def generate_updated_xform(
    xlsform: str,
    xform: str,
    form_type: str,
):
    """Update the version in an XForm so it's unique."""
    name = os.path.basename(xform).replace(".xml", "")
    outfile = xform

    log.debug(f"Reading xlsform: {xlsform}")
    if form_type != "xml":
        try:
            xls2xform_convert(xlsform_path=xlsform, xform_path=outfile, validate=False)
        except Exception as e:
            log.error(f"Couldn't convert {xlsform} to an XForm!", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e

        if os.path.getsize(outfile) <= 0:
            log.warning(f"{outfile} is empty!")
            raise HTTPException(status=400, detail=f"{outfile} is empty!") from None

        xls = open(outfile, "r")
        data = xls.read()
        xls.close()
    else:
        xls = open(xlsform, "r")
        data = xls.read()
        xls.close()

    tmp = name.split("_")
    tmp[0]
    tmp[1]
    id = tmp[2].split(".")[0]
    extract = f"jr://file/{name}.geojson"

    # # Parse the XML to geojson
    # xml = xmltodict.parse(str(data))

    # # First change the osm data extract file
    # index = 0
    # for inst in xml["h:html"]["h:head"]["model"]["instance"]:
    #     try:
    #         if "@src" in inst:
    #             if (
    #                 xml["h:html"]["h:head"]["model"]["instance"][index]["@src"].split(
    #                     "."
    #                 )[1]
    #                 == "geojson"
    #             ):
    #                 xml["h:html"]["h:head"]["model"]["instance"][index][
    #                     "@src"
    #                 ] = extract

    #         if "data" in inst:
    #             print("data in inst")
    #             if "data" == inst:
    #                 print("Data = inst ", inst)
    #                 xml["h:html"]["h:head"]["model"]["instance"]["data"]["@id"] = id
    #                 # xml["h:html"]["h:head"]["model"]["instance"]["data"]["@id"] = xform
    #             else:
    #                 xml["h:html"]["h:head"]["model"]["instance"][0]["data"]["@id"] = id
    #     except Exception:
    #         continue
    #     index += 1
    # xml["h:html"]["h:head"]["h:title"] = name

    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }

    import xml.etree.ElementTree as ET

    root = ET.fromstring(data)
    head = root.find("h:head", namespaces)
    model = head.find("xforms:model", namespaces)
    instances = model.findall("xforms:instance", namespaces)

    index = 0
    for inst in instances:
        try:
            if "src" in inst.attrib:
                if (inst.attrib["src"].split("."))[1] == "geojson":
                    (inst.attrib)["src"] = extract

            # Looking for data tags
            data_tags = inst.findall("xforms:data", namespaces)
            if data_tags:
                for dt in data_tags:
                    dt.attrib["id"] = id
        except Exception:
            continue
        index += 1

    # Save the modified XML
    newxml = ET.tostring(root)

    # write the updated XML file
    outxml = open(outfile, "w")
    # newxml = xmltodict.unparse(xml)
    outxml.write(newxml.decode())
    outxml.close()

    # insert the new version
    # forms = table(
    #     "xlsforms", column("title"), column("xls"), column("xml"), column("id")
    # )
    # ins = insert(forms).values(title=name, xml=data)
    # sql = ins.on_conflict_do_update(
    #     constraint="xlsforms_title_key", set_=dict(title=name, xml=newxml)
    # )
    # db.execute(sql)
    # db.commit()

    return outfile


def create_qrcode(project_id: int, token: str, name: str, odk_central_url: str = None):
    """Create the QR Code for an app-user."""
    if not odk_central_url:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        odk_central_url = settings.ODK_CENTRAL_URL

    # Qr code text json in the format acceptable by odk collect.
    qr_code_setting = {
        "general": {
            "server_url": f"{odk_central_url}/v1/key/{token}/projects/{project_id}",
            "form_update_mode": "match_exactly",
            "basemap_source": "osm",
            "autosend": "wifi_and_cellular",
        },
        "project": {"name": f"{name}"},
        "admin": {},
    }

    # Base64 encoded
    qr_data = base64.b64encode(
        zlib.compress(json.dumps(qr_code_setting).encode("utf-8"))
    )
    return qr_data


def upload_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    xform.uploadMedia(project_id, xform_id, filespec)


def download_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
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
    pathlib.Path(osm_fieldwork.__file__).resolve().parent
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


def create_odk_xform_for_janakpur(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_credentials: project_schemas.ODKCentral = None,
    create_draft: bool = False,
    upload_media=True,
    convert_to_draft_when_publishing=True,
):
    """Create an XForm on a remote ODK Central server."""
    title = os.path.basename(os.path.splitext(filespec)[0])
    # result = xform.createForm(project_id, title, filespec, True)
    # Pass odk credentials of project in xform

    if not odk_credentials:
        odk_credentials = project_schemas.ODKCentral(
            odk_central_url=settings.ODK_CENTRAL_URL,
            odk_central_user=settings.ODK_CENTRAL_USER,
            odk_central_password=settings.ODK_CENTRAL_PASSWD,
        )
    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.createForm(project_id, xform_id, filespec, create_draft)

    if result != 200 and result != 409:
        return result

    # This modifies an existing published XForm to be in draft mode.
    # An XForm must be in draft mode to upload an attachment.
    if upload_media:
        # Upload buildings file
        building_file = f"/tmp/buildings_{title}.geojson"

        result = xform.uploadMedia(
            project_id, title, building_file, convert_to_draft_when_publishing
        )

        # Upload roads file
        road_file = f"/tmp/roads_{title}.geojson"
        result = xform.uploadMedia(
            project_id, title, road_file, convert_to_draft_when_publishing
        )

    result = xform.publishForm(project_id, title)
    return result


def generate_updated_xform_for_janakpur(
    xlsform: str,
    xform: str,
    form_type: str,
):
    """Update the version in an XForm so it's unique."""
    name = os.path.basename(xform).replace(".xml", "")

    log.debug(f"Name in form = {name}")

    outfile = xform
    if form_type != "xml":
        try:
            xls2xform_convert(xlsform_path=xlsform, xform_path=outfile, validate=False)
        except Exception as e:
            log.error(f"Couldn't convert {xlsform} to an XForm!", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e

        if os.path.getsize(outfile) <= 0:
            log.warning(f"{outfile} is empty!")
            raise HTTPException(status=400, detail=f"{outfile} is empty!") from None

        xls = open(outfile, "r")
        data = xls.read()
        xls.close()
    else:
        xls = open(xlsform, "r")
        data = xls.read()
        xls.close()

    tmp = name.split("_")
    tmp[0]
    tmp[1]
    id = tmp[2].split(".")[0]

    buildings_extract = f"jr://file/buildings_{name}.geojson"
    roads_extract = f"jr://file/roads_{name}.geojson"

    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }

    import xml.etree.ElementTree as ET

    root = ET.fromstring(data)
    head = root.find("h:head", namespaces)
    model = head.find("xforms:model", namespaces)
    instances = model.findall("xforms:instance", namespaces)

    index = 0
    for inst in instances:
        try:
            if "src" in inst.attrib:
                print("SRC = Present")
                if (inst.attrib["src"]) == "jr://file/buildings.geojson":  # FIXME
                    print("INST attribs = ", inst.attrib["src"])
                    inst.attrib["src"] = buildings_extract

                if (inst.attrib["src"]) == "jr://file/roads.geojson":  # FIXME
                    inst.attrib["src"] = roads_extract

            # Looking for data tags
            data_tags = inst.findall("xforms:data", namespaces)
            if data_tags:
                for dt in data_tags:
                    dt.attrib["id"] = id
        except Exception:
            continue
        index += 1

    # Save the modified XML
    newxml = ET.tostring(root)

    # write the updated XML file
    outxml = open(outfile, "w")
    outxml.write(newxml.decode())
    outxml.close()

    return outfile
