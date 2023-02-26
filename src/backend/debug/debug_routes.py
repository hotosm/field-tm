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

from fastapi import APIRouter, Depends
from fastapi.logger import logger as logger

# from ..odkconvert.make_data_extract import PostgresClient, OverpassClient

from ..db import database
from ..debug import debug_schemas


router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

#
# These are temporary debugging endpoints so it's possible to
# call directly into the backend support code. As that code is
# more developed, then these will be called by other endpoints,
# and not directly.
#


@router.get("/", response_model=debug_schemas.DebugOut)
async def debug():
    return {"message": "Hello World!"}
    # raise HTTPException(status_code=404, detail="Tasks not found")


@router.get("/basemap")
def make_basemap():
    """Make a basemap of satellite imagery"""
    logger.info("/debug/basemap Unimplemented!")
    return {"message": "Hello World from /debug/basemap"}


@router.get("/makecsv")
def do_odk2csv():
    """Convert the submissions data into a CSV file"""
    logger.info("/debug/do_odk2csv is Unimplemented!")
    return {"message": "Hello World from /debug/makecsv"}

