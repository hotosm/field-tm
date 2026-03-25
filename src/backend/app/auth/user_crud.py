"""User CRUD helpers shared by auth routes and tests."""

import logging

from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.auth.auth_schemas import AuthUser
from app.db.models import (
    DbUser,
)

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
                detail=f"User ({user_data.sub}) could not be inserted in db",
            )

        return db_user_details

    except Exception as e:
        await db.rollback()
        log.exception(f"Exception occurred: {e}", stack_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
