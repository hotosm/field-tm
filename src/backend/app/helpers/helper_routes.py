# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Routes to help with common processes in the Field-TM workflow."""

import csv
import json
from io import BytesIO, StringIO
from pathlib import Path
from textwrap import dedent
from typing import Annotated
from uuid import uuid4

import requests
from fastapi import (
    APIRouter,
    Depends,
    Request,
    UploadFile,
)
from fastapi.exceptions import HTTPException
from fastapi.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from loguru import logger as log
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from osm_login_python.core import Auth
from psycopg import Connection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser
from app.auth.providers.osm import init_osm_auth
from app.central import central_deps
from app.central.central_crud import (
    convert_geojson_to_odk_csv,
    convert_odk_submission_json_to_geojson,
)
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.database import db_conn
from app.db.enums import HTTPStatus, XLSFormType
from app.db.postgis_utils import (
    add_required_geojson_properties,
    featcol_keep_single_geom_type,
    flatgeobuf_to_featcol,
    javarosa_to_geojson_geom,
    multigeom_to_singlegeom,
    parse_geojson_file_to_featcol,
)
from app.helpers.helper_crud import send_email

router = APIRouter(
    prefix="/helper",
    tags=["helper"],
    responses={404: {"description": "Not found"}},
)


@router.get("/download-template-xlsform")
async def download_template(
    form_type: XLSFormType,
):
    """Download example XLSForm from Field-TM."""
    form_filename = XLSFormType(form_type).name
    xlsform_path = f"{xlsforms_path}/{form_filename}.yaml"
    xlsx_bytes = convert_to_xlsform(str(xlsform_path))
    if xlsx_bytes:
        return StreamingResponse(
            xlsx_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f"attachment; filename={form_filename}.xlsx"
            },
        )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Failed to convert YAML form to XLSForm.",
        )


@router.get("/convert-fgb-to-geojson")
async def convert_fgb_to_geojson(
    url: str,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Convert flatgeobuf to GeoJSON format, extracting GeometryCollection.

    Helper endpoint to test data extracts during project creation.
    Required as the flatgeobuf files wrapped in GeometryCollection
    cannot be read in QGIS or other tools.

    Args:
        url (str): URL to the flatgeobuf file.
        db (Connection): The database connection.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    with requests.get(url) as response:
        if not response.ok:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Download failed for data extract",
            )
        data_extract_geojson = await flatgeobuf_to_featcol(db, response.content)

    if not data_extract_geojson:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=("Failed to convert flatgeobuf --> geojson"),
        )

    headers = {
        "Content-Disposition": ("attachment; filename=fmtm_data_extract.geojson"),
        "Content-Type": "application/media",
    }

    return Response(content=json.dumps(data_extract_geojson), headers=headers)


@router.post("/append-geojson-properties")
async def append_required_geojson_properties(
    geojson: UploadFile,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Append required properties to a GeoJSON file.

    The required properties for Field-TM are:
    - "id"
    - "osm_id"
    - "tags"
    - "version"
    - "changeset"
    - "timestamp"

    These are added automatically if missing during the project creation workflow.
    However it may be useful to run your file through this endpoint to validation.
    """
    featcol = parse_geojson_file_to_featcol(await geojson.read())
    if not featcol:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="No geometries present"
        )
    featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

    if featcol_single_geom_type:
        processed_featcol = add_required_geojson_properties(featcol_single_geom_type)
        headers = {
            "Content-Disposition": ("attachment; filename=geojson_withtags.geojson"),
            "Content-Type": "application/media",
        }
        return Response(content=json.dumps(processed_featcol), headers=headers)

    raise HTTPException(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        detail="Your geojson file is invalid.",
    )


@router.post("/convert-geojson-to-odk-csv")
async def convert_geojson_to_odk_csv_wrapper(
    geojson: UploadFile,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Convert GeoJSON upload media to ODK CSV upload media."""
    filename = Path(geojson.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json", ".geojson"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Provide a valid .json or .geojson file",
        )

    contents = await geojson.read()
    feature_csv = await convert_geojson_to_odk_csv(BytesIO(contents))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.csv"}
    return Response(feature_csv.getvalue(), headers=headers)


@router.post("/create-entities-from-csv")
async def create_entities_from_csv(
    csv_file: UploadFile,
    odk_project_id: int,
    entity_name: str,
    current_user: Annotated[AuthUser, Depends(login_required)],
    odk_creds: ODKCentral = Depends(),
):
    """Upload a CSV file to create new ODK Entities in a project.

    The Entity must already be defined on the server.
    The CSV fields must match the Entity fields.
    """
    filename = Path(csv_file.filename)
    file_ext = filename.suffix.lower()

    if file_ext != ".csv":
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Provide a valid .csv"
        )

    def parse_csv(csv_bytes):
        parsed_data = []
        csv_str = csv_bytes.decode("utf-8")
        csv_reader = csv.DictReader(StringIO(csv_str))
        for row in csv_reader:
            parsed_data.append(dict(row))
        return parsed_data

    parsed_data = parse_csv(await csv_file.read())
    entities_data_dict = {str(uuid4()): data for data in parsed_data}

    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        entities = await odk_central.createEntities(
            odk_project_id,
            entity_name,
            entities_data_dict,
        )

    return entities


