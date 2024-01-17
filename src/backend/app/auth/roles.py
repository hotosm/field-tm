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

"""User roles authorisation Depends methods.

These methods use FastAPI Depends for dependency injection
and always return an AuthUser object in a standard format.
"""

from fastapi import Depends, HTTPException
from loguru import logger as log
from sqlalchemy.orm import Session

from app.auth.osm import AuthUser, login_required
from app.db.database import get_db
from app.db.db_models import DbProject, DbUser, DbUserRoles
from app.models.enums import HTTPStatus, ProjectRole, UserRole
from app.projects.project_deps import get_project_by_id


async def get_uid(user_data: AuthUser) -> int:
    """Extract user id from returned OSM user."""
    if user_id := user_data.get("id"):
        return user_id
    else:
        log.error(f"Failed to get user id from auth object: {user_data}")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Auth failed. No user id present",
        )


async def super_admin(
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> AuthUser:
    """Super admin role, with access to all endpoints."""
    user_id = await get_uid(user_data)

    match = db.query(DbUser).filter_by(id=user_id, role=UserRole.ADMIN).first()

    if not match:
        log.error(f"User ID {user_id} requested an admin endpoint, but is not admin")
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="User must be an administrator"
        )

    return user_data


async def org_admin(
    project: DbProject = Depends(get_project_by_id),
    org_id: int = None,
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> AuthUser:
    """Organization admin with full permission for projects in an organization."""
    user_id = await get_uid(user_data)

    org_admin = (
        db.query(DbUserRoles)
        .filter_by(user_id=user_id, role=ProjectRole.ORGANIZATION_ADMIN)
        .first()
    )

    if not org_admin:
        log.error(f"User ID {user_id} is not an admin for any organization")
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="User must be an organization admin",
        )

    matched_project = db.query(DbProject).filter_by(id=org_admin.project_id).first()
    matched_org_id = matched_project.organisation_id

    if (
        org_id
        and matched_org_id == org_id
        or project
        and matched_org_id == project.organisation_id
    ):
        return user_data

    log.error(f"User ID {user_id} is not an organization admin for id {org_id}")
    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail="User is not an organization admin"
    )


async def validator(
    project_id: int,
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> AuthUser:
    """A validator for a specific project."""
    user_id = await get_uid(user_data)

    match = (
        db.query(DbUserRoles).filter_by(user_id=user_id, project_id=project_id).first()
    )

    if not match:
        log.error(f"User ID {user_id} has no access to project ID {project_id}")
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="User has no access to project"
        )

    if match.role.value < ProjectRole.VALIDATOR.value:
        log.error(
            f"User ID {user_id} does not have validator permission"
            f"for project ID {project_id}"
        )
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="User is not a validator for this project",
        )

    return user_data
