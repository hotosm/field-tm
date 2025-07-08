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
"""Logic for organisation management."""

import io
import json
from datetime import date, datetime
from io import BytesIO
from textwrap import dedent
from typing import Optional

import aiohttp
from fastapi import (
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.auth_schemas import AuthUser
from app.auth.providers.osm import get_osm_token, send_osm_message
from app.config import settings
from app.db.enums import MappingLevel, UserRole
from app.db.models import DbOrganisation, DbOrganisationManagers, DbUser
from app.helpers.helper_crud import send_email
from app.organisations.organisation_schemas import OrganisationIn, OrganisationOut
from app.organisations.organisation_utils import (
    build_submission_filters,
    collect_all_submissions,
    generate_csv_string,
    generate_geojson_dict,
    populate_odk_credentials_for_projects,
)
from app.projects.project_crud import DbProject
from app.users.user_crud import send_mail
from app.users.user_schemas import UserIn


async def init_admin_org(db: Connection) -> None:
    """Init admin org and user at application startup."""
    # Create admin user
    admin_user = UserIn(
        sub="osm|1",
        username="localadmin",
        role=UserRole.ADMIN,
        name="Admin",
        email_address="admin@fmtm.dev",
        mapping_level=MappingLevel.ADVANCED,
        is_email_verified=True,
    )
    await DbUser.create(db, admin_user, ignore_conflict=True)

    # Create service user
    svc_user = UserIn(
        sub="osm|20386219",
        username="svcfmtm",
        name="Field-TM Service Account",
        email_address=settings.ODK_CENTRAL_USER,
        is_email_verified=True,
        # This API key is used for the Central Webhook service
        api_key=settings.CENTRAL_WEBHOOK_API_KEY.get_secret_value()
        if settings.CENTRAL_WEBHOOK_API_KEY
        else None,
    )
    await DbUser.create(db, svc_user, ignore_conflict=True)

    # Create HOTOSM org
    org_in = OrganisationIn(
        name=settings.DEFAULT_ORG_NAME,
        description="Default organisation",
        url=settings.DEFAULT_ORG_URL,
        associated_email=settings.DEFAULT_ORG_EMAIL,
        odk_central_url=settings.ODK_CENTRAL_URL,
        odk_central_user=settings.ODK_CENTRAL_USER,
        odk_central_password=settings.ODK_CENTRAL_PASSWD.get_secret_value()
        if settings.ODK_CENTRAL_PASSWD
        else "",
        approved=True,
    )

    org_logo = None
    if logo_url := settings.DEFAULT_ORG_LOGO_URL:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(logo_url) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "")

                    if content_type.startswith("image/"):
                        org_logo = UploadFile(
                            file=BytesIO(await response.read()),
                            filename="logo.png",
                            headers={"Content-Type": content_type},
                        )
                    else:
                        log.debug(f"Invalid content type for logo: {content_type}")
            except aiohttp.ClientError as e:
                log.debug(f"Failed to fetch logo from {logo_url}: {e}")

    hotosm_org = await DbOrganisation.create(
        db,
        org_in,
        admin_user.sub,
        org_logo,
        ignore_conflict=True,
    )

    # Make admin user manager of HOTOSM
    if hotosm_org:
        await DbOrganisationManagers.create(db, hotosm_org.id, admin_user.sub)


async def get_my_organisations(
    db: Connection,
    current_user: AuthUser,
):
    """Get organisations filtered by the current user.

    TODO add extra UNION for all associated projects to user.

    Args:
        db (Connection): The database connection.
        current_user (AuthUser): The current user.

    Returns:
        list[dict]: A list of organisation objects to be serialised.
    """
    sql = """
        SELECT DISTINCT org.*
        FROM organisations org
        JOIN organisation_managers managers
            ON managers.organisation_id = org.id
        WHERE managers.user_sub = %(user_sub)s

        UNION

        SELECT DISTINCT org.*
        FROM organisations org
        JOIN projects project
            ON project.organisation_id = org.id
        WHERE project.author_sub = %(user_sub)s;
    """
    async with db.cursor(row_factory=class_row(OrganisationOut)) as cur:
        await cur.execute(sql, {"user_sub": current_user.sub})
        return await cur.fetchall()


