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

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
)
from fastapi.exceptions import HTTPException
from fastapi.responses import Response

from app.auth.osm import AuthUser, login_required
from app.db.postgis_utils import (
    add_required_geojson_properties,
    parse_and_filter_geojson,
)
from app.models.enums import HTTPStatus

router = APIRouter(
    prefix="/helper",
    tags=["helper"],
    responses={404: {"description": "Not found"}},
)


@router.post("/validate-data-extract")
async def download_features(
    geojson: UploadFile,
    current_user: AuthUser = Depends(login_required),
):
    """Validate and append tags to data extract geojson.

    Args:
        geojson (UploadFile): The GeoJSON file.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: The HTTP response object containing the downloaded file.
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
