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

"""Organisation dependencies for use in Depends."""

import os
from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import login_required
from app.auth.auth_schemas import AuthUser
from app.central import central_schemas
from app.db.database import db_conn
from app.db.enums import HTTPStatus, UserRole
from app.db.models import DbOrganisation, DbOrganisationManagers, DbProject
from app.projects.project_deps import get_project


async def get_organisation(
    db: Annotated[Connection, Depends(db_conn)],
    id: str | int,
    check_approved: bool = True,
) -> DbOrganisation:
    """Return an organisation from the DB, else exception.

    Args:
        id (str | int): The organisation ID (integer) or name (string) to check.
        db (Connection): The database connection.
        check_approved (bool): Throw error if org is not approved yet.

    Returns:
        DbOrganisation: The organisation if found.

    Raises:
        HTTPException: Raised with a 404 status code if the user is not found.
    """
    try:
        try:
            # Is ID (int)
            id = int(id)
        except ValueError:
            # Is name (str)
            pass
        db_org = await DbOrganisation.one(db, id)

    except KeyError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    if check_approved and db_org.approved is False:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f"Organisation ({id}) is not approved yet.",
        )

    return db_org


async def get_org_odk_creds(
    org: DbOrganisation,
) -> central_schemas.ODKCentralDecrypted:
    """Get odk credentials for an organisation, else error."""
    url = org.odk_central_url
    user = org.odk_central_user
    password = org.odk_central_password

    if not all([url, user, password]):
        log.info(
            """Organisation does not have ODK Central credentials configured
            using default hotosm credentials""",
        )
        default_creds = await get_default_odk_creds()
        return central_schemas.ODKCentralDecrypted(**default_creds.dict())

    return central_schemas.ODKCentralDecrypted(
        odk_central_url=url,
        odk_central_user=user,
        odk_central_password=password,
    )


async def get_default_odk_creds():
    """Get default odk credentials."""
    return central_schemas.ODKCentralIn(
        odk_central_url=os.getenv("ODK_CENTRAL_URL"),
        odk_central_user=os.getenv("ODK_CENTRAL_USER"),
        odk_central_password=os.getenv("ODK_CENTRAL_PASSWD"),
    )


async def org_exists(
    org_id: int | str,
    db: Annotated[Connection, Depends(db_conn)],
) -> DbOrganisation:
    """Wrapper for to check an org exists in a route dependency.

    Requires Depends from a route.
    """
    if not org_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Organisation id not provided",
        )

    return await get_organisation(db, org_id, check_approved=False)


async def org_from_project(
    project: Annotated[DbProject, Depends(get_project)],
    db: Annotated[Connection, Depends(db_conn)],
) -> DbOrganisation:
    """Get an organisation from a project id."""
    return await get_organisation(db, project.organisation_id)


async def org_or_project_manager(
    org_id: int,
    db: Connection = Depends(db_conn),
    current_user: AuthUser = Depends(login_required),
):
    """Authorize user if they are an admin, org manager, or project manager in the org.

    Args:
        org_id (int): Organisation ID.
        db (Connection): Database connection.
        current_user (AuthUser): Authenticated user.

    Returns:
        dict: Contains the user and organisation.

    Raises:
        HTTPException: If the user lacks required permissions.
    """
    # Check if user is admin
    if current_user.role == UserRole.ADMIN:
        org = await DbOrganisation.one(db, org_id)
        return {"user": current_user, "org": org}
    # Check if user is org manager
    org_managers = await DbOrganisationManagers.get(db, org_id, current_user.sub)
    if org_managers:
        org = await DbOrganisation.one(db, org_id)
        return {"user": current_user, "org": org}
    # Check if user is project manager for any project in the org
    sql = """
        SELECT 1 FROM user_roles ur
        JOIN projects p ON ur.project_id = p.id
        WHERE ur.user_sub = %(user_sub)s
        AND ur.role = 'PROJECT_MANAGER'
        AND p.organisation_id = %(org_id)s
        LIMIT 1
    """
    async with db.cursor() as cur:
        await cur.execute(sql, {"user_sub": current_user.sub, "org_id": org_id})
        if await cur.fetchone():
            org = await DbOrganisation.one(db, org_id)
            return {"user": current_user, "org": org}
    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN,
        detail="""You must be an admin, organisation manager, or
        project manager to access this resource.""",
    )
