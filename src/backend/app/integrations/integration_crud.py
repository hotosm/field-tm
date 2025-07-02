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
"""Logic for integration routes."""

from secrets import token_urlsafe

from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row

# from app.central.central_crud import update_entity_mapping_status
from app.central.central_schemas import (
    OdkCentralWebhookRequest,
    OdkEntitiesUpdate,
    # EntityMappingStatusIn,
)
from app.db.enums import (
    EntityState,
    HTTPStatus,
    OdkWebhookEvents,
    # ReviewStateEnum,
)
from app.db.models import DbOdkEntities, DbUser


async def generate_api_token(
    db: Connection,
    user_sub: str,
) -> str:
    """Generate a new API token for a given user."""
    async with db.cursor(row_factory=class_row(DbUser)) as cur:
        await cur.execute(
            """
                UPDATE users
                SET api_key = %(api_key)s
                WHERE sub = %(user_sub)s
                RETURNING *;
            """,
            {"user_sub": user_sub, "api_key": token_urlsafe(32)},
        )
        db_user = await cur.fetchone()
        if not db_user.api_key:
            msg = f"Failed to generate API Key for user ({user_sub})"
            log.error(msg)
            raise ValueError(msg)

    return db_user.api_key


async def update_entity_status_in_fmtm(
    db: Connection,
    odk_event: OdkCentralWebhookRequest,
):
    """Update the status for an Entity in the Field-TM db."""
    if odk_event.type != OdkWebhookEvents.UPDATE_ENTITY:
        log.error(
            "Attempted entity status update, but the "
            f"event type was wrong: {odk_event.type}"
        )
        return

    # Insert state into db
    new_state = odk_event.data.get("status")
    submission_ids = odk_event.data.get("submission_ids", "")

    if new_state is None:
        log.warning(f"Missing entity state in webhook event: {odk_event.data}")
        return HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Missing entity state property",
        )

    try:
        new_state_int = int(new_state)
        # the string name is inserted in the db
        new_entity_state = EntityState(new_state_int).name
    except (ValueError, TypeError):
        log.warning(
            f"Invalid entity state '{new_state}' in webhook event: {odk_event.data}"
        )
        return HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid entity state",
        )

    log.debug(
        f"Updating entity ({str(odk_event.id)}) status "
        f"in Field-TM db to ({new_entity_state})"
    )
    update_success = await DbOdkEntities.update(
        db,
        str(odk_event.id),
        OdkEntitiesUpdate(status=new_entity_state, submission_ids=submission_ids),
    )
    if not update_success:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error updating entity with UUID ({str(odk_event.id)})",
        )
    return Response(status_code=HTTPStatus.OK)


# async def update_entity_status_in_odk(
#     odk_event: OdkCentralWebhookRequest,
# ):
#     # FIXME here we don't have the project id and odkid to submit the updates!
#     # FIXME perhaps this needs an update to the webhook, to include the
#     # related entity details, so we can extract the project id, and then
#     # get the related ODK credentials?
#     # Else we need another workaround

#     review_state = odk_event.data.get("reviewState")
#     if review_state not in [ReviewStateEnum.HASISSUES, ReviewStateEnum.REJECTED]:
#         log.debug(f"Submission ({odk_event.id}) reviewed and marked 'approved'")
#         return Response(status_code=HTTPStatus.OK)

#     new_entity_label = f"Feature {odk_event.data.get("osm_id")}"

#     # We parse as EntityMappingStatusIn to ensure the status
#     # emoji is appended to the label
#     entity_update = EntityMappingStatusIn(
#         entity_id=str(odk_event.id),
#         status=EntityState.MARKED_BAD,
#         label=new_entity_label,
#     )
#     return await update_entity_mapping_status(
#         project.odk_credentials,
#         project.odkid,
#         entity_update.entity_id,
#         entity_update.label,
#         entity_update.status,
#     )
