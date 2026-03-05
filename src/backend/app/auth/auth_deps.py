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

"""Auth dependency adapters built on hotosm-auth Litestar context."""

from types import SimpleNamespace
from typing import Any

from hotosm_auth_litestar import get_current_user, get_current_user_optional
from litestar import Request
from litestar import status_codes as status
from litestar.exceptions import HTTPException

from app.config import settings


def _pick_attr(obj: object, *names: str) -> Any:
    """Read the first non-empty field from object attributes/dict keys."""
    for name in names:
        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if value not in (None, ""):
            return value
    return None


def get_user_sub(user: object) -> str:
    """Normalize hotosm-auth user identifiers to Field-TM `provider|id` form."""
    sub = _pick_attr(user, "sub", "user_sub")
    if sub:
        sub_value = str(sub)
        if "|" in sub_value:
            return sub_value
        return f"osm|{sub_value}"

    uid = _pick_attr(user, "uid", "id", "user_id")
    if uid is not None:
        return f"osm|{uid}"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated user is missing a valid identifier.",
    )


def get_user_username(user: object) -> str:
    """Get a username-like value from auth user data."""
    username = _pick_attr(user, "username", "preferred_username", "name")
    if username:
        return str(username)

    email = _pick_attr(user, "email", "email_address")
    if email:
        return str(email).split("@")[0]

    return "unknown"


def get_user_is_admin(user: object) -> bool:
    """Best-effort extraction of admin flag from auth user data."""
    return bool(_pick_attr(user, "is_admin", "is_superuser", "admin", "superuser"))


async def login_required(request: Request) -> object:
    """Dependency for endpoints requiring login."""
    if settings.DEBUG:
        return SimpleNamespace(sub="osm|1", username="localadmin", is_admin=True)
    return await get_current_user(request)


async def public_endpoint(request: Request) -> object:
    """Optional-auth dependency with a service-account fallback."""
    if settings.DEBUG:
        return SimpleNamespace(sub="osm|1", username="localadmin", is_admin=True)
    user = await get_current_user_optional(request)
    if user:
        return user
    return SimpleNamespace(sub="osm|20386219", username="svcftm", is_admin=False)
