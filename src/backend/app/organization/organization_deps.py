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

"""Organization dependencies for use in Depends."""

from typing import Union

from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger as log
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_models import DbOrganisation
from app.models.enums import HTTPStatus


async def get_organization_by_name(db: Session, org_name: str) -> DbOrganisation:
    """Get an organization from the db by name.

    Args:
        db (Session): database session
        org_name (int): id of the organization

    Returns:
        DbOrganisation: organization with the given id
    """
    return (
        db.query(DbOrganisation)
        .filter(func.lower(DbOrganisation.name).like(func.lower(f"%{org_name}%")))
        .first()
    )


async def get_organisation_by_id(db: Session, org_id: int) -> DbOrganisation:
    """Get an organization from the db by id.

    Args:
        db (Session): database session
        org_id (int): id of the organization

    Returns:
        DbOrganisation: organization with the given id
    """
    return db.query(DbOrganisation).filter(DbOrganisation.id == org_id).first()


async def org_exists(
    org_id: Union[str, int],
    db: Session = Depends(get_db),
) -> DbOrganisation:
    """Check if organization name exists, else error.

    The org_id can also be an org name.
    """
    try:
        org_id = int(org_id)
    except ValueError:
        pass

    if isinstance(org_id, int):
        log.debug(f"Getting organization by id: {org_id}")
        db_organization = await get_organisation_by_id(db, org_id)

    if isinstance(org_id, str):
        log.debug(f"Getting organization by name: {org_id}")
        db_organization = await get_organization_by_name(db, org_id)

    if not db_organization:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Organization {org_id} does not exist",
        )

    log.debug(f"Organization match: {db_organization}")
    return db_organization
