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

from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, OrgUserDict
from app.auth.roles import org_admin, super_admin
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbOrganisation, DbOrganisationManagers
from app.organisations import organisation_crud
from app.organisations.organisation_deps import org_exists
from app.organisations.organisation_schemas import (
    OrganisationIn,
    OrganisationOut,
    OrganisationUpdate,
    parse_organisation_input,
)

router = APIRouter(
    prefix="/organisation",
    tags=["organisation"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=list[OrganisationOut])
async def get_organisations(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> list[DbOrganisation]:
    """Get a list of all organisations."""
    return await DbOrganisation.all(db, current_user.id)


@router.post("", response_model=OrganisationOut)
async def create_organisation(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
    # Depends required below to allow logo upload
    org_in: OrganisationIn = Depends(parse_organisation_input),
    logo: Optional[UploadFile] = File(None),
) -> OrganisationOut:
    """Create an organisation with the given details.

    Either a logo can be uploaded, or a link to the logo provided
    in the Organisation JSON ('logo': 'https://your.link.to.logo.png').
    """
    if org_in.name is None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="The `name` is required to create an organisation.",
        )
    return await DbOrganisation.create(db, org_in, current_user.id, logo)


@router.get("/my-organisations", response_model=list[OrganisationOut])
async def get_my_organisations(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> list[DbOrganisation]:
    """Get a list of all organisations."""
    return await organisation_crud.get_my_organisations(db, current_user)


@router.get("/unapproved", response_model=list[OrganisationOut])
async def list_unapproved_organisations(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> list[DbOrganisation]:
    """Get a list of unapproved organisations."""
    return await DbOrganisation.unapproved(db)


@router.delete("/unapproved/{org_id}")
async def delete_unapproved_org(
    org_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(super_admin)],
):
    """Delete an unapproved organisation.

    NOTE this endpoint is required as
        org_user_dict: Annotated[AuthUser, Depends(org_admin)]
    will also check if the organisation is approved and error if it's not.
    This is an ADMIN-only endpoint for deleting unapproved orgs.
    """
    org_deleted = await DbOrganisation.delete(db, org_id)

    if not org_deleted:
        log.error(f"Failed deleting org ({org_id}).")
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Failed deleting org ({org_id}).",
        )

    log.info(f"Successfully deleted org ({org_id}).")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/approve", response_model=OrganisationOut)
async def approve_organisation(
    org_id: int,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(super_admin)],
):
    """Approve the organisation request made by the user.

    The logged in user must be super admin to perform this action .
    """
    log.info(f"Approving organisation ({org_id}).")
    approved_org = await DbOrganisation.update(
        db,
        org_id,
        OrganisationUpdate(approved=True),
    )
    # Set organisation requester as organisation manager
    if approved_org.created_by:
        await DbOrganisationManagers.create(
            db, approved_org.id, approved_org.created_by
        )

    return approved_org


@router.post("/new-admin")
async def add_new_organisation_admin(
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    user_id: int,
):
    """Add a new organisation admin.

    The logged in user must be either the owner of the organisation or a super admin.
    """
    await DbOrganisationManagers.create(
        db,
        org_user_dict.get("org").id,
        user_id,
    )


@router.get("/{org_id}", response_model=OrganisationOut)
async def get_organisation_detail(
    organisation: Annotated[DbOrganisation, Depends(org_exists)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get a specific organisation by id or name."""
    return organisation


@router.patch("/{org_id}", response_model=OrganisationOut)
async def update_organisation(
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[AuthUser, Depends(org_admin)],
    new_values: OrganisationUpdate = Depends(parse_organisation_input),
    logo: UploadFile = File(None),
):
    """Partial update for an existing organisation."""
    org_id = org_user_dict.get("org").id
    return await DbOrganisation.update(db, org_id, new_values, logo)


@router.delete("/{org_id}")
async def delete_org(
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[AuthUser, Depends(org_admin)],
):
    """Delete an organisation."""
    org = org_user_dict.get("org")
    org_deleted = await DbOrganisation.delete(db, org.id)
    if not org_deleted:
        log.error(f"Failed deleting org ({org.name}).")
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Failed deleting org ({org.name}).",
        )
    return Response(status_code=HTTPStatus.NO_CONTENT)
