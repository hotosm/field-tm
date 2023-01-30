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

router = APIRouter(
    prefix="/central",
    tags=["central"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=debug_schemas.DebugOut)
async def central():
    return {"message": "Hello World!"}
    #raise HTTPException(status_code=404, detail="Tasks not found")

@router.get("/appuser")
def create_appuser():
    """Create an appuser in Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /debug/submisisons"}

@router.get("/project")
def create_project():
    """Create a project in Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /debug/submisisons"}

@router.get("/submissions")
def download_submissions():
    """Download the submissions data from Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /debug/submisisons"}

@router.get("/upload")
def upload_project_files():
    """Upload the XForm and data files to Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /central/upload"}

@router.get("/download")
def download_project_files():
    """Download the project data files from Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /central/upload"}

