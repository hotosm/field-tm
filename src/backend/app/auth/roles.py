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

"""User roles authorisation Depends methods.

These methods use FastAPI Depends for dependency injection
and always return an AuthUser object in a standard format.
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_logic import get_uid
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.db.database import db_conn
from app.db.enums import HTTPStatus, ProjectRole, ProjectStatus, ProjectVisibility
from app.db.models import DbProject, DbUser
from app.projects.project_deps import get_project


async def check_access(
    user: AuthUser,
    db: Connection,
    org_id: Optional[int] = None,
    project_id: Optional[int] = None,
    role: Optional[ProjectRole] = None,
    check_completed: bool = False,
) -> Optional[DbUser]:
    """Check if the user has access to a project or organisation.

    Access is determined based on the user's role and permissions:
    - If the user has an 'ADMIN' role, access is granted.
    - If the user has a 'READ_ONLY' role, access is denied.
    - For other roles, access is granted if the user is an organisation manager
      for the specified organisation (org_id) or has the specified role
      in the specified project (project_id).
    - If only project_id is provided, the user's organization manager status
      for the organization linked to the project is also checked.

    Args:
        user (AuthUser): AuthUser object, or user ID.
        db (Connection): The database connection.
        org_id (Optional[int]): Org ID for organisation-specific access.
        project_id (Optional[int]): Project ID for project-specific access.
        role (Optional[ProjectRole]): Role to check for project-specific access.
        check_completed (bool): If True, check if project is completed.

    Returns:
        Optional[DbUser]: The user details if access is granted,
            otherwise None.
    """
    user_sub = await get_uid(user)

    sql = """
        WITH role_hierarchy AS (
            SELECT 'MAPPER' AS role, 0 AS level
            UNION ALL SELECT 'VALIDATOR', 1
            UNION ALL SELECT 'FIELD_MANAGER', 2
            UNION ALL SELECT 'ASSOCIATE_PROJECT_MANAGER', 3
            UNION ALL SELECT 'PROJECT_MANAGER', 4
        )

        SELECT *
        FROM users
        WHERE sub = %(user_sub)s
            AND (
                CASE
                    -- Simple check to see if ADMIN or blocked (READ_ONLY)
                    WHEN role = 'ADMIN'::public.userrole THEN true
                    WHEN role = 'READ_ONLY'::public.userrole THEN false
                    ELSE
                        -- Check if project is completed and check_completed is true
                        NOT (
                            %(check_completed)s
                            AND EXISTS (
                                SELECT 1
                                FROM projects
                                WHERE id = %(project_id)s
                                    AND status IN (
                                            'COMPLETED'::public.projectstatus,
                                            'ARCHIVED'::public.projectstatus
                                        )
                                    )
                        )
                        AND (
                            -- Check to see if user is org admin
                            EXISTS (
                                SELECT 1
                                FROM organisation_managers
                                WHERE organisation_managers.user_sub = %(user_sub)s
                                AND organisation_managers.organisation_id = %(org_id)s
                            )

                            -- Check to see if user has equal or greater than project
                            -- role
                            OR EXISTS (
                                SELECT 1
                                FROM user_roles
                                JOIN role_hierarchy AS user_role_h
                                    ON user_roles.role::public.projectrole
                                        = user_role_h.role::public.projectrole
                                JOIN role_hierarchy AS required_role_h
                                    ON %(role)s::public.projectrole
                                        = required_role_h.role::public.projectrole
                                WHERE user_roles.user_sub = %(user_sub)s
                                AND user_roles.project_id = %(project_id)s
                                AND user_role_h.level >= required_role_h.level
                            )

                            -- Extract organisation id from project,
                            -- then check to see if user is org admin
                            OR (
                                %(org_id)s IS NULL
                                AND EXISTS (
                                    SELECT 1
                                    FROM organisation_managers
                                    JOIN projects
                                        ON projects.organisation_id =
                                            organisation_managers.organisation_id
                                    WHERE organisation_managers.user_sub = %(user_sub)s
                                    AND projects.id = %(project_id)s
                                )
                            )
                        )
                END
            );
    """

    async with db.cursor(row_factory=class_row(DbUser)) as cur:
        await cur.execute(
            sql,
            {
                "user_sub": user_sub,
                "project_id": project_id,
                "org_id": org_id,
                "role": getattr(role, "name", None),
                "check_completed": check_completed,
            },
        )
        db_user = await cur.fetchone()

    return db_user if db_user else None


async def super_admin(
    current_user: Annotated[AuthUser, Depends(login_required)],
    db: Annotated[Connection, Depends(db_conn)],
) -> DbUser:
    """Super admin role, with access to all endpoints.

    Returns:
        current_user: DbUser Pydantic model.
    """
    db_user = await check_access(current_user, db)

    if db_user:
        return db_user

    log.error(
        f"User {current_user.username} requested an admin endpoint, but is not admin"
    )
    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail="User must be an administrator"
    )


async def wrap_check_access(
    project: DbProject,
    db: Connection,
    user_data: AuthUser,
    role: ProjectRole,
    check_completed: bool = False,
) -> ProjectUserDict:
    """Wrap check_access call with HTTPException."""
    db_user = await check_access(
        user_data,
        db,
        project_id=project.id,
        role=role,
        check_completed=check_completed,
    )

    if not db_user:
        msg = "User does not have permission to access the project."
        # NOTE workaround to allow a mix of svcfmtm access on mapper frontend
        # for public projects, but also blocking access for svcfmtm on
        # mapper frontend if the project is private. We must send 401 and
        # not 403 to make managing this easier
        if user_data.username == "svcfmtm":
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail=msg)
        else:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=msg)

    return {
        "user": db_user,
        "project": project,
    }


class ProjectManager:
    """A wrapper for the project manager to restrict access if project is completed."""

    def __init__(self, check_completed: bool = False):
        """Initialize the project manager with check_completed flag."""
        self.check_completed = check_completed

    async def __call__(
        self,
        project_id: int,
        db: Annotated[Connection, Depends(db_conn)],
        current_user: Annotated[AuthUser, Depends(login_required)],
    ) -> ProjectUserDict:
        """A project manager for a specific project."""
        # NOTE here we get the project manually to avoid warnings before the project
        # if fully created yet (about odk_token not existing)
        project = await DbProject.one(db, project_id, warn_on_missing_token=False)
        return await wrap_check_access(
            project,
            db,
            current_user,
            ProjectRole.PROJECT_MANAGER,
            check_completed=self.check_completed,
        )


async def associate_project_manager(
    project: Annotated[DbProject, Depends(get_project)],
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> ProjectUserDict:
    """An associate project manager for a specific project."""
    return await wrap_check_access(
        project,
        db,
        current_user,
        ProjectRole.ASSOCIATE_PROJECT_MANAGER,
    )


async def field_manager(
    project: Annotated[DbProject, Depends(get_project)],
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> ProjectUserDict:
    """A field manager for a specific project."""
    return await wrap_check_access(
        project,
        db,
        current_user,
        ProjectRole.FIELD_MANAGER,
    )


async def validator(
    project: Annotated[DbProject, Depends(get_project)],
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> ProjectUserDict:
    """A validator for a specific project."""
    return await wrap_check_access(
        project,
        db,
        current_user,
        ProjectRole.VALIDATOR,
    )


class Mapper:
    """A wrapper for the mapper to restrict access if project is completed."""

    def __init__(self, check_completed: bool = False):
        """Initialize the mapper with check_completed flag."""
        self.check_completed = check_completed

    async def __call__(
        self,
        project: Annotated[DbProject, Depends(get_project)],
        db: Annotated[Connection, Depends(db_conn)],
        # Here temp auth token/cookie is allowed
        current_user: Annotated[AuthUser, Depends(public_endpoint)],
    ) -> ProjectUserDict:
        """A mapper for a specific project."""
        if self.check_completed and project.status in [
            ProjectStatus.COMPLETED,
            ProjectStatus.ARCHIVED,
        ]:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Project is locked since it is in {project.status.value} "
                "state.",
            )

        # If project is public, skip permission check
        if project.visibility == ProjectVisibility.PUBLIC:
            return {
                "user": await DbUser.one(db, current_user.sub),
                "project": project,
            }

        # As the default user for temp auth (svcfmtm) does not have valid permissions
        # on any project, this will block access for temp login users on projects
        # that are not public
        return await wrap_check_access(
            project,
            db,
            current_user,
            ProjectRole.MAPPER,
            check_completed=self.check_completed,
        )


async def project_contributors(
    project: Annotated[DbProject, Depends(get_project)],
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[AuthUser, Depends(login_required)],
) -> ProjectUserDict:
    """A contributor to a specific project."""
    user_sub = current_user.sub
    org_id = project.organisation_id

    query = """
        SELECT * FROM users
        WHERE sub = %(user_sub)s
            AND (
                CASE
                WHEN %(visibility)s = 'PRIVATE' THEN
                    CASE
                    WHEN role = 'ADMIN' THEN true
                    WHEN EXISTS (
                        SELECT 1 FROM organisation_managers
                        WHERE organisation_managers.user_sub = %(user_sub)s
                            AND organisation_managers.organisation_id = %(org_id)s
                    ) THEN true
                    WHEN EXISTS (
                        SELECT 1 FROM user_roles
                        WHERE user_roles.user_sub = %(user_sub)s
                            AND user_roles.project_id = %(project_id)s
                            AND user_roles.role = 'PROJECT_MANAGER'
                    ) THEN true
                    WHEN EXISTS (
                        SELECT 1 FROM projects
                        WHERE projects.author_sub = %(user_sub)s
                            AND projects.id = %(project_id)s
                    ) THEN true
                    WHEN EXISTS (
                        SELECT 1 FROM task_events
                        WHERE task_events.user_sub = %(user_sub)s
                            AND task_events.project_id = %(project_id)s
                    ) THEN true
                    ELSE false
                    END
                ELSE true
                END
            );
    """
    async with db.cursor() as cur:
        await cur.execute(
            query,
            {
                "user_sub": user_sub,
                "project_id": project.id,
                "org_id": org_id,
                "visibility": project.visibility,
            },
        )
        db_user = await cur.fetchone()

    if db_user:
        return {
            "user": db_user,
            "project": project,
        }

    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN,
        detail="You must be a project contributor to access this resource.",
    )
