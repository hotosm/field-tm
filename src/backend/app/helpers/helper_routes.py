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
"""Routes to help with common processes in the Field-TM workflow (Litestar)."""

import csv
import json
import logging
from io import BytesIO, StringIO
from pathlib import Path
from textwrap import dedent
from uuid import uuid4

import requests
from geojson_aoi import parse_aoi
from litestar import Request, Response, Router, get, post
from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.exceptions import HTTPException
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import xlsforms_path
from osm_login_python.core import Auth

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
from app.db.enums import XLSFormType
from app.helpers.geometry_utils import (
    javarosa_to_geojson_geom,
    multigeom_to_singlegeom,
)

log = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 30


@get(
    "/download-template-xlsform",
)
async def download_template(
    form_type: XLSFormType,
) -> Response[bytes]:
    """Download example XLSForm from Field-TM."""
    form_filename = XLSFormType(form_type).name
    form_path = f"{xlsforms_path}/{form_filename}.yaml"
    xlsx_bytes = convert_to_xlsform(str(form_path))
    if xlsx_bytes:
        return Response(
            content=xlsx_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f"attachment; filename={form_filename}.xlsx"
            },
            status_code=status.HTTP_200_OK,
        )
    msg = "Failed to convert YAML form to XLSForm."
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=msg,
    )


@post(
    "/convert-geojson-to-odk-csv",
    dependencies={"current_user": Provide(login_required)},
)
async def convert_geojson_to_odk_csv_wrapper(
    geojson: UploadFile,
    current_user: AuthUser,
) -> Response[bytes]:
    """Convert GeoJSON upload media to ODK CSV upload media."""
    filename = Path(geojson.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json", ".geojson"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a valid .json or .geojson file",
        )

    contents = await geojson.read()
    feature_csv = await convert_geojson_to_odk_csv(BytesIO(contents))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.csv"}
    return Response(
        feature_csv.getvalue(),
        headers=headers,
        status_code=status.HTTP_200_OK,
    )


@post(
    "/create-entities-from-csv",
    dependencies={
        "current_user": Provide(login_required),
    },
)
async def create_entities_from_csv(
    csv_file: UploadFile,
    odk_project_id: int,
    entity_name: str,
    current_user: AuthUser,
    odk_creds: ODKCentral,
) -> dict:
    """Upload a CSV file to create new ODK Entities in a project.

    The Entity must already be defined on the server.
    The CSV fields must match the Entity fields.
    """
    filename = Path(csv_file.filename)
    file_ext = filename.suffix.lower()

    if file_ext != ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a valid .csv",
        )

    def parse_csv(csv_bytes: bytes):
        csv_str = csv_bytes.decode("utf-8")
        csv_reader = csv.DictReader(StringIO(csv_str))
        return [dict(row) for row in csv_reader]

    parsed_data = parse_csv(await csv_file.read())
    entities_data_dict = {str(uuid4()): data for data in parsed_data}

    async with central_deps.get_odk_dataset(odk_creds) as odk_central:
        create_success = await odk_central.createEntities(
            odk_project_id,
            entity_name,
            entities_data_dict,
        )

    # Response: {"success": true}
    return create_success


@post(
    "/javarosa-geom-to-geojson",
    dependencies={"current_user": Provide(login_required)},
)
async def convert_javarosa_geom_to_geojson(
    javarosa_string: str,
    current_user: AuthUser,
) -> dict:
    """Convert a JavaRosa geometry string to GeoJSON."""
    return await javarosa_to_geojson_geom(javarosa_string)


@post(
    "/convert-odk-submission-json-to-geojson",
    dependencies={"current_user": Provide(login_required)},
)
async def convert_odk_submission_json_to_geojson_wrapper(
    json_file: UploadFile,
    current_user: AuthUser,
) -> Response[bytes]:
    """Convert the ODK submission output JSON to GeoJSON.

    The submission JSON be downloaded via ODK Central, or osm-fieldwork.
    The logic works with the standardised XForm form fields from osm-fieldwork.
    """
    filename = Path(json_file.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a valid .json file",
        )

    contents = await json_file.read()
    submission_geojson = await convert_odk_submission_json_to_geojson(BytesIO(contents))
    submission_data = BytesIO(json.dumps(submission_geojson).encode("utf-8"))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.geojson"}
    return Response(
        submission_data.getvalue(),
        headers=headers,
        status_code=status.HTTP_200_OK,
    )


