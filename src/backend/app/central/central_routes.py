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
"""Routes to relay requests to ODK Central server."""

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.central import central_crud
from app.db import database

router = APIRouter(
    prefix="/central",
    tags=["central"],
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


@router.get("/list-forms")
async def get_form_lists(
    db: Session = Depends(database.get_db),
) -> list:
    """Get a list of all XLSForms available in FMTM.

    Returns:
        dict: JSON of {id:title} with each XLSForm record.
    """
    forms = await central_crud.get_form_list(db)
    return forms
