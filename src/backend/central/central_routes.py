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
from sqlalchemy.orm import Session
from fastapi.logger import logger as logger
from fastapi.responses import JSONResponse

from ..db import database
from ..central import central_schemas, central_crud
from ..projects import project_crud

# # FIXME: I am not sure this is thread-safe
# from odkconvert.OdkCentral import OdkProject, OdkAppUser, OdkForm
# project = OdkProject()
# xform = OdkForm()
# appuser = OdkAppUser()

# url = settings.ODK_CENTRAL_URL
# user = settings.ODK_CENTRAL_USER
# pw = settings.ODK_CENTRAL_PASSWD
# project.authenticate(url, user, pw)

router = APIRouter(
    prefix="/central",
    tags=["central"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects")
async def list_projects():
    """List projects in Central"""
    projects = central_crud.list_odk_projects()
    if projects is None:
        return {"message": "No projects found"}
    return JSONResponse(content={"projects": projects})


@router.get("/appuser")
async def create_appuser(
    project_id: int,
    name: str,
    db: Session = Depends(database.get_db),
):
    """Create an appuser in Central"""
    appuser = central_crud.create_appuser(project_id, name=name)
    # tasks = tasks_crud.update_qrcode(db, task_id, qrcode['id'])
    return project_crud.create_qrcode(db, project_id, appuser.get("token"), name)


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
async def download_project_files(
    project_id: int, type: central_schemas.CentralFileType
):
    """Download the project data files from Central. The filespec is
    a string that can contain multiple filenames separated by a comma.
    """
    # FileResponse("README.md")
    # xxx = central_crud.does_central_exist()
    logger.warning("/central/download is Unimplemented!")
    return {"message": "Hello World from /central/download"}
