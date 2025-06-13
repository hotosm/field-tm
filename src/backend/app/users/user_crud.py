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
"""Logic for user routes."""

import os
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from textwrap import dedent
from typing import Literal, Optional

import aiosmtplib
import markdown
from fastapi import Request
from fastapi.exceptions import HTTPException
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.auth_schemas import AuthUser
from app.auth.providers.osm import get_osm_token, send_osm_message
from app.config import settings
from app.db.enums import HTTPStatus, UserRole
from app.db.models import DbProject, DbUser
from app.projects.project_crud import get_pagination

SVC_OSM_TOKEN = os.getenv("SVC_OSM_TOKEN", None)
WARNING_INTERVALS = [21, 14, 7]  # Days before deletion
INACTIVITY_THRESHOLD = 2 * 365  # 2 years approx


async def get_or_create_user(
    db: Connection,
    user_data: AuthUser,
) -> DbUser:
    """Get user from User table if exists, else create."""
    try:
        upsert_sql = """
            WITH upserted_user AS (
                INSERT INTO users (
                    sub,
                    username,
                    email_address,
                    profile_img,
                    role,
                    registered_at
                )
                VALUES (
                    %(user_sub)s,
                    %(username)s,
                    %(email_address)s,
                    %(profile_img)s,
                    %(role)s,
                    NOW()
                )
                ON CONFLICT (sub)
                DO UPDATE SET
                    profile_img = EXCLUDED.profile_img,
                    last_login_at = NOW()
                RETURNING sub, username, email_address, profile_img, role
            )

            SELECT
                u.sub,
                u.username,
                u.email_address,
                u.profile_img,
                u.role,

                -- Aggregate the organisation IDs managed by the user
                array_agg(
                    DISTINCT om.organisation_id
                ) FILTER (WHERE om.organisation_id IS NOT NULL) AS orgs_managed,

                -- Aggregate project roles for the user, as project:role pairs
                jsonb_object_agg(
                    ur.project_id,
                    COALESCE(ur.role, 'MAPPER')
                ) FILTER (WHERE ur.project_id IS NOT NULL) AS project_roles

            FROM upserted_user u
            LEFT JOIN user_roles ur ON u.sub = ur.user_sub
            LEFT JOIN organisation_managers om ON u.sub = om.user_sub
            GROUP BY
                u.sub,
                u.username,
                u.email_address,
                u.profile_img,
                u.role;
        """

        async with db.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(
                upsert_sql,
                {
                    "user_sub": user_data.sub,
                    "username": user_data.username,
                    "email_address": user_data.email,
                    "profile_img": user_data.profile_img or "",
                    "role": UserRole(user_data.role).name,
                },
            )
            db_user_details = await cur.fetchone()

        if not db_user_details:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User ({user_data.sub}) could not be inserted in db",
            )

        return db_user_details

    except Exception as e:
        await db.rollback()
        log.exception(f"Exception occurred: {e}", stack_info=True)
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e


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
                    SELECT sub, username, last_login_at
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
                SELECT sub, username
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
        title="Field-TM account deletion warning",
        body=message_content,
    )
    log.info(f"Sent warning to {username}: {days_remaining} days remaining.")


async def send_mail(
    user_emails: list[str],
    title: str,
    message_content: str,
):
    """Sends an email."""
    if not settings.emails_enabled:
        log.info("An SMTP server has not been configured.")
        return
    message = EmailMessage()
    message["Subject"] = title
    message.set_content(message_content)
    html_content = markdown.markdown(message_content)
    message.add_alternative(html_content, subtype="html")

    log.debug(f"Sending email to {', '.join(user_emails)}")
    await aiosmtplib.send(
        message,
        sender=settings.SMTP_USER,
        recipients=user_emails,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )


async def send_invitation_message(
    request: Request,
    project: DbProject,
    invitee_username: str,
    osm_auth: Auth,
    invite_url: str,
    user_email: str,
    signin_type: str,
):
    """Send an invitation message to a user to join a project."""
    project_url = f"{settings.FMTM_DOMAIN}/project/{project.id}"
    if not project_url.startswith("http"):
        project_url = f"https://{project_url}"

    title = f"You have been invited to join the project {project.name}"
    message_content = dedent(f"""
        You have been invited to join the project **{project.name}**.

        To accept the invitation, please click the link below:
        [Accept Invitation]({invite_url})

        You may use this link after accepting the invitation to view the project if you
        have access:
        [Project]({project_url})

        Thank you for being a part of our platform!
    """)

    if signin_type == "osm":
        osm_token = get_osm_token(request, osm_auth)

        send_osm_message(
            osm_token=osm_token,
            osm_username=invitee_username,
            title=title,
            body=message_content,
        )
        log.info(f"Invitation message sent to osm user ({invitee_username}).")

    elif signin_type == "google":
        await send_mail(
            user_emails=[user_email],
            title=title,
            message_content=message_content,
        )
        log.info(f"Invitation message sent to email user ({user_email}).")


async def get_paginated_users(
    db: Connection,
    page: int,
    results_per_page: int,
    search: Optional[str] = None,
    signin_type: Literal["osm", "google"] = "osm",
) -> dict:
    """Helper function to fetch paginated users with optional filters."""
    # Get subset of users
    users = await DbUser.all(db, search=search, signin_type=signin_type) or []
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
