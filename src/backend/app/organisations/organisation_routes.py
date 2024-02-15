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
"""Routes for organisation management."""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.auth.osm import AuthUser, login_required
from app.auth.roles import org_admin, super_admin
from app.db import database
from app.db.db_models import DbOrganisation, DbUser
from app.organisations import organisation_crud, organisation_schemas
from app.organisations.organisation_deps import check_org_exists, org_exists
from app.users.user_deps import user_exists_in_db

router = APIRouter(
    prefix="/organisation",
    tags=["organisation"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[organisation_schemas.OrganisationOut])
async def get_organisations(
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
) -> list[DbOrganisation]:
    """Get a list of all organisations."""
    return await organisation_crud.get_organisations(db, current_user)


@router.get("/unapproved/", response_model=list[organisation_schemas.OrganisationOut])
async def list_unapproved_organisations(
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(super_admin),
) -> list[DbOrganisation]:
    """Get a list of all organisations."""
    return await organisation_crud.get_unapproved_organisations(db)


@router.get(
    "/unapproved/{org_id}", response_model=list[organisation_schemas.OrganisationOut]
)
async def unapproved_org_detail(
    org_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(super_admin),
):
    """Get a detail of an unapproved organisations."""
    return await organisation_crud.get_unapproved_org_detail(db, org_id)


@router.get("/{org_id}", response_model=organisation_schemas.OrganisationOut)
async def get_organisation_detail(
    organisation: DbOrganisation = Depends(org_exists),
    current_user: AuthUser = Depends(login_required),
):
    """Get a specific organisation by id or name."""
    return organisation


@router.post("/", response_model=organisation_schemas.OrganisationOut)
async def create_organisation(
    # Depends required below to allow logo upload
    org: organisation_schemas.OrganisationIn = Depends(),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: DbUser = Depends(login_required),
) -> organisation_schemas.OrganisationOut:
    """Create an organisation with the given details.

    TODO refactor to use base64 encoded logo / no upload file.
    TODO then we can use the pydantic model as intended.
    """
    return await organisation_crud.create_organisation(db, org, logo)


@router.patch("/{org_id}/", response_model=organisation_schemas.OrganisationOut)
async def update_organisation(
    new_values: organisation_schemas.OrganisationEdit = Depends(),
    logo: UploadFile = File(None),
    organisation: DbOrganisation = Depends(org_exists),
    db: Session = Depends(database.get_db),
    org_user_dict: DbUser = Depends(org_admin),
):
    """Partial update for an existing organisation."""
    return await organisation_crud.update_organisation(
        db, organisation, new_values, logo
    )


@router.delete("/{org_id}")
async def delete_organisations(
    organisation: DbOrganisation = Depends(org_exists),
    db: Session = Depends(database.get_db),
    org_user_dict: DbUser = Depends(org_admin),
):
    """Delete an organisation."""
    return await organisation_crud.delete_organisation(db, organisation)


@router.post("/approve/")
async def approve_organisation(
    org_id: int,
    db: Session = Depends(database.get_db),
    current_user: DbUser = Depends(super_admin),
):
    """Approve the organisation request made by the user.

    The logged in user must be super admin to perform this action .
    """
    org_obj = await check_org_exists(db, org_id, check_approved=False)
    return await organisation_crud.approve_organisation(db, org_obj)


@router.post("/add_admin/")
async def add_new_organisation_admin(
    db: Session = Depends(database.get_db),
    organisation: DbOrganisation = Depends(org_exists),
    user: DbUser = Depends(user_exists_in_db),
    org_user_dict: DbUser = Depends(org_admin),
):
    """Add a new organisation admin.

    The logged in user must be either the owner of the organisation or a super admin.
    """
    return await organisation_crud.add_organisation_admin(db, user, organisation)
