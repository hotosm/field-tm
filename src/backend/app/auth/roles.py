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

from typing import Optional

from fastapi import Depends, HTTPException
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.auth_schemas import AuthUser, OrgUserDict, ProjectUserDict
from app.auth.osm import login_required
from app.db.database import get_db
from app.db.db_models import DbProject, DbUser
from app.models.enums import HTTPStatus, ProjectRole, ProjectVisibility
from app.organisations.organisation_deps import check_org_exists
from app.projects.project_deps import get_project_by_id


async def get_uid(user_data: AuthUser | DbUser) -> int:
    """Extract user id from returned OSM user."""
    try:
        user_id = user_data.id
        return user_id

    except Exception as e:
        log.error(e)
        log.error(f"Failed to get user id from auth object: {user_data}")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Auth failed. No user id present",
        ) from e


async def check_access(
    user: AuthUser,
    db: Session,
    org_id: Optional[int] = None,
    project_id: Optional[int] = None,
    role: Optional[ProjectRole] = None,
) -> Optional[DbUser]:
    """Check if the user has access to a project or organisation.

    Access is determined based on the user's role and permissions:
    - If the user has an 'ADMIN' role, access is granted.
    - If the user has a 'READ_ONLY' role, access is denied.
    - If the organisation is HOTOSM, then grant access.
    - For other roles, access is granted if the user is an organisation manager
      for the specified organisation (org_id) or has the specified role
      in the specified project (project_id).

    Args:
        user (AuthUser, int): AuthUser object, or user ID.
        db (Session): SQLAlchemy database session.
        org_id (Optional[int]): Org ID for organisation-specific access.
        project_id (Optional[int]): Project ID for project-specific access.
        role (Optional[ProjectRole]): Role to check for project-specific access.

    Returns:
        Optional[DbUser]: The user details if access is granted, otherwise None.
    """
    user_id = await get_uid(user)

    sql = text(
        """
        SELECT *
        FROM users
        WHERE id = :user_id
            AND (
                CASE
                    WHEN role = 'ADMIN' THEN true
                    WHEN role = 'READ_ONLY' THEN false
                    WHEN EXISTS (
                        SELECT 1
                        FROM organisations
                        WHERE (organisations.id = :org_id
                            AND organisations.slug = 'hotosm')
                        OR EXISTS (
                            SELECT 1
                            FROM projects
                            JOIN organisations AS org
                                ON projects.organisation_id = org.id
                            WHERE org.slug = 'hotosm'
                                AND projects.id = :project_id
                        )
                    ) THEN true
                    ELSE
                        EXISTS (
                            SELECT 1
                            FROM organisation_managers
                            WHERE organisation_managers.user_id = :user_id
                            AND organisation_managers.organisation_id = :org_id
                        )
                        OR EXISTS (
                            SELECT 1
                            FROM user_roles
                            WHERE user_roles.user_id = :user_id
                            AND user_roles.project_id = :project_id
                            AND user_roles.role >= :role
                        )
                END
            );
    """
    )

    result = db.execute(
        sql,
        {
            "user_id": user_id,
            "project_id": project_id,
            "org_id": org_id,
            "role": getattr(role, "name", None),
        },
    )
    db_user = result.first()

    if db_user:
        return DbUser(**db_user._asdict())

    return None


async def super_admin(
    user_data: AuthUser = Depends(login_required),
    db: Session = Depends(get_db),
) -> DbUser:
    """Super admin role, with access to all endpoints.

    Returns:
        user_data: DbUser SQLAlchemy object.
    """
    db_user = await check_access(user_data, db)

    if db_user:
        return db_user

    log.error(
        f"User {user_data.username} requested an admin endpoint, but is not admin"
    )
    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail="User must be an administrator"
    )


async def check_org_admin(
    db: Session,
    user: AuthUser,
    org_id: int,
) -> OrgUserDict:
    """Database check to determine if org admin role.

    Returns:
        dict: in format {'user': DbUser, 'org': DbOrganisation}.
    """
    db_org = await check_org_exists(db, org_id)

    # Check if org admin, or super admin
    db_user = await check_access(
        user,
        db,
        org_id=org_id,
    )

    if db_user:
        return {"user": db_user, "org": db_org, "project": None}

    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN,
        detail="User is not organisation admin",
    )


async def org_admin(
    project: Optional[DbProject] = Depends(get_project_by_id),
    org_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> OrgUserDict:
    """Organisation admin with full permission for projects in an organisation.

    Returns:
        dict: in format {'user': DbUser, 'org': DbOrganisation}.
    """
    if not (project or org_id):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Either org_id or project_id must be provided",
        )

    if project and org_id:
        log.error("Both org_id and project_id cannot be passed at the same time")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Both org_id and project_id cannot be passed at the same time",
        )

    # Extract org id from project if passed
    if project:
        org_id = project.organisation_id

    # Ensure org_id is provided, raise an exception otherwise
    if not org_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="org_id must be provided to check organisation admin role",
        )

    org_user_dict = await check_org_admin(
        db,
        user_data,
        org_id=org_id,
    )

    if project:
        org_user_dict["project"] = project

    return org_user_dict


async def wrap_check_access(
    project: DbProject,
    db: Session,
    user_data: AuthUser,
    role: ProjectRole,
) -> ProjectUserDict:
    """Wrap check_access call with HTTPException."""
    db_user = await check_access(
        user_data,
        db,
        project_id=project.id,
        role=role,
    )

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="User do not have permission to access the project.",
        )

    return {
        "user": db_user,
        "project": project,
    }


async def project_manager(
    project: DbProject = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> ProjectUserDict:
    """A project manager for a specific project."""
    return await wrap_check_access(
        project,
        db,
        user_data,
        ProjectRole.PROJECT_MANAGER,
    )


async def associate_project_manager(
    project: DbProject = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> ProjectUserDict:
    """An associate project manager for a specific project."""
    return await wrap_check_access(
        project,
        db,
        user_data,
        ProjectRole.ASSOCIATE_PROJECT_MANAGER,
    )


async def field_manager(
    project: DbProject = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> ProjectUserDict:
    """A field manager for a specific project."""
    return await wrap_check_access(
        project,
        db,
        user_data,
        ProjectRole.FIELD_MANAGER,
    )


async def validator(
    project: DbProject = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> ProjectUserDict:
    """A validator for a specific project."""
    return await wrap_check_access(
        project,
        db,
        user_data,
        ProjectRole.VALIDATOR,
    )


async def mapper(
    project: DbProject = Depends(get_project_by_id),
    db: Session = Depends(get_db),
    user_data: AuthUser = Depends(login_required),
) -> ProjectUserDict:
    """A mapper for a specific project."""
    # If project is public, skip permission check
    if project.visibility == ProjectVisibility.PUBLIC:
        user_id = user_data.id
        sql = text("SELECT * FROM users WHERE id = :user_id;")
        result = db.execute(sql, {"user_id": user_id})
        db_user = result.first()

        if not db_user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User ({user_id}) does not exist in database",
            )

        return {
            "user": DbUser(**db_user._asdict()),
            "project": project,
        }

    return await wrap_check_access(
        project,
        db,
        user_data,
        ProjectRole.MAPPER,
    )
