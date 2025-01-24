# Copyright (c) Humanitarian OpenStreetMap Team
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
"""Routes to integrate with external apps, via an API key.

We handle these endpoints separately to minimise the attach surface
possible from misused API keys (so the entire API is not accessible).

API keys are inherently not as secure as OAuth flow / JWT token combo.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.auth.roles import super_admin
from app.central.central_crud import update_entity_mapping_status
from app.central.central_schemas import EntityMappingStatus, EntityMappingStatusIn
from app.db.database import db_conn
from app.db.enums import HTTPStatus
from app.db.models import DbProject, DbUser
from app.integrations.integration_crud import (
    generate_api_token,
)
from app.integrations.integration_deps import valid_api_token
from app.projects.project_deps import get_project

router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/api-token")
async def get_api_token(
    current_user: Annotated[DbUser, Depends(super_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Generate and return a new API token.

    This can only be accessed once, and is regenerated on
    each call to this endpoint.

    Be sure to store it someplace safe, like a password manager.

    NOTE currently requires super admin permission.
    """
    try:
        api_key = await generate_api_token(db, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"api_key": api_key},
    )


@router.post(
    "/webhooks/entity-status",
    response_model=EntityMappingStatus,
)
async def update_entity_status(
    current_user: Annotated[DbUser, Depends(valid_api_token)],
    project: Annotated[DbProject, Depends(get_project)],
    entity_details: EntityMappingStatusIn,
):
    """Update the status for an Entity."""
    return await update_entity_mapping_status(
        project.odk_credentials,
        project.odkid,
        entity_details.entity_id,
        entity_details.label,
        entity_details.status,
    )
