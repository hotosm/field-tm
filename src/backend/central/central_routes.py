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
from fastapi.responses import JSONResponse
from sqlalchemy import (
    column,
    select,
    table,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..db import database
from ..projects import project_crud

router = APIRouter(
    prefix="/central",
    tags=["central"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects")
async def list_projects():
    """List projects in Central."""
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
    """Create an appuser in Central."""
    appuser = central_crud.create_appuser(project_id, name=name)
    # tasks = tasks_crud.update_qrcode(db, task_id, qrcode['id'])
    return project_crud.create_qrcode(db, project_id, appuser.get("token"), name)


# @router.get("/list_submissions")
# async def list_submissions(project_id: int):
#     """List the submissions data from Central"""
#     submissions = central_crud.list_submissions(project_id)
#     logger.info("/central/list_submissions is Unimplemented!")
#     return {"data": submissions}


@router.get("/download_submissions")
async def download_submissions(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the submissions data from Central."""
    project = table(
        "projects", column("project_name_prefix"), column("xform_title"), column("id"), column("odkid")
    )
    where = f"id={project_id}"
    sql = select(project).where(text(where))
    result = db.execute(sql)
    first = result.first()
    if not first:
        return {"error": "No such project!"}
    # FIXME: this should be configurable
    tmp = "/tmp"
    filespec = f"{tmp}/{first.project_name_prefix}_{first.xform_title}"

    xforms = central_crud.list_odk_xforms(first.odkid)
    submissions = list()
    for xform in xforms:
        data = central_crud.download_submissions(first.odkid, xform["xmlFormId"])
        # An empty submissions only has the CSV headers
        # headers = data[0]
        if len(submissions) == 0:
            submissions.append(data[0])
        if len(data) >= 2:
            for entry in range(1, len(data)):
                submissions.append(data[entry])

    result = central_crud.convert_csv(filespec, submissions)
    return {"data": result}

# @router.get("/upload")
# async def upload_project_files(
#         project_id: int,
#         filespec: str
# ):
#     """Upload the XForm and data files to Central"""
#     logger.warning("/central/upload is Unimplemented!")
#     return {"message": "Hello World from /central/upload"}


# @router.get("/download")
# async def download_project_files(
#     project_id: int,
#     type: central_schemas.CentralFileType
# ):
#     """Download the project data files from Central. The filespec is
#     a string that can contain multiple filenames separated by a comma.
#     """
#     # FileResponse("README.md")
#     # xxx = central_crud.does_central_exist()
#     logger.warning("/central/download is Unimplemented!")
#     return {"message": "Hello World from /central/download"}
