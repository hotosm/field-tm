# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
"""Logic for user routes."""

from datetime import datetime, timedelta, timezone
from textwrap import dedent
from typing import Optional

from fastapi import Request
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.providers.osm import get_osm_token, send_osm_message
from app.db.models import DbUser
from app.projects.project_crud import get_pagination

WARNING_INTERVALS = [21, 14, 7]  # Days before deletion
INACTIVITY_THRESHOLD = 2 * 365  # 2 years approx


async def process_inactive_users(
    db: Connection,
    request: Request,
    osm_auth: Auth,
):
    """Identify inactive users, send warnings, and delete accounts."""
    now = datetime.now(timezone.utc)
    warning_thresholds = [
        (now - timedelta(days=INACTIVITY_THRESHOLD - days))
        for days in WARNING_INTERVALS
    ]
    deletion_threshold = now - timedelta(days=INACTIVITY_THRESHOLD)

    osm_token = get_osm_token(request, osm_auth)

    async with db.cursor() as cur:
        # Users eligible for warnings
        for days, warning_date in zip(
            WARNING_INTERVALS, warning_thresholds, strict=False
        ):
            async with db.cursor(row_factory=class_row(DbUser)) as cur:
                await cur.execute(
                    """
                    SELECT id, username, last_login_at
                    FROM users
                    WHERE last_login_at < %(warning_date)s
                    AND last_login_at >= %(next_warning_date)s;
                    """,
                    {
                        "warning_date": warning_date,
                        "next_warning_date": warning_date - timedelta(days=7),
                    },
                )
                users_to_warn = await cur.fetchall()

            for user in users_to_warn:
                await send_warning_email_or_osm(user.id, user.username, days, osm_token)

        # Users eligible for deletion
        async with db.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(
                """
                SELECT id, username
                FROM users
                WHERE last_login_at < %(deletion_threshold)s;
                """,
                {"deletion_threshold": deletion_threshold},
            )
            users_to_delete = await cur.fetchall()

        for user in users_to_delete:
            log.info(f"Deleting user {user.username} due to inactivity.")
            await DbUser.delete(db, user.id)


async def send_warning_email_or_osm(
    user_id: int,
    username: str,
    days_remaining: int,
    osm_token: str,
):
    """Send warning email or OSM message to the user."""
    message_content = dedent(f"""
    ## Account Deletion Warning

    Hi {username},

    Your account has been inactive for a long time. To comply with our policy, your
    account will be deleted in {days_remaining} days if you do not log in.

    Please log in to reset your inactivity period and avoid deletion.

    Thank you for being a part of our platform!
    """)

    send_osm_message(
        osm_token=osm_token,
        osm_id=user_id,
        title="FMTM account deletion warning",
        body=message_content,
    )
    log.info(f"Sent warning to {username}: {days_remaining} days remaining.")


async def get_paginated_users(
    db: Connection,
    page: int,
    results_per_page: int,
    search: Optional[str] = None,
) -> dict:
    """Helper function to fetch paginated users with optional filters."""
    # Get subset of users
    users = await DbUser.all(db, search=search)
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    paginated_users = users[start_index:end_index]

    pagination = await get_pagination(
        page, len(paginated_users), results_per_page, len(users)
    )

    return {"results": paginated_users, "pagination": pagination}
