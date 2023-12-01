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
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from loguru import logger as log
from sqlalchemy import (
    column,
    select,
    table,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..db import database
from ..projects import project_crud, project_schemas

router = APIRouter(
    prefix="/central",
    tags=["central"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects")
async def list_projects():
    """List projects in Central."""
    # TODO update for option to pass credentials by user
    # NOTE runs in separate thread using run_in_threadpool
    projects = await run_in_threadpool(lambda: central_crud.list_odk_projects())
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
    return await project_crud.create_qrcode(db, project_id, appuser.get("token"), name)


# @router.get("/list_submissions")
# async def list_submissions(project_id: int):
#     """List the submissions data from Central"""
#     submissions = central_crud.list_submissions(project_id)
#     log.info("/central/list_submissions is Unimplemented!")
#     return {"data": submissions}


@router.get("/list-forms")
async def get_form_lists(
    db: Session = Depends(database.get_db), skip: int = 0, limit: int = 100
):
    """This function retrieves a list of XForms from a database,
    with the option to skip a certain number of records and limit the number of records returned.


    Parameters:
    skip:int: the number of records to skip before starting to retrieve records. Defaults to 0 if not provided.
    limit:int: the maximum number of records to retrieve. Defaults to 10 if not provided.


    Returns:
    A list of dictionary containing the id and title of each XForm record retrieved from the database.
    """
    # NOTE runs in separate thread using run_in_threadpool
    forms = await run_in_threadpool(lambda: central_crud.get_form_list(db, skip, limit))
    return forms


@router.get("/download_submissions")
async def download_submissions(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the submissions data from Central."""
    project = table(
        "projects",
        column("project_name_prefix"),
        column("xform_title"),
        column("id"),
        column("odkid"),
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
        # FIXME this should be optimised via async or threadpool
        # FIXME very expensive opteration to run blocking in parallel
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


@router.get("/list-submissions")
async def list_submissions(
    project_id: int,
    xml_form_id: str = None,
    db: Session = Depends(database.get_db),
):
    try:
        project = table(
            "projects",
            column("project_name_prefix"),
            column("xform_title"),
            column("id"),
            column("odkid"),
        )
        where = f"id={project_id}"
        sql = select(project).where(text(where))
        result = db.execute(sql)
        first = result.first()
        if not first:
            return {"error": "No such project!"}

        submissions = list()

        if not xml_form_id:
            xforms = central_crud.list_odk_xforms(first.odkid)

            for xform in xforms:
                try:
                    data = central_crud.download_submissions(
                        first.odkid, xform["xml_form_id"], None, False
                    )
                except Exception:
                    continue
                if len(submissions) == 0:
                    submissions.append(json.loads(data[0]))
                if len(data) >= 2:
                    for entry in range(1, len(data)):
                        submissions.append(json.loads(data[entry]))
        else:
            data = central_crud.download_submissions(first.odkid, xml_form_id)
            if len(submissions) == 0:
                submissions.append(json.loads(data[0]))
            if len(data) >= 2:
                for entry in range(1, len(data)):
                    submissions.append(json.loads(data[entry]))

        return submissions
    except Exception as e:
        log.error(e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/submission")
async def get_submission(
    project_id: int,
    xmlFormId: str = None,
    submission_id: str = None,
    db: Session = Depends(database.get_db),
):
    """This api returns the submission json.

    Parameters:
    project_id:int the id of the project in the database.
    xml_form_id:str: the xmlFormId of the form in Central.
    submission_id:str: the submission id of the submission in Central.

    If the submission_id is provided, an individual submission is returned.

    Returns: Submission json.
    """
    try:
        """Download the submissions data from Central."""
        project = table(
            "projects",
            column("project_name_prefix"),
            column("xform_title"),
            column("id"),
            column("odkid"),
            column("odk_central_url"),
            column("odk_central_user"),
            column("odk_central_password"),
        )
        where = f"id={project_id}"
        sql = select(project).where(text(where))
        result = db.execute(sql)
        first = result.first()
        if not first:
            return {"error": "No such project!"}

        # ODK Credentials
        odk_credentials = project_schemas.ODKCentral(
            odk_central_url=first.odk_central_url,
            odk_central_user=first.odk_central_user,
            odk_central_password=first.odk_central_password,
        )

        submissions = list()

        if xmlFormId and submission_id:
            data = central_crud.download_submissions(
                first.odkid, xmlFormId, submission_id, True, odk_credentials
            )
            if len(submissions) == 0:
                submissions.append(json.loads(data[0]))
            if len(data) >= 2:
                for entry in range(1, len(data)):
                    submissions.append(json.loads(data[entry]))

        else:
            if not xmlFormId:
                xforms = central_crud.list_odk_xforms(first.odkid)
                for xform in xforms:
                    try:
                        data = central_crud.download_submissions(
                            first.odkid,
                            xform["xml_form_id"],
                            None,
                            True,
                            odk_credentials,
                        )
                    except Exception:
                        continue
                    if len(submissions) == 0:
                        submissions.append(json.loads(data[0]))
                    if len(data) >= 2:
                        for entry in range(1, len(data)):
                            submissions.append(json.loads(data[entry]))
            else:
                data = central_crud.download_submissions(first.odkid, xmlFormId)
                if len(submissions) == 0:
                    submissions.append(json.loads(data[0]))
                if len(data) >= 2:
                    for entry in range(1, len(data)):
                        submissions.append(json.loads(data[entry]))

        return submissions
    except Exception as e:
        log.error(e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# @router.get("/upload")
# async def upload_project_files(
#         project_id: int,
#         filespec: str
# ):
#     """Upload the XForm and data files to Central"""
#     log.warning("/central/upload is Unimplemented!")
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
#     log.warning("/central/download is Unimplemented!")
#     return {"message": "Hello World from /central/download"}