async def send_approval_message(
    request: Request,
    creator_sub: str,
    organisation_name: str,
    osm_auth: Auth,
    set_primary_org_odk_server: bool = False,
):
    """Send message to the organisation creator after approval."""
    log.info(f"Sending approval message to organisation creator ({creator_sub}).")
    osm_token = get_osm_token(request, osm_auth)
    message_content = dedent(f"""
        ## Congratulations!

        Your organisation **{organisation_name}** has been approved.

        You can now manage your organisation freely.
    """)
    if set_primary_org_odk_server:
        message_content += dedent("""
            It has also been granted access to the ODK server.
        """)
    message_content += dedent("""
        \nThank you for being a part of our platform!
    """)
    send_osm_message(
        osm_token=osm_token,
        osm_sub=creator_sub,
        title="Your organisation has been approved!",
        body=message_content,
    )
    log.info(f"Approval message sent to organisation creator ({creator_sub}).")


async def send_organisation_approval_request(
    request: Request,
    organisation: DbOrganisation,
    db: Connection,
    requester: str,
    primary_organisation: DbOrganisation,
    osm_auth: Auth,
    request_odk_server: bool,
):
    """Notify primary organisation about new organisation's creation."""
    osm_token = get_osm_token(request, osm_auth)
    if settings.DEBUG:
        organisation_url = f"http://{settings.FMTM_DOMAIN}:{settings.FMTM_DEV_PORT}/organization/approve/{organisation.id}"
    else:
        organisation_url = (
            f"https://{settings.FMTM_DOMAIN}/organization/{organisation.id}"
        )

    admins = await DbUser.all(db, role=UserRole.ADMIN)
    if not admins:
        msg = "No instance admins configured!"
        log.error(msg)
        raise Exception(msg)

    admin_usernames = [admin.username for admin in admins]
    title = f"Creation of a new organization {organisation.name} was requested"
    message_content = dedent(f"""
        A new organisation **{organisation.name}** has been created by **{requester}**.

        You can view the organisation details here:
        - [{organisation.name}]({organisation_url}).

        The organisation is currently pending approval.
        Please review the organisation details and approve or reject it as soon as
        possible.
        The organisation's associated email is: {organisation.associated_email} if you
        need to contact them.
    """)

    if request_odk_server:
        message_content += (
            f"\nThe organisation creator has requested access to the "
            f"{primary_organisation.name} ODK server at "
            f"{primary_organisation.odk_central_url}. "
            "The access can be granted during the organisation's approval.\n"
        )

    # Send email notification to primary organisation through their associated email
    # This was included because the primary organisation admins may not be OSM users
    if primary_organisation.associated_email:
        await send_email(
            user_emails=[primary_organisation.associated_email],
            title=title,
            message_content=message_content,
        )

    # Send OSM messages to all admins
    for username in admin_usernames:
        send_osm_message(
            osm_token=osm_token,
            osm_username=username,
            title=title,
            body=message_content,
        )
    log.info(
        "Notification about organisation creation sent at "
        f"{primary_organisation.associated_email}."
    )


