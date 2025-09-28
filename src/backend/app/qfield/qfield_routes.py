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
"""Routes to relay requests to QFieldCloud server."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import RedirectResponse
from psycopg import Connection

from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import ProjectManager
from app.db.database import db_conn
from app.qfield.qfield_crud import create_qfield_project
from app.qfield.qfield_deps import qfield_client

router = APIRouter(
    prefix="/qfield",
    tags=["qfield"],
    responses={404: {"description": "Not found"}},
)


@router.get("/projects")
async def list_projects():
    """List projects in QFieldCloud."""
    async with qfield_client() as client:
        projects = client.list_projects()
        return projects


@router.post("/projects")
async def trigger_qfield_project_create(
    db: Annotated[Connection, Depends(db_conn)],
    project_user_dict: Annotated[ProjectUserDict, Depends(ProjectManager())],
):
    """Attempt to generate the QFieldCloud project from FieldTM project.

    The QField project should be created in /projects/generate-project-data,
    however, if this fails, we can trigger the project creation again via this
    endpoint.
    """
    project = project_user_dict.get("project")
    qfield_url = await create_qfield_project(db, project)
    # Redirect to qfieldcloud project dashboard
    return RedirectResponse(qfield_url)