@router.post("/javarosa-geom-to-geojson")
async def convert_javarosa_geom_to_geojson(
    javarosa_string: str,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Convert a JavaRosa geometry string to GeoJSON."""
    return await javarosa_to_geojson_geom(javarosa_string)


@router.post("/convert-odk-submission-json-to-geojson")
async def convert_odk_submission_json_to_geojson_wrapper(
    json_file: UploadFile,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Convert the ODK submission output JSON to GeoJSON.

    The submission JSON be downloaded via ODK Central, or osm-fieldwork.
    The logic works with the standardised XForm form fields from osm-fieldwork.
    """
    filename = Path(json_file.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Provide a valid .json file"
        )

    contents = await json_file.read()
    submission_geojson = await convert_odk_submission_json_to_geojson(BytesIO(contents))
    submission_data = BytesIO(json.dumps(submission_geojson).encode("utf-8"))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.geojson"}
    return Response(submission_data.getvalue(), headers=headers)


@router.get("/view-raw-data-api-token")
async def get_raw_data_api_osm_token(
    request: Request,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get the OSM OAuth token for a service account for raw-data-api.

    The token returned by this endpoint should be used for the
    RAW_DATA_API_AUTH_TOKEN environment variable.
    """
    response = requests.get(f"{settings.RAW_DATA_API_URL}/auth/login")
    if not response.ok:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not login to raw-data-api",
        )

    raw_api_login_url = response.json().get("login_url")
    return RedirectResponse(raw_api_login_url)


@router.get("/view-field-tm-api-token")
async def view_user_oauth_token(
    request: Request,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get the Field-TM OSM (OAuth) token for a logged in user.

    The token is encrypted with a secret key and only usable via
    this Field-TM instance and the osm-login-python module.
    """
    cookie_name = settings.cookie_name
    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"access_token": request.cookies.get(cookie_name)},
    )


@router.post("/multipolygons-to-polygons")
async def flatten_multipolygons_to_polygons(
    geojson: UploadFile,
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """If any MultiPolygons are present, replace with multiple Polygons."""
    featcol = parse_geojson_file_to_featcol(await geojson.read())
    if not featcol:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="No geometries present"
        )
    multi_to_single_polygons = multigeom_to_singlegeom(featcol)

    if multi_to_single_polygons:
        headers = {
            "Content-Disposition": ("attachment; filename=flattened_polygons.geojson"),
            "Content-Type": "application/media",
        }
        return Response(content=json.dumps(multi_to_single_polygons), headers=headers)

    raise HTTPException(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        detail="Your geojson file is invalid.",
    )


@router.post("/send-test-osm-message")
async def send_test_osm_message(
    request: Request,
    current_user: Annotated[AuthUser, Depends(login_required)],
    # NOTE this is duplicated to access the 'deserialize_data' method
    osm_auth: Annotated[Auth, Depends(init_osm_auth)],
):
    """Sends a test message to currently logged in OSM user."""
    cookie_name = f"{settings.cookie_name}_osm"
    log.debug(f"Extracting OSM token from cookie {cookie_name}")
    serialised_osm_token = request.cookies.get(cookie_name)
    if not serialised_osm_token:
        return HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="You must be logged in to your OpenStreetMap account.",
        )

    # NOTE to get this far, the user must be logged in using OSM
    osm_token = osm_auth.deserialize_data(serialised_osm_token)
    # NOTE message content must be in markdown format
    message_content = dedent("""
        # Heading 1

        ## Heading 2

        Hello there!

        This is a text message in markdown format.

        > Notes section
    """)
    # NOTE post body should contain either recipient or recipient_id
    post_body = {
        "recipient_id": 16289154,
        # "recipient_id": current_user.id,
        "title": "Test message from Field-TM!",
        "body": message_content,
    }

    email_url = f"{settings.OSM_URL}api/0.6/user/messages"
    headers = {"Authorization": f"Bearer {osm_token}"}
    log.debug(f"Sending message to user ({current_user.sub}) via OSM API: {email_url}")
    response = requests.post(email_url, headers=headers, data=post_body)

    if response.status_code == 200:
        log.info("Message sent successfully")
    else:
        msg = "Sending message via OSM failed"
        log.error(f"{msg}: {response.text}")
        return HTTPException(status_code=HTTPStatus.CONFLICT, detail=msg)

    return Response(status_code=HTTPStatus.OK)


@router.post("/send-test-email")
async def send_test_email(user_emails: list[str]):
    """Sends a test email using real SMTP settings."""
    log.info(f"Sending test email to recipients: {user_emails}")
    await send_email(
        user_emails=user_emails,
        title="Test email from Field-TM",
        message_content="This is a test email sent from Field-TM.",
    )
    return Response(
        status_code=HTTPStatus.OK,
    )
