# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=debug_schemas.DebugOut)
async def debug():
    return {"message": "Hello World!"}
    #raise HTTPException(status_code=404, detail="Tasks not found")

@router.get("/makeqr")
def make_qrcode():
    """Make a QR code for an app_user"""
    logger.info("/debug/makeqr is Unimplemented!")
    return {"message": "Hello World from /debug/makeqr"}

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
    return {"message": "Hello World from /debug/basemap"}

