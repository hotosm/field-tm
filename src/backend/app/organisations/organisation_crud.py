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

from io import BytesIO
from textwrap import dedent

import aiohttp
from fastapi import (
    Request,
    UploadFile,
)
from loguru import logger as log
from osm_login_python.core import Auth
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.auth_schemas import AuthUser
from app.auth.providers.osm import get_osm_token, send_osm_message
from app.config import settings
from app.db.enums import MappingLevel, UserRole
from app.db.models import DbOrganisation, DbOrganisationManagers, DbUser
from app.organisations.organisation_schemas import OrganisationIn, OrganisationOut
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
    await send_mail(
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
