"""User CRUD helpers shared by auth routes and tests."""

from __future__ import annotations

import logging

from psycopg import AsyncConnection

from app.auth.auth_schemas import AuthUser
from app.db.models import DbUser

log = logging.getLogger(__name__)


async def get_or_create_user(
    db: AsyncConnection,
    user_data: AuthUser,
) -> DbUser:
    """Upsert a user from auth context and return the current DB record."""
    await DbUser.create(
        db,
        DbUser(
            sub=user_data.sub,
            username=user_data.username,
            email_address=user_data.email,
            profile_img=user_data.profile_img or "",
            is_admin=bool(user_data.is_admin),
        ),
        ignore_conflict=True,
    )

    async with db.cursor() as cur:
        await cur.execute(
            """
            UPDATE users
            SET
                username = %(username)s,
                profile_img = %(profile_img)s,
                email_address = %(email_address)s,
                last_login_at = NOW()
            WHERE sub = %(sub)s
            """,
            {
                "sub": user_data.sub,
                "username": user_data.username,
                "profile_img": user_data.profile_img or "",
                "email_address": user_data.email,
            },
        )

    return await DbUser.one(db, user_data.sub)
