# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
"""Routes to help with common processes in the FMTM workflow."""

import json
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
)
from fastapi.exceptions import HTTPException
from fastapi.responses import Response

from app.auth.osm import AuthUser, login_required
from app.central.central_crud import (
    convert_geojson_to_odk_csv,
    convert_odk_submission_json_to_geojson,
    read_and_test_xform,
)
from app.db.postgis_utils import (
    add_required_geojson_properties,
    javarosa_to_geojson_geom,
    parse_and_filter_geojson,
)
from app.models.enums import GeometryType, HTTPStatus

router = APIRouter(
    prefix="/helper",
    tags=["helper"],
    responses={404: {"description": "Not found"}},
)


@router.post("/append-geojson-properties")
async def append_required_geojson_properties(
    geojson: UploadFile,
    current_user: AuthUser = Depends(login_required),
):
    """Append required properties to a GeoJSON file.

    The required properties for FMTM are:
    - "id"
    - "osm_id"
    - "tags"
    - "version"
    - "changeset"
    - "timestamp"

    These are added automatically if missing during the project creation workflow.
    However it may be useful to run your file through this endpoint to validation.
    """
    featcol = parse_and_filter_geojson(await geojson.read())
    if featcol:
        processed_featcol = add_required_geojson_properties(featcol)
        headers = {
            "Content-Disposition": ("attachment; filename=geojson_withtags.geojson"),
            "Content-Type": "application/media",
        }
        return Response(content=json.dumps(processed_featcol), headers=headers)

    raise HTTPException(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        detail="Your geojson file is invalid.",
    )


@router.post("/convert-xlsform-to-xform")
async def convert_xlsform_to_xform(
    xlsform: UploadFile,
    current_user: AuthUser = Depends(login_required),
):
    """Convert XLSForm to XForm XML."""
    filename = Path(xlsform.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".xls", ".xlsx"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Provide a valid .xls or .xlsx file"
        )

    contents = await xlsform.read()
    xform_data = await read_and_test_xform(
        BytesIO(contents), file_ext, return_form_data=True
    )

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.xml"}
    return Response(xform_data.getvalue(), headers=headers)


@router.post("/convert-geojson-to-odk-csv")
async def convert_geojson_to_odk_csv_wrapper(
    geojson: UploadFile,
    current_user: AuthUser = Depends(login_required),
):
    """Convert GeoJSON upload media to ODK CSV upload media."""
    filename = Path(geojson.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json", ".geojson"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Provide a valid .json or .geojson file"
        )

    contents = await geojson.read()
    feature_csv = await convert_geojson_to_odk_csv(BytesIO(contents))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.csv"}
    return Response(feature_csv.getvalue(), headers=headers)


@router.post("/javarosa-geom-to-geojson")
async def convert_javarosa_geom_to_geojson(
    javarosa_string: str,
    geometry_type: GeometryType,
    current_user: AuthUser = Depends(login_required),
):
    """Convert a JavaRosa geometry string to GeoJSON."""
    return await javarosa_to_geojson_geom(javarosa_string, geometry_type)


@router.post("/convert-odk-submission-json-to-geojson")
async def convert_odk_submission_json_to_geojson_wrapper(
    json_file: UploadFile,
    current_user: AuthUser = Depends(login_required),
):
    """Convert the ODK submission output JSON to GeoJSON.

    The submission JSON be downloaded via ODK Central, or osm-fieldwork.
    The logic works with the standardised XForm form fields from osm-fieldwork.
    """
    filename = Path(json_file.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .json file")

    contents = await json_file.read()
    submission_geojson = await convert_odk_submission_json_to_geojson(BytesIO(contents))

    headers = {"Content-Disposition": f"attachment; filename={filename.stem}.geojson"}
    return Response(submission_geojson.getvalue(), headers=headers)
