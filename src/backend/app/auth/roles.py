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
from app.db.enums import (
    HTTPStatus,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
    UserRole,
)
from app.db.models import DbProject, DbUser
from app.projects.project_deps import get_project


async def check_access(
    user: AuthUser,
    db: Connection,
    project_id: Optional[int] = None,
    role: Optional[ProjectRole] = None,
    check_completed: bool = False,
) -> Optional[DbUser]:
    """Check if the user has access to a project.

    Simplified rules:
    - Global ADMINs (`UserRole.ADMIN`) always have access.
    - For project-specific access, we check the `user_roles` table:
        * PROJECT_MANAGER: must have PROJECT_MANAGER role for the project.
        * MAPPER (or None): must have at least MAPPER role for the project.
    - `check_completed=True` blocks access to COMPLETED / ARCHIVED projects.
    """
    user_sub = await get_uid(user)

    # Global admin shortcut – no further checks
    async with db.cursor(row_factory=class_row(DbUser)) as cur:
        await cur.execute(
            """
            SELECT *
            FROM users
            WHERE sub = %(user_sub)s
            """,
            {"user_sub": user_sub},
        )
        db_user = await cur.fetchone()

    if not db_user:
        return None

    if db_user.is_admin or user.role == UserRole.ADMIN:
        return db_user

    # If no project context or no specific project role required, return user
    if project_id is None or role is None:
        return db_user

    async with db.cursor() as cur:
        # Optionally block completed / archived projects
        if check_completed:
            await cur.execute(
                """
                SELECT 1
                FROM projects
                WHERE id = %(project_id)s
                  AND status IN ('COMPLETED', 'ARCHIVED')
                """,
                {"project_id": project_id},
            )
            if await cur.fetchone():
                return None

        # Check project role
        await cur.execute(
            """
            SELECT 1
            FROM user_roles
            WHERE user_sub = %(user_sub)s
              AND project_id = %(project_id)s
              AND role = %(role)s
            """,
            {
                "user_sub": user_sub,
                "project_id": project_id,
                "role": role.value if isinstance(role, ProjectRole) else role,
            },
        )
        has_role = await cur.fetchone()

    return db_user if has_role else None


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
