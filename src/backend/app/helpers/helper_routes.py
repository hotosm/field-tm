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
