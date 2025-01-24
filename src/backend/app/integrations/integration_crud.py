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
"""Logic for integration routes."""

from secrets import token_urlsafe

from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row

from app.db.models import DbUser


async def generate_api_token(
    db: Connection,
    user_id: int,
) -> str:
    """Generate a new API token for a given user."""
    async with db.cursor(row_factory=class_row(DbUser)) as cur:
        await cur.execute(
            """
                UPDATE users
                SET api_key = %(api_key)s
                WHERE id = %(user_id)s
                RETURNING *;
            """,
            {"user_id": user_id, "api_key": token_urlsafe(32)},
        )
        db_user = await cur.fetchone()
        if not db_user.api_key:
            msg = f"Failed to generate API Key for user ({user_id})"
            log.error(msg)
            raise ValueError(msg)

    return db_user.api_key
