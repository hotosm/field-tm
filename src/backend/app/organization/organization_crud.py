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
from fastapi import HTTPException, File,UploadFile
from fastapi.logger import logger as logger
import re

from sqlalchemy.orm import Session

from ..db import db_models


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

async def create_organization(db: Session, name:str, description:str, url:str, type:int, logo: UploadFile = File(...)):
    # create new project
    try:
        db_organization = db_models.DbOrganisation(
            name=name,
            slug = generate_slug(name),
            description=description,
            url=url,
            # type=type,
        )
        file_path = os.path.join("app/images")

        # Save logo file to assets folder
        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except OSError:
                pass

        with open(file_path+'/'+logo.filename, "wb") as file:
            file.write(await logo.read())
            file.close()

        db_organization.logo = logo.filename
        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=f" ----- Error: {e}"
        ) from e

    return True

