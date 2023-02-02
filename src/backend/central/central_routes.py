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
from db import database
from models.enums import TaskStatus
from central import central_schemas, central_crud
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/central",
    tags=["central"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=central_schemas.CentralOut)
async def central():
    return {"message": "Hello World!"}
    #raise HTTPException(status_code=404, detail="Tasks not found")

@router.get("/appuser")
async def create_appuser(name):
    """Create an appuser in Central"""
    logger.info("/central/appuser is Unimplemented!")
    return {"message": "Hello World from /central/appuser"}

@router.get("/project")
async def create_project(name: str, boundary: str):
    """Create a project in Central"""
    logger.info("/central/project is Unimplemented!")
    # TODO: Return project_id instead of debug
    return {"message": "Hello World from /central/project"}

@router.get("/submissions")
async def download_submissions(project_id: int, xform_id: str):
    """Download the submissions data from Central"""
    logger.info("/central/submissions is Unimplemented!")
    return {"message": "Hello World from /central/submisisons"}

@router.get("/upload")
async def upload_project_files(project_id: int, filespec: str):
    """Upload the XForm and data files to Central"""
    logger.warning("/central/upload is Unimplemented!")
    return {"message": "Hello World from /central/upload"}

@router.get("/download")
async def download_project_files(project_id: int, type: central_schemas.CentralFileType):
    """Download the project data files from Central. The filespec is
    a string that can contain multiple filenames separeted by a comma.
    """
    # FileResponse("README.md")
    #xxx = central_crud.does_central_exist()
    logger.warning("/central/download is Unimplemented!")
    return {"message": "Hello World from /central/download"}

