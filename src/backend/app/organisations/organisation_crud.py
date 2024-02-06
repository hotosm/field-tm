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
"""Logic for organisation management."""

from io import BytesIO

from fastapi import HTTPException, Response, UploadFile
from loguru import logger as log
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.auth.osm import AuthUser
from app.config import settings
from app.db import db_models
from app.models.enums import HTTPStatus, UserRole
from app.organisations.organisation_deps import (
    get_organisation_by_name,
)
from app.organisations.organisation_schemas import OrganisationEdit, OrganisationIn
from app.s3 import add_obj_to_bucket
from app.users.user_crud import get_user


async def get_organisations(
    db: Session, current_user: AuthUser, is_approved: bool
) -> list[db_models.DbOrganisation]:
    """Get all orgs."""
    db_user = await get_user(db, current_user.id)

    if db_user.role != UserRole.ADMIN:
        # If user not admin, only show approved orgs
        is_approved = True

    return db.query(db_models.DbOrganisation).filter_by(approved=is_approved).all()


async def upload_logo_to_s3(
    db_org: db_models.DbOrganisation, logo_file: UploadFile(None)
) -> str:
    """Upload logo using standardised /{org_id}/logo.png format.

    Browsers treat image mimetypes the same, regardless of extension,
    so it should not matter if a .jpg is renamed .png.

    Args:
        db_org(db_models.DbOrganisation): The organisation database object.
        logo_file(UploadFile): The logo image uploaded to FastAPI.

    Returns:
        logo_url(str): The S3 URL for the logo file.
    """
    logo_path = f"/{db_org.id}/logo.png"

    file_bytes = await logo_file.read()
    file_obj = BytesIO(file_bytes)

    add_obj_to_bucket(
        settings.S3_BUCKET_NAME,
        file_obj,
        logo_path,
        content_type=logo_file.content_type,
    )

    logo_url = f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}{logo_path}"

    return logo_url


async def create_organisation(
    db: Session, org_model: OrganisationIn, logo: UploadFile(None)
) -> db_models.DbOrganisation:
    """Creates a new organisation with the given name, description, url, type, and logo.

    Saves the logo file S3 bucket under /{org_id}/logo.png.

    Args:
        db (Session): database session
        org_model (OrganisationIn): Pydantic model for organisation input.
        logo (UploadFile, optional): logo file of the organisation.
            Defaults to File(...).

    Returns:
        DbOrganisation: SQLAlchemy Organisation model.
    """
    if await get_organisation_by_name(db, org_name=org_model.name):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Organisation already exists with the name ({org_model.name})",
        )

    # Required to check if exists on error
    db_organisation = None

    try:
        # Create new organisation without logo set
        db_organisation = db_models.DbOrganisation(**org_model.model_dump())

        db.add(db_organisation)
        db.commit()
        # Refresh to get the assigned org id
        db.refresh(db_organisation)

        # Update the logo field in the database with the correct path
        if logo:
            db_organisation.logo = await upload_logo_to_s3(db_organisation, logo)
        db.commit()

    except Exception as e:
        log.exception(e)
        log.debug("Rolling back changes to db organisation")
        # Rollback any changes
        db.rollback()
        # Delete the failed organisation entry
        if db_organisation:
            log.debug(f"Deleting created organisation ID {db_organisation.id}")
            db.delete(db_organisation)
            db.commit()
        raise HTTPException(
            status_code=400, detail=f"Error creating organisation: {e}"
        ) from e

    return db_organisation


async def update_organisation(
    db: Session,
    organisation: db_models.DbOrganisation,
    values: OrganisationEdit,
    logo: UploadFile(None),
) -> db_models.DbOrganisation:
    """Update an existing organisation database entry.

    Args:
        db (Session): database session
        organisation (DbOrganisation): Editing database model.
        values (OrganisationEdit): Pydantic model for organisation edit.
        logo (UploadFile, optional): logo file of the organisation.
            Defaults to File(...).

    Returns:
        DbOrganisation: SQLAlchemy Organisation model.
    """
    if not (updated_fields := values.dict(exclude_none=True)):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"No values were provided to update organisation {organisation.id}",
        )

    update_cmd = (
        update(db_models.DbOrganisation)
        .where(db_models.DbOrganisation.id == organisation.id)
        .values(**updated_fields)
    )
    db.execute(update_cmd)

    if logo:
        organisation.logo = await upload_logo_to_s3(organisation, logo)

    db.commit()
    db.refresh(organisation)

    return organisation


async def delete_organisation(
    db: Session,
    organisation: db_models.DbOrganisation,
) -> Response:
    """Delete an existing organisation database entry.

    Args:
        db (Session): database session
        organisation (DbOrganisation): Database model to delete.

    Returns:
        bool: If deletion was successful.
    """
    db.delete(organisation)
    db.commit()

    return Response(status_code=HTTPStatus.NO_CONTENT)


async def add_organisation_admin(
    db: Session, user: db_models.DbUser, organisation: db_models.DbOrganisation
):
    """Adds a user as an admin to the specified organisation.

    Args:
        db (Session): The database session.
        user (DbUser): The user model instance.
        organisation (DbOrganisation): The organisation model instance.

    Returns:
        Response: The HTTP response with status code 200.
    """
    log.info(f"Adding user ({user.id}) as org ({organisation.id}) admin")
    # add data to the managers field in organisation model
    organisation.managers.append(user)
    db.commit()

    return Response(status_code=HTTPStatus.OK)


async def approve_organisation(db, organisation):
    """Approves an oranisation request made by the user .

    Args:
        db: The database session.
        organisation (DbOrganisation): The organisation model instance.

    Returns:
        Response: An HTTP response with the status code 200.
    """
    log.info(f"Approving organisation ID {organisation.id}")
    organisation.approved = True
    db.commit()
    return Response(status_code=HTTPStatus.OK)
