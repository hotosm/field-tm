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
from fastapi.logger import logger as log
from fastapi.responses import JSONResponse

# from ..odkconvert.make_data_extract import PostgresClient, OverpassClient
from ..db import database
from ..debug import debug_schemas
from ..debug.debug_crud import load_test_data_as_test_user

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
    """???."""
    return {"message": "Hello World!"}
    # raise HTTPException(status_code=404, detail="Tasks not found")


@router.get("/basemap")
def make_basemap():
    """Make a basemap of satellite imagery."""
    log.info("/debug/basemap Unimplemented!")
    return {"message": "Hello World from /debug/basemap"}


@router.get("/makecsv")
def do_odk2csv():
    """Convert the submissions data into a CSV file."""
    log.info("/debug/do_odk2csv is Unimplemented!")
    return {"message": "Hello World from /debug/makecsv"}


@router.get("/import-test-data")
def import_test_data():
    """Import the test data zips into the API.

    This endpoint should only be available during debugging, and is
    useful for first app load.

    A user with credentials test:test is created, and 5 projects are generated.
    Zips containing task and QR codes are then uploaded for each project.

    "Coulibistrie": "resilience"\n
    "Dos_D_Ane": "resilience"\n
    "Naivasha": "buildings"\n
    "Stonetown2": "buildings"\n
    "Vulamba": "buildings"
    """
    log.info("/load-test-data called")
    try:
        load_test_data_as_test_user()
        return JSONResponse(
            content={"message": "Test data upload successful"}, status_code=200
        )
    except Exception as e:
        log.error(e)
        log.error("Data import failed")
        return JSONResponse(
            content={"message": "Error during test data upload"}, status_code=409
        )
