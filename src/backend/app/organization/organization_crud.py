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
"""Logic for organization management."""

from io import BytesIO

from fastapi import HTTPException, Response, UploadFile
from loguru import logger as log
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.config import settings
from app.db import db_models
from app.models.enums import HTTPStatus
from app.organization.organization_deps import (
    get_organization_by_name,
)
from app.organization.organization_schemas import OrganisationEdit, OrganisationIn
from app.s3 import add_obj_to_bucket


def get_organisations(
    db: Session,
):
    """Get all orgs."""
    return db.query(db_models.DbOrganisation).all()


async def upload_logo_to_s3(
    db_org: db_models.DbOrganisation, logo_file: UploadFile(None)
) -> str:
    """Upload logo using standardised /{org_id}/logo.png format.

    Browsers treat image mimetypes the same, regardless of extension,
    so it should not matter if a .jpg is renamed .png.

    Args:
        db_org(db_models.DbOrganisation): The organization database object.
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


async def create_organization(
    db: Session, org_model: OrganisationIn, logo: UploadFile(None)
) -> db_models.DbOrganisation:
    """Creates a new organization with the given name, description, url, type, and logo.

    Saves the logo file S3 bucket under /{org_id}/logo.png.

    Args:
        db (Session): database session
        org_model (OrganisationIn): Pydantic model for organization input.
        logo (UploadFile, optional): logo file of the organization.
            Defaults to File(...).

    Returns:
        DbOrganization: SQLAlchemy Organization model.
    """
    if await get_organization_by_name(db, org_name=org_model.name):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Organization already exists with the name {org_model.name}",
        )

    # Required to check if exists on error
    db_organization = None

    try:
        # Create new organization without logo set
        db_organization = db_models.DbOrganisation(**org_model.dict())

        db.add(db_organization)
        db.commit()
        # Refresh to get the assigned org id
        db.refresh(db_organization)

        # Update the logo field in the database with the correct path
        if logo:
            db_organization.logo = await upload_logo_to_s3(db_organization, logo)
        db.commit()

    except Exception as e:
        log.exception(e)
        log.debug("Rolling back changes to db organization")
        # Rollback any changes
        db.rollback()
        # Delete the failed organization entry
        if db_organization:
            log.debug(f"Deleting created organisation ID {db_organization.id}")
            db.delete(db_organization)
            db.commit()
        raise HTTPException(
            status_code=400, detail=f"Error creating organization: {e}"
        ) from e

    return db_organization


async def update_organization(
    db: Session,
    organization: db_models.DbOrganisation,
    values: OrganisationEdit,
    logo: UploadFile(None),
) -> db_models.DbOrganisation:
    """Update an existing organisation database entry.

    Args:
        db (Session): database session
        organization (DbOrganisation): Editing database model.
        values (OrganisationEdit): Pydantic model for organization edit.
        logo (UploadFile, optional): logo file of the organization.
            Defaults to File(...).

    Returns:
        DbOrganization: SQLAlchemy Organization model.
    """
    if not (updated_fields := values.dict(exclude_none=True)):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"No values were provided to update organization {organization.id}",
        )

    update_cmd = (
        update(db_models.DbOrganisation)
        .where(db_models.DbOrganisation.id == organization.id)
        .values(**updated_fields)
    )
    db.execute(update_cmd)

    if logo:
        organization.logo = await upload_logo_to_s3(organization, logo)

    db.commit()
    db.refresh(organization)

    return organization


async def delete_organization(
    db: Session,
    organization: db_models.DbOrganisation,
) -> Response:
    """Delete an existing organisation database entry.

    Args:
        db (Session): database session
        organization (DbOrganisation): Database model to delete.

    Returns:
        bool: If deletion was successful.
    """
    db.delete(organization)
    db.commit()

    return Response(status_code=HTTPStatus.NO_CONTENT)
