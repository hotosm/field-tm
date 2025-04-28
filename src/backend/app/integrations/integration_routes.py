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
from loguru import logger as log
from psycopg import Connection

from app.auth.auth_deps import login_required
from app.auth.roles import super_admin
from app.central.central_schemas import (
    OdkCentralWebhookRequest,
)
from app.db.database import db_conn
from app.db.enums import HTTPStatus, OdkWebhookEvents
from app.db.models import DbUser
from app.integrations.integration_crud import (
    generate_api_token,
    update_entity_status_in_fmtm,
    # update_entity_status_in_odk,
)

router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/api-key")
async def get_api_key(
    current_user: Annotated[DbUser, Depends(super_admin)],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Generate and return a new API key.

    This can only be accessed once, and is regenerated on
    each call to this endpoint.

    Be sure to store it someplace safe, like a password manager.

    NOTE currently requires super admin permission.
    """
    try:
        api_token = await generate_api_token(db, current_user.sub)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"api_token": api_token},
    )


@router.post(
    "/webhooks/entity-status",
    # response_model=EntityMappingStatus,
)
async def update_entity_status_from_webhook(
    db: Annotated[Connection, Depends(db_conn)],
    current_user: Annotated[DbUser, Depends(login_required)],
    odk_event: OdkCentralWebhookRequest,
):
    """ODK Central webhook triggers.

    These are required to trigger the replication to users via electric-sql.

    TODO perhaps these should be separated out, as the review action
    does not require a db connection.
    """
    log.debug(f"Webhook called with event ({odk_event.type.value})")

    if odk_event.type == OdkWebhookEvents.UPDATE_ENTITY:
        # insert state into db
        await update_entity_status_in_fmtm(db, odk_event)

    elif odk_event.type == OdkWebhookEvents.REVIEW_SUBMISSION:
        # update entity status in odk
        # await update_entity_status_in_odk(db, odk_event)
        log.warning(
            "The handling of submission reviews via webhook is not implemented yet."
        )

    elif odk_event.type == OdkWebhookEvents.NEW_SUBMISSION:
        # unsupported for now
        log.debug("The handling of new submissions via webhook is not implemented yet.")

    else:
        msg = (
            f"Webhook was called for an unsupported event type ({odk_event.type.value})"
        )
        log.warning(msg)
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg)
