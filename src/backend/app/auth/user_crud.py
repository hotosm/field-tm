"""User CRUD helpers shared by auth routes and tests."""

import logging

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.auth.auth_schemas import AuthUser

# from app.auth.providers.osm import get_osm_token, send_osm_message
from app.db.models import (
    DbUser,
)
from app.i18n import _

log = logging.getLogger(__name__)


async def get_or_create_user(
    db: AsyncConnection,
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
                    registered_at
                )
                VALUES (
                    %(user_sub)s,
                    %(username)s,
                    %(email_address)s,
                    %(profile_img)s,
                    NOW()
                )
                ON CONFLICT (sub)
                DO UPDATE SET
                    profile_img = EXCLUDED.profile_img,
                    last_login_at = NOW()
                RETURNING sub, username, email_address, profile_img, is_admin
            )

            SELECT
                u.sub,
                u.username,
                u.email_address,
                u.profile_img,
                u.is_admin,

                -- Aggregate project roles for the user, as project:role pairs
                jsonb_object_agg(
                    ur.project_id,
                    COALESCE(ur.role, 'MAPPER')
                ) FILTER (WHERE ur.project_id IS NOT NULL) AS project_roles

            FROM upserted_user u
            LEFT JOIN user_roles ur ON u.sub = ur.user_sub
            GROUP BY
                u.sub,
                u.username,
                u.email_address,
                u.profile_img,
                u.is_admin;
        """

        async with db.cursor(row_factory=class_row(DbUser)) as cur:
            await cur.execute(
                upsert_sql,
                {
                    "user_sub": user_data.sub,
                    "username": user_data.username,
                    "email_address": user_data.email,
                    "profile_img": user_data.profile_img or "",
                },
            )
            db_user_details = await cur.fetchone()

        if not db_user_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_("User (%(user_sub)s) could not be inserted in db")
                % {"user_sub": user_data.sub},
            )

        return db_user_details

    except Exception as e:
        await db.rollback()
        log.exception(f"Exception occurred: {e}", stack_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # FIXME work out how to use osm token from hotosm_auth pkg
    # async def process_inactive_users(
    #     db: AsyncConnection,
    # ):
    #     """Identify inactive users, send warnings, and delete accounts."""
    #     now = datetime.now(timezone.utc)
    #     warning_thresholds = [
    #         (now - timedelta(days=INACTIVITY_THRESHOLD - days))
    #         for days in WARNING_INTERVALS
    #     ]
    #     deletion_threshold = now - timedelta(days=INACTIVITY_THRESHOLD)

    #     async with db.cursor() as cur:
    #         # Users eligible for warnings
    #         for days, warning_date in zip(
    #             WARNING_INTERVALS, warning_thresholds, strict=False
    #         ):
    #             async with db.cursor(row_factory=class_row(DbUser)) as cur:
    #                 await cur.execute(
    #                     """
    #                     SELECT sub, username, last_login_at
    #                     FROM users
    #                     WHERE last_login_at < %(warning_date)s
    #                     AND last_login_at >= %(next_warning_date)s;
    #                     """,
    #                     {
    #                         "warning_date": warning_date,
    #                         "next_warning_date": warning_date - timedelta(days=7),
    #                     },
    #                 )
    #                 users_to_warn = await cur.fetchall()

    #             for user in users_to_warn:
    #                 if SVC_OSM_TOKEN:
    #                     await send_warning_email_or_osm(
    #                         user.sub, user.username, days, SVC_OSM_TOKEN
    #                     )
    #                 else:
    #                     log.warning(
    #                         f"The SVC_OSM_TOKEN is not set on this server. "
    #                         f"Cannot send emails to inactive users: "
    #                         f"{', '.join(user.username for user in users_to_warn)}"
    #                     )

    #         # Users eligible for deletion
    #         async with db.cursor(row_factory=class_row(DbUser)) as cur:
    #             await cur.execute(
    #                 """
    #                 SELECT sub, username
    #                 FROM users
    #                 WHERE last_login_at < %(deletion_threshold)s;
    #                 """,
    #                 {"deletion_threshold": deletion_threshold},
    #             )
    #             users_to_delete = await cur.fetchall()

    #         for user in users_to_delete:
    #             log.info(f"Deleting user {user.username} due to inactivity.")
    #             await DbUser.delete(db, user.sub)

    # FIXME work out how to use osm token from hotosm_auth pkg
    # async def send_warning_email_or_osm(
    #     user_sub: str,
    #     username: str,
    #     days_remaining: int,
    #     osm_token: str,
    # ):
    #     """Send warning email or OSM message to the user."""
    #     message_content = dedent(f"""
    #     ## Account Deletion Warning

    #     Hi {username},

    #     Your account has been inactive for a long time. To comply with our
    #     policy, your account will be deleted in {days_remaining} days if you
    #     do not log in.

    #     Please log in to reset your inactivity period and avoid deletion.

    #     Thank you for being a part of our platform!
    #     """)

    #     send_osm_message(
    #         osm_token=osm_token,
    #         osm_sub=user_sub,
    #         title="Field-TM account deletion warning",
    #         body=message_content,
    #     )
    #     log.info(f"Sent warning to {username}: {days_remaining} days remaining.")

    # FIXME work out how to use osm token from hotosm_auth pkg
    # async def send_invitation_message(
    #     request: Request,
    #     project: DbProject,
    #     invitee_username: str,
    #     osm_auth: Auth,
    #     invite_url: str,
    #     user_email: str,
    #     signin_type: str,
    # ):  # noqa: PLR0913
    #     """Send an invitation message to a user to join a project."""
    #     project_url = f"{settings.FTM_DOMAIN}/project/{project.id}"
    #     if not project_url.startswith("http"):
    #         project_url = f"https://{project_url}"

    #     title = f"You have been invited to join the project {project.project_name}"
    #     message_content = dedent(f"""
    #         You have been invited to join the project **{project.project_name}**.

    #         To accept the invitation, please click the link below:
    #         [Accept Invitation]({invite_url})

    #         You may use this link after accepting the invitation to view the
    #         project if you have access:
    #         [Project]({project_url})

    #         Thank you for being a part of our platform!
    #     """)

    #     if signin_type == "osm":
    #         osm_token = get_osm_token(request, osm_auth)

    #         send_osm_message(
    #             osm_token=osm_token,
    #             osm_username=invitee_username,
    #             title=title,
    #             body=message_content,
    #         )
    #         log.info(f"Invitation message sent to osm user ({invitee_username}).")

    return await DbUser.one(db, user_data.sub)
