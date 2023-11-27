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
"""Routes for organization management."""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from loguru import logger as log
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


@router.get("/{organization_id}")
async def get_organization_detail(
    organization_id: int, db: Session = Depends(database.get_db)
):
    """Get API for fetching detail about a organiation based on id."""
    organization = await organization_crud.get_organisation_by_id(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return organization


@router.post("/")
async def create_organization(
    name: str = Form(),  # Required field for organization name
    description: str = Form(None),  # Optional field for organization description
    url: str = Form(None),  # Optional field for organization URL
    logo: UploadFile = File(None),  # Optional field for organization logo
    db: Session = Depends(database.get_db),  # Dependency for database session
):
    """Create an organization with the given details.

    Parameters:
        name (str): The name of the organization. Required.
        description (str): The description of the organization. Optional.
        url (str): The URL of the organization. Optional.
        logo (UploadFile): The logo of the organization. Optional.
        db (Session): The database session. Dependency.

    Returns:
        dict: A dictionary with a message indicating successful creation
            of the organization.
    """
    # Check if the organization with the same already exists
    if await organization_crud.get_organisation_by_name(db, name=name):
        raise HTTPException(
            status_code=400, detail=f"Organization already exists with the name {name}"
        )

    await organization_crud.create_organization(db, name, description, url, logo)

    return {"Message": "Organization Created Successfully."}


@router.patch("/{organization_id}/")
async def update_organization(
    organization_id: int,
    name: str = Form(None),
    description: str = Form(None),
    url: str = Form(None),
    logo: UploadFile = File(None),
    db: Session = Depends(database.get_db),
):
    """PUT API to update the details of an organization."""
    try:
        organization = await organization_crud.update_organization_info(
            db, organization_id, name, description, url, logo
        )
        return organization
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=400, detail="Error updating organization."
        ) from e


@router.delete("/{organization_id}")
async def delete_organisations(
    organization_id: int, db: Session = Depends(database.get_db)
):
    """Delete an organization."""
    organization = await organization_crud.get_organisation_by_id(db, organization_id)

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    db.delete(organization)
    db.commit()
    return {"Message": "Organization Deleted Successfully."}
