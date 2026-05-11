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

"""Auth routes for authenticated user profile sync and retrieval."""

from litestar import Router, get
from litestar.di import Provide
from psycopg import AsyncConnection

from app.auth.auth_deps import (
    get_user_is_admin,
    get_user_sub,
    get_user_username,
    login_required,
)
from app.auth.auth_schemas import AuthUser
from app.auth.user_crud import get_or_create_user
from app.db.database import db_conn
from app.db.models import DbUser


def _build_auth_user(auth_user: object) -> AuthUser:
    """Normalize the authenticated principal into the app's AuthUser shape."""
    return AuthUser(
        sub=get_user_sub(auth_user),
        username=get_user_username(auth_user),
        email=getattr(auth_user, "email", None)
        or getattr(auth_user, "email_address", None),
        picture=getattr(auth_user, "picture", None),
        profile_img=getattr(auth_user, "profile_img", None),
        is_admin=get_user_is_admin(auth_user),
    )


@get(
    "/profile/me",
    summary="Get or create the current authenticated user profile.",
    dependencies={
        "db": Provide(db_conn),
        "auth_user": Provide(login_required),
    },
)
async def get_current_user_profile(
    db: AsyncConnection,
    auth_user: object,
) -> DbUser:
    """Upsert the authenticated user into the database and return their profile.

    The sub is formatted as ``hotosm|<id>`` or ``fieldtm|<id>`` depending on
    the configured AUTH_PROVIDER, matching the convention used throughout the app.
    """
    db_user = await get_or_create_user(db, _build_auth_user(auth_user))
    await db.commit()
    return db_user


auth_router = Router(
    path="/api/v1/auth",
    tags=["api"],
    route_handlers=[
        get_current_user_profile,
    ],
)
