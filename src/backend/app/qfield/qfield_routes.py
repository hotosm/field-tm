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
"""Routes to relay requests to QFieldCloud server (Litestar)."""

from litestar import Router, delete, get, post
from litestar import status_codes as status
from litestar.di import Provide
from litestar.params import Parameter
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.roles import project_manager, super_admin
from app.db.database import db_conn
from app.qfield import qfield_schemas
from app.qfield.qfield_crud import (
    create_qfield_project,
    delete_qfield_project,
    qfc_credentials_test,
)
from app.qfield.qfield_deps import qfield_client


@get(
    "/projects",
    summary="List projects in QFieldCloud.",
    dependencies={
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
)
async def list_projects() -> dict:
    """List projects in QFieldCloud."""
    async with qfield_client() as client:
        projects = client.list_projects()
        return projects


@post(
    "/projects",
    summary="Attempt to generate the QFieldCloud project from FieldTM project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def trigger_qfield_project_create(
    db: AsyncConnection,
    auth_user: AuthUser,
    project_id: int = Parameter(),
) -> dict[str, str]:
    """Attempt to generate the QFieldCloud project from FieldTM project.

    The QField project should be created in /projects/generate-project-data,
    however, if this fails, we can trigger the project creation again via this
    endpoint.
    """
    # For this endpoint, we need to manually check permissions
    # since it doesn't have project_id in the path
    from app.auth.roles import wrap_check_access
    from app.db.enums import ProjectRole
    from app.db.models import DbProject

    project = await DbProject.one(db, project_id, warn_on_missing_token=False)
    project_user = await wrap_check_access(
        project,
        db,
        auth_user,
        ProjectRole.PROJECT_ADMIN,
        check_completed=False,
    )
    qfield_url = await create_qfield_project(db, project_user.get("project"))
    # Redirect to qfieldcloud project dashboard
    return {"url": qfield_url}


@post(
    "/test-credentials",
    summary="Test QFieldCloud credentials by attempting to open a session.",
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
    status_code=status.HTTP_200_OK,
)
async def qfc_creds_test(
    qfc_creds: qfield_schemas.QFieldCloud,
) -> None:
    """Test QFieldCloud credentials by attempting to open a session."""
    await qfc_credentials_test(qfc_creds)
    return None


@delete(
    "/{project_id:int}",
    summary="Delete a project from QFieldCloud.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(project_manager),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def trigger_delete_qfield_project(
    project_id: int,
    current_user: ProjectUserDict,
    db: AsyncConnection,
    auth_user: AuthUser,
) -> None:
    """Delete a project from QFieldCloud."""
    await delete_qfield_project(db, project_id)
    return None


qfield_router = Router(
    path="/qfield",
    tags=["qfield"],
    route_handlers=[
        list_projects,
        trigger_qfield_project_create,
        qfc_creds_test,
        trigger_delete_qfield_project,
    ],
)
