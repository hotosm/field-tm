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

from typing import Union,Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.logger import logger as logger
from sqlalchemy.orm import Session

from ..db import database
from . import organization_crud

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def get_organisations(
    db: Session = Depends(database.get_db),

):
    """Get api for fetching organization list."""
    organizations = organization_crud.get_organisations(db)
    return organizations


@router.post("/")
async def create_organization(
    # organization: organization_schemas.Organisation = Form(...),
    name: str=Form(),
    description: str=Form(None),
    url: str=Form(None),
    type: int=Form(),
    logo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """Create a new organization.

    This endpoint allows you to create a new organization by providing the necessary details in the request body.

    ## Request Body
    - `slug` (str): the organization's slug. Required.
    - `logo` (str): the URL of the organization's logo. Required.
    - `name` (str): the name of the organization. Required.
    - `description` (str): a description of the organization.0
    - `url` (str): the URL of the organization's website. Required.
    - `type` (int): the type of the organization. Required.


    ## Response
    - Returns a JSON object containing a success message .

    ### Example Response
    ```
    {
        "Message": "Organization Created Successfully.",
    }
    ```
    """
    await organization_crud.create_organization(db,name,description,url,type,logo)

    return {"Message": "Organization Created Successfully."}
