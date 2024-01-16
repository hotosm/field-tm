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
    UploadFile,
)
from sqlalchemy.orm import Session

from app.db import database
from app.db.db_models import DbOrganisation
from app.organization import organization_crud, organization_schemas
from app.organization.organization_deps import org_exists

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[organization_schemas.OrganisationOut])
def get_organisations(
    db: Session = Depends(database.get_db),
) -> list[organization_schemas.OrganisationOut]:
    """Get a list of all organizations."""
    return organization_crud.get_organisations(db)


@router.get("/{org_id}", response_model=organization_schemas.OrganisationOut)
async def get_organization_detail(
    organization: DbOrganisation = Depends(org_exists),
    db: Session = Depends(database.get_db),
):
    """Get a specific organization by id or name."""
    return organization


@router.post("/", response_model=organization_schemas.OrganisationOut)
async def create_organization(
    org: organization_schemas.OrganisationIn = Depends(),
    logo: UploadFile = File(None),
    db: Session = Depends(database.get_db),
) -> organization_schemas.OrganisationOut:
    """Create an organization with the given details."""
    return await organization_crud.create_organization(db, org, logo)


@router.patch("/{org_id}/", response_model=organization_schemas.OrganisationOut)
async def update_organization(
    new_values: organization_schemas.OrganisationEdit = Depends(),
    logo: UploadFile = File(None),
    organization: DbOrganisation = Depends(org_exists),
    db: Session = Depends(database.get_db),
):
    """Partial update for an existing organization."""
    return await organization_crud.update_organization(
        db, organization, new_values, logo
    )


@router.delete("/{org_id}")
async def delete_organisations(
    organization: DbOrganisation = Depends(org_exists),
    db: Session = Depends(database.get_db),
):
    """Delete an organization."""
    return await organization_crud.delete_organization(db, organization)
