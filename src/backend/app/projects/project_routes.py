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
"""Endpoints for Field-TM projects (Litestar)."""

import json
import logging
from typing import Optional

from litestar import Response, Router, delete, get, patch
from litestar import status_codes as status
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from osm_fieldwork.json_data_models import get_choices
from psycopg import AsyncConnection

from app.auth.auth_deps import login_required, public_endpoint
from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import project_manager, super_admin
from app.central import central_crud
from app.db.database import db_conn
from app.db.enums import ProjectStatus
from app.db.models import (
    DbProject,
    DbUser,
    FieldMappingApp,
)
from app.helpers import helper_schemas
from app.projects import project_crud, project_deps, project_schemas
from app.qfield.qfield_crud import delete_qfield_project

log = logging.getLogger(__name__)


@get(
    "/all",
    summary="Return all projects.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(public_endpoint),
    },
    return_dto=project_schemas.ProjectOut,
)
async def read_projects(
    db: AsyncConnection,
    user_sub: Optional[str] | None = None,
    skip: Optional[int] = 0,
    limit: Optional[int] = 100,
    hashtags: Optional[list[str]] = None,
) -> list[DbProject]:
    """Return all projects."""
    projects = await DbProject.all(db, skip, limit, user_sub, hashtags)
    return projects or []


@get(
    "/summaries",
    summary="Get a paginated summary of projects.",
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
    return_dto=project_schemas.ProjectSummary,
)
async def read_project_summaries(
    db: AsyncConnection,
    page: int = Parameter(default=1, ge=1),
    results_per_page: int = Parameter(default=13, le=100),
    user_sub: str | None = Parameter(default=None),
    hashtags: str | None = Parameter(default=None),
    search: str | None = Parameter(default=None),
    country: str | None = Parameter(default=None),
    status: ProjectStatus | None = Parameter(default=None),
    field_mapping_app: FieldMappingApp | None = Parameter(default=None),
) -> helper_schemas.PaginatedResponse[DbProject]:
    """Get a paginated summary of projects.

    NOTE this is a public endpoint with no auth requirements.
    """
    return await project_crud.get_paginated_projects(
        db,
        page,
        results_per_page,
        user_sub,
        hashtags,
        search,
        status,
        field_mapping_app,
        country=country,
    )


@get(
    "/categories",
    summary="Get all project categories.",
    dependencies={
        "auth_user": Provide(public_endpoint),
    },
)
async def get_categories() -> dict:
    """Get api for fetching all the categories.

    This endpoint fetches all the categories from osm_fieldwork.

    ## Response
    - Returns a JSON object containing a list of categories and their respective forms.

    """
    # Categories are fetched from osm_fieldwork.data_models.get_choices().
    categories = get_choices()
    return categories


@get(
    "/{project_id:int}",
    summary="Get a specific project by ID.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(public_endpoint),
    },
    return_dto=project_schemas.ProjectOut,
)
async def read_project(
    project_id: int,
    db: AsyncConnection,
) -> DbProject:
    """Get a specific project by ID."""
    try:
        return await DbProject.one(db, project_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ({project_id}) not found.",
        ) from e


@get(
    "/{project_id:int}/download",
    summary="Download the project boundary as GeoJSON.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(public_endpoint),
    },
)
async def download_project_boundary(
    project_id: int,
    db: AsyncConnection,
) -> Response:
    """Downloads the boundary of a project as a GeoJSON file."""
    try:
        project = await DbProject.one(db, project_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ({project_id}) not found.",
        ) from e

    geojson_bytes = json.dumps(project.outline).encode("utf-8")
    headers = {
        "Content-Disposition": f"attachment; filename={project.slug}.geojson",
        "Content-Type": "application/media",
    }
    return Response(
        content=geojson_bytes,
        headers=headers,
        status_code=status.HTTP_200_OK,
    )


@patch(
    "/{project_id:int}",
    summary="Partially update an existing project.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user_dict": Provide(project_manager),
    },
    return_dto=project_schemas.ProjectOut,
)
async def update_project(
    data: project_schemas.ProjectUpdate,
    project_id: int,
    current_user_dict: ProjectUserDict,
    db: AsyncConnection,
) -> DbProject:
    """Partial update an existing project."""
    # NOTE this does not including updating the ODK project name
    # If password is None but URL/username are provided,
    # preserve existing encrypted password
    project = current_user_dict.get("project")
    if (
        (data.external_project_instance_url or data.external_project_username)
        and not data.external_project_password
        and project.external_project_password_encrypted
    ):
        # Password is None, so set password_encrypted to preserve
        # existing encrypted password (allows validation to pass)
        data.password_encrypted = project.external_project_password_encrypted

    return await DbProject.update(db, project.id, data)


@delete(
    "/{project_id:int}",
    summary="Delete a project from ODK Central and the local database.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
        "current_user": Provide(super_admin),
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    db: AsyncConnection,
    current_user: DbUser,
) -> None:
    """Delete a project from both ODK Central and the local database."""
    project = await project_deps.get_project_by_id(db, project_id)

    log.info(
        f"User {current_user.username} attempting deletion of project {project.id}"
    )

    # Handle QField projects separately
    if project.field_mapping_app == FieldMappingApp.QFIELD:
        log.info(f"Deleting QFieldCloud project for FieldTM project ({project.id})")
        await delete_qfield_project(db, project.id)
    else:
        # Delete ODK Central project
        log.info(f"Deleting ODK Central project for FieldTM project ({project.id})")
        # Use None for credentials to fall back to environment variables
        await central_crud.delete_odk_project(project.external_project_id, None)

    # Delete Field-TM project
    await DbProject.delete(db, project.id)

    log.info(f"Deletion of project {project.id} successful")
    return None


project_router = Router(
    path="/projects",
    tags=["projects"],
    route_handlers=[
        read_projects,
        read_project_summaries,
        get_categories,
        read_project,
        download_project_boundary,
        update_project,
        delete_project,
    ],
)
