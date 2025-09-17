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

import asyncio
import os
from datetime import datetime, timedelta, timezone
from textwrap import dedent
from typing import Literal, Optional

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
from app.db.models import (
    DbProject,
    DbSubmissionDailyCount,
    DbSubmissionStatsCache,
    DbUser,
    DbUserRole,
)
from app.db.postgis_utils import timestamp
from app.helpers.helper_crud import send_email
from app.projects.project_crud import get_pagination
from app.submissions import submission_crud

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
        await send_email(
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


async def get_active_users(db: Connection) -> list[str]:
    """Fetch users active in the last one day."""
    yesterday = timestamp() - timedelta(days=1)
    users = await DbUser.all(db, last_login_after=yesterday)
    return [u.sub for u in users] if users else []


async def update_submission_counts(db: Connection):
    """Insert/update daily submission counts per user per project (incremental)."""
    active_users = await get_active_users(db)
    if not active_users:
        log.info("No active users found, skipping submission count update.")
        return

    for user_sub in active_users:
        projects = await DbUserRole.all(db, user_sub=user_sub)
        project_ids = {p.project_id for p in projects}
        if not project_ids:
            log.info(
                f"No projects found for {user_sub}, skipping submission count update."
            )
            continue

        for project_id in project_ids:
            user_daily_counts = await DbSubmissionDailyCount.all(
                db, user_sub=user_sub, project_id=project_id
            )
            last_date = (
                user_daily_counts[-1]["submission_date"] if user_daily_counts else None
            )

            filters = {"$wkt": True}
            if last_date:
                filters["$filter"] = (
                    f"__system/submissionDate gt {last_date.isoformat()}"
                )

            project = await DbProject.one(db, project_id, minimal=True)
            data = await submission_crud.get_submission_by_project(
                project, filters, expand=False
            )

            daily_counts: dict[str, int] = {}
            for sub in data.get("value", []):
                if sub.get("username") != user_sub:
                    continue
                sub_date = sub["__system"]["submissionDate"][:10]
                daily_counts[sub_date] = daily_counts.get(sub_date, 0) + 1

            # Upsert daily counts
            for date_str, count in daily_counts.items():
                await DbSubmissionDailyCount.upsert(
                    db, user_sub, project_id, date_str, count
                )


async def _fetch_submission_data(semaphore, project, user_sub):
    """Fetch all, approved, and issues submissions for a project."""
    async with semaphore:
        all_data = await submission_crud.get_submission_by_project(
            project, {"$wkt": True}, expand=False
        )
    async with semaphore:
        approved_data = await submission_crud.get_submission_by_project(
            project,
            {"$filter": "__system/reviewState eq 'approved'", "$wkt": True},
            expand=False,
        )
    async with semaphore:
        issues_data = await submission_crud.get_submission_by_project(
            project,
            {"$filter": "__system/reviewState eq 'hasIssues'", "$wkt": True},
            expand=False,
        )

    approved_subs = [
        s for s in approved_data.get("value", []) if s.get("username") == user_sub
    ]
    issues_subs = [
        s for s in issues_data.get("value", []) if s.get("username") == user_sub
    ]
    user_subs = [s for s in all_data.get("value", []) if s.get("username") == user_sub]

    return approved_subs, issues_subs, user_subs, project


async def calculate_submission_stats(db, concurrency_limit=5):
    """Calculate and cache submission stats for active users."""
    active_users = await get_active_users(db)
    if not active_users:
        return

    semaphore = asyncio.Semaphore(concurrency_limit)

    for user_sub in active_users:
        projects = await DbUserRole.all(db, user_sub=user_sub)
        project_ids = {p.project_id for p in projects}
        if not project_ids:
            continue

        tasks = [
            _fetch_submission_data(
                semaphore, await DbProject.one(db, pid, minimal=True), user_sub
            )
            for pid in project_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                continue
            approved_subs, issues_subs, user_subs_list, project = res
            total_valid = len(approved_subs)
            total_invalid = len(issues_subs)
            total = len(user_subs_list)

            org_counts, loc_counts = {}, {}
            if user_subs_list:
                org_counts[project.organisation_name] = len(user_subs_list)
                loc_counts[project.location_str] = len(user_subs_list)

            await DbSubmissionStatsCache.upsert(
                db,
                user_sub=user_sub,
                project_id=project.id,
                total_valid_submissions=total_valid,
                total_invalid_submissions=total_invalid,
                total_submissions=total,
                top_organisations=[
                    {"name": k, "count": v} for k, v in org_counts.items()
                ],
                top_locations=[{"name": k, "count": v} for k, v in loc_counts.items()],
                last_calculated=timestamp(),
            )
