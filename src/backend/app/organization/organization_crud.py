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
import string
from fastapi import HTTPException, File,UploadFile
from fastapi.logger import logger as logger
import re

from sqlalchemy.orm import Session

from ..db import db_models

IMAGEDIR = "app/images/"

# --------------
# ---- CRUD ----
# --------------


def get_organisations(
    db: Session,
):
    db_organisation = db.query(db_models.DbOrganisation).all()
    return db_organisation

def generate_slug(text: str) -> str:
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '-')
    # Remove consecutive hyphens
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


async def get_organisation_by_name(db: Session, name: str):

    # Construct the SQL query with the case-insensitive search
    query = f"SELECT * FROM organisations WHERE LOWER(name) LIKE LOWER('%{name}%') LIMIT 1"

    # Execute the query and retrieve the result
    result = db.execute(query)

    # Fetch the first row of the result
    db_organisation = result.fetchone()
    return db_organisation


async def create_organization(db: Session, name: str, description: str, url: str, logo: UploadFile = File(...)):
    """
    Creates a new organization with the given name, description, url, type, and logo.
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
        db_organization = db_models.DbOrganisation(
            name=name,
            slug=generate_slug(name),
            description=description,
            url=url
        )

        # Save logo file to app/images folder
        # file_path = os.path.join("app/images")
        # if not os.path.exists(file_path):
        #     os.makedirs(file_path)

        # with open(os.path.join(file_path, logo.filename), "wb") as file:
        #     file.write(await logo.read())

        db_organization.logo = logo.filename if logo else None
        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=f" ----- Error: {e}"
        ) from e

    return True

