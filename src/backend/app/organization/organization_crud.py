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

import re
from io import BytesIO

from fastapi import HTTPException, UploadFile
from loguru import logger as log
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import db_models
from app.s3 import add_obj_to_bucket


def get_organisations(
    db: Session,
):
    """Get all orgs."""
    db_organisation = db.query(db_models.DbOrganisation).all()
    return db_organisation


def generate_slug(text: str) -> str:
    """Sanitise the organization name for use in a URL."""
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower().replace(" ", "-")
    # Remove consecutive hyphens
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


async def get_organisation_by_name(db: Session, name: str):
    """Get org by name.

    This function is used to check if a org exists with the same name.
    """
    # Use SQLAlchemy's query-building capabilities
    db_organisation = (
        db.query(db_models.DbOrganisation)
        .filter(func.lower(db_models.DbOrganisation.name).like(func.lower(f"%{name}%")))
        .first()
    )
    return db_organisation


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
        logo_path(str): The file path in S3.
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

    return logo_path


async def create_organization(
    db: Session, name: str, description: str, url: str, logo: UploadFile(None)
):
    """Creates a new organization with the given name, description, url, type, and logo.

    Saves the logo file S3 bucket under /{org_id}/logo.png.

    Args:
        db (Session): database session
        name (str): name of the organization
        description (str): description of the organization
        url (str): url of the organization
        type (int): type of the organization
        logo (UploadFile, optional): logo file of the organization.
            Defaults to File(...).

    Returns:
        bool: True if organization was created successfully
    """
    try:
        # Create new organization without logo set
        db_organization = db_models.DbOrganisation(
            name=name,
            slug=generate_slug(name),
            description=description,
            url=url,
        )

        db.add(db_organization)
        db.commit()
        # Refresh to get the assigned org id
        db.refresh(db_organization)

        logo_path = await upload_logo_to_s3(db_organization, logo)

        # Update the logo field in the database with the correct path
        db_organization.logo = (
            f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}{logo_path}"
        )
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

    return True


async def get_organisation_by_id(db: Session, id: int):
    """Get an organization by its id.

    Args:
        db (Session): database session
        id (int): id of the organization

    Returns:
        DbOrganisation: organization with the given id
    """
    db_organization = (
        db.query(db_models.DbOrganisation)
        .filter(db_models.DbOrganisation.id == id)
        .first()
    )
    return db_organization


async def update_organization_info(
    db: Session,
    organization_id,
    name: str,
    description: str,
    url: str,
    logo: UploadFile,
):
    """Update an existing organisation database entry."""
    organization = await get_organisation_by_id(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if name:
        organization.name = name
    if description:
        organization.description = description
    if url:
        organization.url = url
    if logo:
        organization.logo = await upload_logo_to_s3(organization, logo)

    db.commit()
    db.refresh(organization)
    return organization