@get(
    "/view-raw-data-api-token",
    dependencies={"current_user": Provide(login_required)},
)
async def get_raw_data_api_osm_token(
    request: Request,
    current_user: AuthUser,
) -> Response[None]:
    """Get the OSM OAuth token for a service account for raw-data-api.

    The token returned by this endpoint should be used for the
    RAW_DATA_API_AUTH_TOKEN environment variable.
    """
    response = requests.get(
        f"{settings.RAW_DATA_API_URL}/auth/login",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not login to raw-data-api",
        )

    raw_api_login_url = response.json().get("login_url")
    return Response(
        content=b"",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": raw_api_login_url},
    )


@get(
    "/view-field-tm-api-token",
    dependencies={"current_user": Provide(login_required)},
)
async def view_user_oauth_token(
    request: Request,
    current_user: AuthUser,
) -> dict[str, str | None]:
    """Get the Field-TM OSM (OAuth) token for a logged in user.

    The token is encrypted with a secret key and only usable via
    this Field-TM instance and the osm-login-python module.
    """
    cookie_name = settings.cookie_name
    return {"access_token": request.cookies.get(cookie_name)}


@post(
    "/multipolygons-to-polygons",
    dependencies={"current_user": Provide(login_required)},
)
async def flatten_multipolygons_to_polygons(
    geojson: UploadFile,
    current_user: AuthUser,
) -> Response[bytes]:
    """If any MultiPolygons are present, replace with multiple Polygons."""
    featcol = parse_aoi(settings.FMTM_DB_URL, await geojson.read())
    if not featcol:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No geometries present",
        )
    multi_to_single_polygons = multigeom_to_singlegeom(featcol)

    if multi_to_single_polygons:
        headers = {
            "Content-Disposition": ("attachment; filename=flattened_polygons.geojson"),
            "Content-Type": "application/media",
        }
        return Response(
            content=json.dumps(multi_to_single_polygons).encode("utf-8"),
            headers=headers,
            status_code=status.HTTP_200_OK,
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Your geojson file is invalid.",
    )


@post(
    "/send-test-osm-message",
    dependencies={
        "current_user": Provide(login_required),
        "osm_auth": Provide(init_osm_auth),
    },
    status_code=status.HTTP_200_OK,
)
async def send_test_osm_message(
    request: Request,
    current_user: AuthUser,
    # NOTE this is duplicated to access the 'deserialize_data' method
    osm_auth: Auth,
) -> None:
    """Sends a test message to currently logged in OSM user."""
    cookie_name = f"{settings.cookie_name}_osm"
    log.debug(f"Extracting OSM token from cookie {cookie_name}")
    serialised_osm_token = request.cookies.get(cookie_name)
    if not serialised_osm_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in to your OpenStreetMap account.",
        )

    # NOTE to get this far, the user must be logged in using OSM
    osm_token = osm_auth.deserialize_data(serialised_osm_token)
    # NOTE message content must be in markdown format
    message_content = dedent(
        """
        # Heading 1

        ## Heading 2

        Hello there!

        This is a text message in markdown format.

        > Notes section
    """
    )
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
    response = requests.post(
        email_url,
        headers=headers,
        data=post_body,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == status.HTTP_200_OK:
        log.info("Message sent successfully")
        return None

    msg = "Sending message via OSM failed"
    log.error(f"{msg}: {response.text}")
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=msg,
    )


helper_router = Router(
    path="/helper",
    tags=["helper"],
    route_handlers=[
        download_template,
        convert_geojson_to_odk_csv_wrapper,
        create_entities_from_csv,
        convert_javarosa_geom_to_geojson,
        convert_odk_submission_json_to_geojson_wrapper,
        get_raw_data_api_osm_token,
        view_user_oauth_token,
        flatten_multipolygons_to_polygons,
        send_test_osm_message,
    ],
)
