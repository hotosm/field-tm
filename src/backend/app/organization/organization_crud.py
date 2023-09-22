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
import os
import random
import re
import string

from fastapi import HTTPException, UploadFile
from loguru import logger as log
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import db_models

IMAGEDIR = "app/images/"


def get_organisations(
    db: Session,
):
    db_organisation = db.query(db_models.DbOrganisation).all()
    return db_organisation


def generate_slug(text: str) -> str:
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower().replace(" ", "-")
    # Remove consecutive hyphens
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


async def get_organisation_by_name(db: Session, name: str):
    # Use SQLAlchemy's query-building capabilities
    db_organisation = (
        db.query(db_models.DbOrganisation)
        .filter(func.lower(db_models.DbOrganisation.name).like(func.lower(f"%{name}%")))
        .first()
    )
    return db_organisation


async def upload_image(db: Session, file: UploadFile(None)):
    # Check if file with the same name exists
    filename = file.filename
    file_path = f"{IMAGEDIR}{filename}"
    while os.path.exists(file_path):
        # Generate a random character
        random_char = "".join(random.choices(string.ascii_letters + string.digits, k=3))

        # Add the random character to the filename
        logo_name, extension = os.path.splitext(filename)
        filename = f"{logo_name}_{random_char}{extension}"
        file_path = f"{IMAGEDIR}{filename}"

    # Read the file contents
    contents = await file.read()

    # Save the file
    with open(file_path, "wb") as f:
        f.write(contents)

    return filename


async def create_organization(
    db: Session, name: str, description: str, url: str, logo: UploadFile(None)
):
    """Creates a new organization with the given name, description, url, type, and logo.
    Saves the logo file to the app/images folder.

    Args:
        db (Session): database session
        name (str): name of the organization
        description (str): description of the organization
        url (str): url of the organization
        type (int): type of the organization
        logo (UploadFile, optional): logo file of the organization. Defaults to File(...).

    Returns:
        bool: True if organization was created successfully
    """
    # create new organization
    try:
        logo_name = await upload_image(db, logo) if logo else None

        db_organization = db_models.DbOrganisation(
            name=name,
            slug=generate_slug(name),
            description=description,
            url=url,
            logo=logo_name,
        )

        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
    except Exception as e:
        log.error(e)
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
        organization.logo = await upload_image(db, logo) if logo else None

    db.commit()
    db.refresh(organization)
    return organization
