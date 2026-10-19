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

These methods use dependency injection and always return
an AuthUser object in a standard format.
"""

import logging
from typing import Optional

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.auth.auth_deps import get_user_sub
from app.auth.auth_schemas import ProjectUserDict
from app.db.enums import ProjectRole, ProjectVisibility
from app.db.models import DbProject, DbUser
from app.i18n import _
from app.projects.project_deps import get_project_by_id

log = logging.getLogger(__name__)


async def check_access(
    user: object,
    db: AsyncConnection,
    project_id: Optional[int] = None,
    role: Optional[ProjectRole] = None,
    check_completed: bool = False,
) -> Optional[DbUser]:
    """Check if the user has access to a project.

    - Global admins always have access.
    - The project creator, or a user with PROJECT_MANAGER in `user_roles`,
      has PROJECT_MANAGER (and MAPPER) access.
    - MAPPER access also accepts a MAPPER role in `user_roles`.
    - `check_completed=True` blocks access to COMPLETED / ARCHIVED projects.
    """
    user_sub = get_user_sub(user)

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

    if db_user.is_admin or getattr(user, "is_admin", False):
        return db_user

    # If no project context or no specific project role required, return user
    if project_id is None or role is None:
        return db_user

    # Project creators manage their own projects; managers may also map.
    roles = [ProjectRole.PROJECT_MANAGER.value]
    if role == ProjectRole.MAPPER:
        roles.append(ProjectRole.MAPPER.value)
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT 1
            FROM projects p
            WHERE p.id = %(project_id)s
              AND NOT (
                %(check_completed)s AND p.status IN ('COMPLETED', 'ARCHIVED')
              )
              AND (
                p.created_by_sub = %(user_sub)s
                OR EXISTS (
                    SELECT 1 FROM user_roles ur
                    WHERE ur.project_id = p.id
                      AND ur.user_sub = %(user_sub)s
                      AND ur.role = ANY(%(roles)s::projectrole[])
                )
              )
            """,
            {
                "user_sub": user_sub,
                "project_id": project_id,
                "roles": roles,
                "check_completed": check_completed,
            },
        )
        has_role = await cur.fetchone()

    return db_user if has_role else None


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=_("User does not have permission to access the project."),
    )


async def wrap_check_access(
    project: DbProject,
    db: AsyncConnection,
    user_data: object,
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
        raise _forbidden()
    return {"user": db_user, "project": project}


async def project_manager(
    project_id: int,
    db: AsyncConnection,
    auth_user: object,
    check_completed: bool = False,
) -> ProjectUserDict:
    """Only allow access to project managers (or global admins).

    Permission is checked before the (large) project row is loaded.
    """
    db_user = await check_access(
        auth_user,
        db,
        project_id=project_id,
        role=ProjectRole.PROJECT_MANAGER,
        check_completed=check_completed,
    )
    if not db_user:
        raise _forbidden()
    project = await get_project_by_id(db, project_id)
    return {"user": db_user, "project": project}


async def ensure_project_viewable(
    db: AsyncConnection,
    project: DbProject,
    auth_user: object | None,
) -> None:
    """Public projects are open to guests; private ones need a project role."""
    if project.visibility == ProjectVisibility.PUBLIC:
        return
    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("You must be logged in to view this project."),
        )
    await wrap_check_access(project, db, auth_user, ProjectRole.MAPPER)
