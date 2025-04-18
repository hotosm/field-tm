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

import os
from datetime import datetime, timedelta, timezone
from textwrap import dedent
from typing import Optional

from fastapi import Request
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.providers.osm import get_osm_token, send_osm_message
from app.config import settings
from app.db.models import DbProject, DbUser
from app.projects.project_crud import get_pagination

SVC_OSM_TOKEN = os.getenv("SVC_OSM_TOKEN", None)
WARNING_INTERVALS = [21, 14, 7]  # Days before deletion
INACTIVITY_THRESHOLD = 2 * 365  # 2 years approx


async def process_inactive_users(
    db: Connection,
):
    """Identify inactive users, send warnings, and delete accounts."""
    now = datetime.now(timezone.utc)
    warning_thresholds = [
        (now - timedelta(days=INACTIVITY_THRESHOLD - days))
        for days in WARNING_INTERVALS
    ]
    deletion_threshold = now - timedelta(days=INACTIVITY_THRESHOLD)

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
                if SVC_OSM_TOKEN:
                    await send_warning_email_or_osm(
                        user.sub, user.username, days, SVC_OSM_TOKEN
                    )
                else:
                    log.warning(
                        f"The SVC_OSM_TOKEN is not set on this server. "
                        f"Cannot send emails to inactive users: "
                        f"{', '.join(user.username for user in users_to_warn)}"
                    )

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
            await DbUser.delete(db, user.sub)


async def send_warning_email_or_osm(
    user_sub: str,
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
        osm_sub=user_sub,
        title="FMTM account deletion warning",
        body=message_content,
    )
    log.info(f"Sent warning to {username}: {days_remaining} days remaining.")


async def send_invitation_osm_message(
    request: Request,
    project: DbProject,
    invitee_username: str,
    osm_auth: Auth,
    invite_url: str,
):
    """Send an invitation message to a user to join a project."""
    log.info(f"Sending invitation message to osm user ({invitee_username}).")

    osm_token = get_osm_token(request, osm_auth)

    project_url = f"{settings.FMTM_DOMAIN}/project/{project.id}"
    if not project_url.startswith("http"):
        project_url = f"https://{project_url}"

    message_content = dedent(f"""
        You have been invited to join the project **{project.name}**.

        To accept the invitation, please click the link below:
        [Accept Invitation]({invite_url})

        You may use this link after accepting the invitation to view the project:
        [Project]({project_url})

        Thank you for being a part of our platform!
    """)

    send_osm_message(
        osm_token=osm_token,
        osm_username=invitee_username,
        title=f"You have been invited to join the project {project.name}",
        body=message_content,
    )
    log.info(f"Invitation message sent to osm user ({invitee_username}).")


async def get_paginated_users(
    db: Connection,
    page: int,
    results_per_page: int,
    search: Optional[str] = None,
) -> dict:
    """Helper function to fetch paginated users with optional filters."""
    # Get subset of users
    users = await DbUser.all(db, search=search) or []
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page

    if not users:
        paginated_users = []
    else:
        paginated_users = users[start_index:end_index]

    pagination = await get_pagination(
        page, len(paginated_users), results_per_page, len(users)
    )
    return {"results": paginated_users, "pagination": pagination}
