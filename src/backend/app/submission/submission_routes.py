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

from fastapi import APIRouter, Depends
from fastapi.logger import logger as logger
from sqlalchemy.orm import Session

from ..db import database
from . import submission_crud

router = APIRouter(
    prefix="/submission",
    tags=["submission"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_submissions(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):
    """This api returns the submission made in the project.
    It takes two parameters: project_id and task_id.


    project_id: The ID of the project. This endpoint returns the submission made in this project.

    task_id: The ID of the task. This parameter is optional. If task_id is provided, this endpoint returns the submissions made for this task.

    Returns the list of submissions.
    """
    return submission_crud.get_submission_of_project(db, project_id, task_id)


@router.get("/list-forms")
async def list_forms(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """This api returns the list of forms in the odk central.

    It takes one parameter: project_id.

    project_id: The ID of the project. This endpoint returns the list of forms in this project.

    Returns the list of forms details provided by the central api.
    """
    return submission_crud.get_forms_of_project(db, project_id)


@router.get("/list-app-users")
async def list_app_users(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """This api returns the list of forms in the odk central.

    It takes one parameter: project_id.

    project_id: The ID of the project. This endpoint returns the list of forms in this project.

    Returns the list of forms details provided by the central api.
    """
    return submission_crud.list_app_users_or_project(db, project_id)


@router.get("/download")
async def download_submission(
    project_id: int,
    task_id: int = None,
    exportJson: bool = True,
    db: Session = Depends(database.get_db),
):
    """This api downloads the the submission made in the project.
    It takes two parameters: project_id and task_id.

    project_id: The ID of the project. This endpoint returns the submission made in this project.

    task_id: The ID of the task. This parameter is optional. If task_id is provided, this endpoint returns the submissions made for this task.

    """
    return submission_crud.download_submission(db, project_id, task_id, exportJson)


@router.get("/submission-points")
async def submission_points(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):
    """This api returns the submission points of a project.
    It takes two parameter: project_id and task_id.

    project_id: The ID of the project. This endpoint returns the submission points of this project.
    task_id: The task_id of the project. This endpoint returns the submission points of this task.
    """
    return submission_crud.get_submission_points(db, project_id, task_id)


@router.get("/convert-to-osm")
async def convert_to_osm(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):

    """
        This api converts the submission to osm format.
        It takes two parameter: project_id and task_id.

        task_id is optional. 
        If task_id is provided, this endpoint converts the submission of this task.
        If task_id is not provided, this endpoint converts the submission of the whole project.

    """

    return await submission_crud.convert_to_osm(db, project_id, task_id)
