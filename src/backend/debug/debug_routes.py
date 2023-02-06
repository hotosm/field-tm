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

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
import logging.config
from fastapi.logger import logger as logger
from ..db import database
from ..models.enums import TaskStatus
from ..debug import debug_schemas, debug_crud
from ..tasks import tasks_schemas, tasks_crud
from ..central import central_schemas, central_crud
from ..db import db_models


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
    #raise HTTPException(status_code=404, detail="Tasks not found")

@router.get("/makeqr")
def make_qrcode(project_id=None,
                token=None,
                project_name=None,
                db: Session = Depends(database.get_db),
):
    """Make a QR code for an app_user"""
    logger.info("/debug/makeqr is Unimplemented!")
    qrcode = central_crud.create_QRCode(project_id, token, project_name)
    qrdb = db_models.DbQrCode(image=qrcode, )
    db.add(qrdb)
    db.commit()
    logger.info("/debug/makeqr is partially implemented!")
    # TODO: write to qr_code table
    return {"data": qrcode}

@router.get("/makedata")
def make_data_extract():
    """Extract data from OSM"""
    logger.info("/debug/makedata is Unimplemented!")
    return {"message": "Hello World from /debug/makedata"}

@router.get("/basemap")
def make_basemap():
    """Make a basemap of satellite imagery"""
    logger.info("/debug/basemap Unimplemented!")
    return {"message": "Hello World from /debug/basemap"}

@router.get("/polygonize")
def make_task_polygons():
    """Make a multipolygon containing all the task boundaries"""
    logger.info("/debug/polygonize is Unimplemented!")
    return {"message": "Hello World from /debug/polygonize"}

@router.get("/makecsv")
def do_odk2csv():
    """Convert the submissions data into a CSV file"""
    logger.info("/debug/do_odk2csv is Unimplemented!")
    return {"message": "Hello World from /debug/makecsv"}

@router.get("/makeosm")
def do_csv2osm():
    """Convert the submissions data into a CSV file"""
    logger.info("/debug/do_csv2osm is Unimplemented!")
    return {"message": "Hello World from /debug/makeosm"}

@router.get("/makexform")
def make_xform():
    """Convert the submissions data into a CSV file"""
    logger.info("/debug/do_csv2osm is Unimplemented!")
    return {"message": "Hello World from /debug/majexform"}

