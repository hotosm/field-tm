# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Routes for organisation management."""

from datetime import date
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser, OrgUserDict
from app.auth.providers.osm import init_osm_auth
from app.auth.roles import org_admin, super_admin
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbOrganisation, DbOrganisationManagers
from app.organisations import organisation_crud
from app.organisations.organisation_deps import (
    get_org_odk_creds,
    org_exists,
)
from app.organisations.organisation_schemas import (
    OrganisationIn,
    OrganisationOut,
    OrganisationUpdate,
    OrgManagersOut,
    StatsResponse,
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
    return await DbOrganisation.all(db, current_user.sub)


@router.post("", response_model=OrganisationOut)
async def create_organisation(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
    # Depends required below to allow logo upload
    org_in: OrganisationIn = Depends(parse_organisation_input),
    logo: Optional[UploadFile] = File(None),
    osm_auth=Depends(init_osm_auth),
    request_odk_server: bool = False,
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
    organisation = await DbOrganisation.create(db, org_in, current_user.sub, logo)

    primary_organisation = await DbOrganisation.primary_org(db)
    background_tasks.add_task(
        organisation_crud.send_organisation_approval_request,
        request=request,
        organisation=organisation,
        db=db,
        requester=current_user.username,
        primary_organisation=primary_organisation,
        osm_auth=osm_auth,
        request_odk_server=request_odk_server,
    )
    return organisation


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
        org_user_dict: Annotated[OrgUserDict, Depends(org_admin)]
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
    request: Request,
    org_id: int,
    background_tasks: BackgroundTasks,
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(super_admin)],
    osm_auth=Depends(init_osm_auth),
    set_primary_org_odk_server: bool = False,
):
    """Approve the organisation request made by the user.

    The logged in user must be super admin to perform this action.

    A background task notifies the organisation creator.
    """
    log.info(f"Approving organisation ({org_id}).")
    primary_organisation = await DbOrganisation.primary_org(db)
    primary_org_odk_creds = await get_org_odk_creds(primary_organisation)
    if set_primary_org_odk_server:
        org_update = OrganisationUpdate(
            odk_central_url=primary_org_odk_creds.odk_central_url,
            odk_central_user=primary_org_odk_creds.odk_central_user,
            odk_central_password=primary_org_odk_creds.odk_central_password,
            approved=True,
        )
    else:
        org_update = OrganisationUpdate(approved=True)
    approved_org = await DbOrganisation.update(
        db,
        org_id,
        org_update,
    )
    # Set organisation requester as organisation manager
    if approved_org.created_by:
        await DbOrganisationManagers.create(
            db, approved_org.id, approved_org.created_by
        )

        log.info(f"Approved organisation ({org_id}).")
        background_tasks.add_task(
            organisation_crud.send_approval_message,
            request=request,
            creator_sub=approved_org.created_by,
            organisation_name=approved_org.name,
            osm_auth=osm_auth,
            set_primary_org_odk_server=set_primary_org_odk_server,
        )

    return approved_org


@router.post("/new-admin")
async def add_new_organisation_admin(
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    user_sub: str,
):
    """Add a new organisation admin.

    The logged in user must be either the owner of the organisation or a super admin.
    """
    await DbOrganisationManagers.create(
        db,
        org_user_dict.get("org").id,
        user_sub,
    )


@router.get("/org-admins", response_model=list[OrgManagersOut])
async def get_organisation_admins(
    db: Annotated[Connection, Depends(db_conn)],
    organisation: Annotated[DbOrganisation, Depends(org_exists)],
    current_user: Annotated[AuthUser, Depends(login_required)],
):
    """Get the list of organisation admins."""
    org_managers = await DbOrganisationManagers.get(
        db,
        organisation.id,
    )
    return org_managers


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
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
    new_values: OrganisationUpdate = Depends(parse_organisation_input),
    logo: UploadFile = File(None),
):
    """Partial update for an existing organisation."""
    org_id = org_user_dict.get("org").id
    return await DbOrganisation.update(db, org_id, new_values, logo)


@router.delete("/{org_id}")
async def delete_org(
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
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


@router.delete("/org-admin/{user_sub}")
async def remove_organisation_admin(
    user_sub: str,
    db: Annotated[Connection, Depends(db_conn)],
    org_user_dict: Annotated[OrgUserDict, Depends(org_admin)],
):
    """Remove an organization admin.

    The logged in user must be either the admin of the organization or a super admin.
    Users cannot delete their own admin role.

    Args:
        user_sub: The subject ID of the user to remove as admin
        db: Database connection
        org_user_dict: Dictionary containing authenticated user and organization info

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 400 if attempting to delete own role
    """
    current_user = org_user_dict.get("user")
    if current_user.sub == user_sub:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="You cannot remove your own admin role.",
        )

    await DbOrganisationManagers.delete(db, user_sub)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{org_id}/stats", response_model=StatsResponse)
async def get_stats(
    org_id: int,
    org_user_dict: dict = Depends(
        org_admin
    ),  # admin or organisation admin can only access
    db: Connection = Depends(db_conn),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Get mapping and submission statistics for an organisation.

    Returns:
        StatsResponse: Aggregated statistics including tasks, activity, and submissions.
    """
    return await organisation_crud.get_organisation_stats(
        db, org_id, start_date, end_date
    )


@router.get("/{org_id}/submissions/download")
async def download_organisation_submissions_route(
    org_id: int,
    file_type: str = "geojson",
    submitted_date_range: str = None,
    org_user_dict: dict = Depends(
        org_admin
    ),  # admin or organisation admin can only access
    db: Connection = Depends(db_conn),
):
    """Download all submissions for an organisation across projects.

    Returns:
        StreamingResponse: CSV or GeoJSON file containing submission data.
    """
    return await organisation_crud.download_organisation_submissions(
        db, org_id, file_type, submitted_date_range
    )
