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
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from litestar.handlers.base import BaseRouteHandler

from app.config import AuthProvider, settings
from app.i18n import _

_LOCAL_ADMIN_RAW_SUB = "custom|1"
_LOCAL_ADMIN_USERNAME = "localadmin"


def _pick_attr(obj: object, *names: str) -> Any:
    """Read the first non-empty field from object attributes/dict keys."""
    for name in names:
        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if value not in (None, ""):
            return value
    return None


def get_user_sub(user: object) -> str:
    """Normalize hotosm-auth user identifiers to Field-TM `provider|id` form.

    The prefix is derived from the configured AUTH_PROVIDER:
    - HOTOSM  → ``hotosm|<id>``
    - BUNDLED → ``fieldtm|<id>``
    - others  → preserve any existing ``provider|id`` form or fall back to ``osm|<id>``
    - ``custom|<id>`` is preserved for the internal local admin user.
    """
    provider_prefixes = {
        AuthProvider.HOTOSM: "hotosm",
        AuthProvider.BUNDLED: "fieldtm",
    }
    prefix = provider_prefixes.get(settings.AUTH_PROVIDER)

    sub = _pick_attr(user, "sub", "user_sub")
    if sub:
        sub_value = str(sub)
        if "|" in sub_value:
            existing_prefix, raw_id = sub_value.split("|", 1)
            if existing_prefix == AuthProvider.CUSTOM.value:
                return sub_value
            if prefix:
                # Re-prefix the raw ID with the correct provider name.
                return f"{prefix}|{raw_id}"
            return sub_value
        return f"{prefix or 'osm'}|{sub_value}"

    uid = _pick_attr(user, "uid", "id", "user_id")
    if uid is not None:
        return f"{prefix or 'osm'}|{uid}"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_("Authenticated user is missing a valid identifier."),
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


def get_local_admin_auth_user() -> SimpleNamespace:
    """Return the internal local admin principal used when auth is disabled."""
    return SimpleNamespace(
        sub=_LOCAL_ADMIN_RAW_SUB,
        username=_LOCAL_ADMIN_USERNAME,
        is_admin=True,
    )


def auth_disabled() -> bool:
    """Whether auth is explicitly disabled (local development only)."""
    return settings.AUTH_PROVIDER == AuthProvider.DISABLED


async def login_required(request: Request) -> object:
    """Dependency for endpoints requiring login."""
    if auth_disabled():
        return get_local_admin_auth_user()
    return await get_current_user(request)


async def login_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Route guard: reject anonymous requests on handlers that don't use the user."""
    await login_required(connection)  # type: ignore[arg-type]


async def get_optional_auth_user(request: Request) -> object | None:
    """Return the authenticated user when present, otherwise None."""
    if auth_disabled():
        return get_local_admin_auth_user()
    return await get_current_user_optional(request)
