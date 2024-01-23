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

"""Organisation dependencies for use in Depends."""

from typing import Union

from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger as log
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_models import DbOrganisation, DbProject
from app.models.enums import HTTPStatus
from app.projects import project_deps


async def get_organisation_by_name(
    db: Session, org_name: str, check_approved: bool = True
) -> DbOrganisation:
    """Get an organisation from the db by name.

    Args:
        db (Session): database session
        org_name (int): id of the organisation
        check_approved (bool): first check if the organisation is approved

    Returns:
        DbOrganisation: organisation with the given id
    """
    org_obj = (
        db.query(DbOrganisation)
        .filter(func.lower(DbOrganisation.name).like(func.lower(f"%{org_name}%")))
        .first()
    )
    if org_obj and check_approved and org_obj.approved is False:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Organisation ({org_obj.id}) is not approved yet",
        )
    return org_obj


async def get_organisation_by_id(
    db: Session, org_id: int, check_approved: bool = True
) -> DbOrganisation:
    """Get an organisation from the db by id.

    Args:
        db (Session): database session
        org_id (int): id of the organisation
        check_approved (bool): first check if the organisation is approved

    Returns:
        DbOrganisation: organisation with the given id
    """
    org_obj = db.query(DbOrganisation).filter_by(id=org_id).first()
    if org_obj and check_approved and org_obj.approved is False:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Organisation {org_id} is not approved yet",
        )
    return org_obj


async def check_org_exists(
    db: Session,
    org_id: Union[str, int],
    check_approved: bool = True,
) -> DbOrganisation:
    """Check if organisation name exists, else error.

    The org_id can also be an org name.
    """
    try:
        org_id = int(org_id)
    except ValueError:
        pass

    if isinstance(org_id, int):
        log.debug(f"Getting organisation by id: {org_id}")
        db_organisation = await get_organisation_by_id(db, org_id, check_approved)

    if isinstance(org_id, str):
        log.debug(f"Getting organisation by name: {org_id}")
        db_organisation = await get_organisation_by_name(db, org_id, check_approved)

    if not db_organisation:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Organisation {org_id} does not exist",
        )

    log.debug(f"Organisation match: {db_organisation}")
    return db_organisation


async def org_exists(
    org_id: Union[str, int],
    db: Session = Depends(get_db),
) -> DbOrganisation:
    """Wrapper for check_org_exists to be used as a route dependency.

    Requires Depends from a route.
    """
    return await check_org_exists(db, org_id)


async def org_from_project(
    project: DbProject = Depends(project_deps.get_project_by_id),
    db: Session = Depends(get_db),
) -> DbOrganisation:
    """Get an organisation from a project id."""
    return await check_org_exists(db, project.organisation_id)