async def get_organisation_stats(
    db,
    org_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Retrieve aggregated statistics for a given organisation.

    This includes overall task counts, project-level task status,
    and daily activity (e.g., tasks mapped per day) within a specified date range.

    If no start_date is provided, it defaults to the beginning of the current year.
    If no end_date is provided, it defaults to today's date.

    Args:
        db (Connection): Database connection object.
        org_id (int): ID of the organisation to retrieve statistics for.
        start_date (date, optional): Start date of the stats period.
        end_date (date, optional): End date of the stats period.

    Returns:
        dict: A dictionary containing overview stats, per-project task status,
              and daily activity stats.
    """
    today = datetime.utcnow().date()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date.replace(month=1, day=1)

    log.info(
        f"""Fetching stats for org_id={org_id}, start_date={start_date},
        end_date={end_date}"""
    )

    empty_stats = {
        "overview": {
            "total_tasks": 0,
            "active_projects": 0,
            "total_submissions": 0,
            "total_contributors": 0,
        },
        "task_status": [],
        "activity": {
            "last_submission": None,
            "daily_stats": [],
        },
    }

    # === Main Overview Query ===
    main_sql = """
        WITH base_projects AS (
            SELECT id FROM projects WHERE organisation_id = %(org_id)s
        ),
        project_overview AS (
            SELECT
                COALESCE(SUM(p.total_tasks), 0) AS total_tasks,
                COUNT(*) FILTER (WHERE p.status NOT IN ('COMPLETED', 'ARCHIVED'))
                AS active_projects
            FROM projects p
            WHERE p.organisation_id = %(org_id)s
        ),
        submission_count AS (
            SELECT COALESCE(SUM(stats.total_submissions), 0) AS
            total_submissions
            FROM mv_project_stats stats
            JOIN base_projects bp ON stats.project_id = bp.id
        ),
        task_event_agg AS (
            SELECT
                COUNT(*) FILTER (WHERE ev.event = 'FINISH') AS tasks_mapped,
                COUNT(*) FILTER (WHERE ev.event = 'GOOD') AS tasks_validated,
                COUNT(DISTINCT ev.user_sub) AS total_contributors,
                MAX(ev.created_at::date) AS last_activity_date
            FROM task_events ev
            JOIN base_projects bp ON ev.project_id = bp.id
            WHERE ev.created_at::date BETWEEN %(start_date)s AND %(end_date)s
        )
        SELECT
            po.total_tasks,
            po.active_projects,
            tea.tasks_mapped,
            tea.tasks_validated,
            tea.total_contributors,
            tea.last_activity_date,
            sc.total_submissions
        FROM project_overview po
        CROSS JOIN task_event_agg tea
        CROSS JOIN submission_count sc;
    """

    # === Daily Stats Query ===
    daily_sql = """
        SELECT
            ev.created_at::date AS date,
            COUNT(*) FILTER (WHERE ev.event = 'FINISH') AS tasks_mapped,
            COUNT(*) FILTER (WHERE ev.event = 'GOOD') AS tasks_validated
        FROM task_events ev
        JOIN projects p ON ev.project_id = p.id
        WHERE p.organisation_id = %(org_id)s
          AND ev.created_at::date BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY ev.created_at::date
        ORDER BY date;
    """

    # === Task Stats per Project ===
    project_task_sql = """
        SELECT
            p.id AS project_id,
            p.total_tasks,
            COUNT(*) FILTER (WHERE ev.event = 'FINISH') AS tasks_mapped,
            COUNT(*) FILTER (WHERE ev.event = 'GOOD') AS tasks_validated,
            COALESCE(stats.total_submissions, 0) AS total_submission
        FROM projects p
        LEFT JOIN task_events ev
            ON ev.project_id = p.id AND ev.created_at::date BETWEEN
            %(start_date)s AND %(end_date)s
        LEFT JOIN mv_project_stats stats ON stats.project_id = p.id
        WHERE p.organisation_id = %(org_id)s
        GROUP BY p.id, p.total_tasks, stats.total_submissions
        ORDER BY p.id;


    """

    try:
        async with db.cursor() as cur:
            # Fetch org-wide stats
            await cur.execute(
                main_sql,
                {
                    "org_id": org_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            row = await cur.fetchone()

            # Fetch daily stats
            await cur.execute(
                daily_sql,
                {
                    "org_id": org_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            daily_rows = await cur.fetchall()

            # Fetch per-project stats
            await cur.execute(
                project_task_sql,
                {
                    "org_id": org_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            project_rows = await cur.fetchall()

        daily_stats = [
            {
                "date": r[0].isoformat(),
                "tasks_mapped": r[1] or 0,
                "tasks_validated": r[2] or 0,
            }
            for r in daily_rows
        ]

        task_status = []
        for r in project_rows:
            project_id = r[0]
            total_tasks = r[1] or 0
            mapped = r[2] or 0
            validated = r[3] or 0
            total_submission = r[4] or 0
            to_map = max(total_tasks - mapped - validated, 0)

            task_status.append(
                {
                    "project_id": project_id,
                    "tasks_mapped": mapped,
                    "tasks_validated": validated,
                    "tasks_to_map": to_map,
                    "total_submission": total_submission,
                    "total_task": total_tasks,
                }
            )

        if not row:
            empty_stats["task_status"] = task_status
            empty_stats["activity"]["daily_stats"] = daily_stats
            return empty_stats

        return {
            "overview": {
                "total_tasks": row[0] or 0,
                "active_projects": row[1] or 0,
                "total_submissions": row[6] or 0,
                "total_contributors": row[4] or 0,
            },
            "task_status": task_status,
            "activity": {
                "last_submission": row[5],
                "daily_stats": daily_stats,
            },
        }

    except Exception as e:
        log.error(f"Error fetching stats for org_id={org_id}: {str(e)}")
        return empty_stats


async def download_organisation_submissions(
    db: Connection,
    org_id: int,
    file_type: str,
    submitted_date_range: str = None,
):
    """Download all form submissions for a given organisation across all projects.

    Args:
        db (Connection): Database connection object.
        org_id (int): Organisation ID to fetch submissions for.
        file_type (str): Output format - 'csv' or 'geojson'.
        submitted_date_range (str, optional): Date range filter
        in format "YYYY-MM-DD,YYYY-MM-DD".

    Returns:
        StreamingResponse: A file download stream in the requested format.
    """
    log.info(f"Starting export for organisation {org_id} as {file_type.upper()}")

    try:
        org = await DbOrganisation.one(db, org_id)
        projects = await DbProject.all(db, org_id=org_id)

        if not projects:
            log.warning(f"No projects found for organisation {org_id}")
            return {"message": f"No projects found for organisation {org_id}"}

        log.info(f"Found {len(projects)} project(s) for organisation {org_id}")

        # Set ODK credentials on projects if missing
        await populate_odk_credentials_for_projects(projects, org)

        # Parse and apply filters
        filters = build_submission_filters(submitted_date_range)
        if filters:
            log.info(
                f"Applied filters for submission date range: {submitted_date_range}"
            )

        # Fetch submissions
        all_submissions = await collect_all_submissions(projects, filters)
        if not all_submissions:
            log.warning(f"No submissions found for organisation {org_id}")
            return {"message": f"No submissions found for organisation {org_id}"}

        log.info(f"Collected {len(all_submissions)} submission(s) for export")

        # Format output
        file_type = file_type.lower()
        if file_type == "csv":
            csv_content = generate_csv_string(all_submissions)
            log.info(f"Exporting CSV for organisation {org_id}")
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename=organisation_{org_id}_submissions.csv"
                    )
                },
            )

        elif file_type == "geojson":
            geojson_data = generate_geojson_dict(all_submissions)
            log.info(f"Exporting GeoJSON for organisation {org_id}")
            return StreamingResponse(
                io.StringIO(json.dumps(geojson_data)),
                media_type="application/geo+json",
                headers={
                    "Content-Disposition": (
                        f"attachment; "
                        f"filename=organisation_{org_id}_submissions.geojson"
                    )
                },
            )

        log.error(f"Unsupported file type requested: {file_type}")
        return {"error": "Unsupported file type. Use 'csv' or 'geojson'."}

    except Exception as e:
        log.exception(f"Failed to export submissions for organisation {org_id}: {e}")
        return {"error": "Internal server error while exporting submissions."}
