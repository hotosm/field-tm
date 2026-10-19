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
"""Minimal ODK Central routes still used by the HTMX manager UI."""

from litestar import Router, post
from litestar import status_codes as status
from litestar.di import Provide

from app.auth.auth_deps import login_required
from app.central import central_crud, central_schemas


@post(
    "/test-credentials",
    summary="Test ODK Central credentials by attempting to open a session.",
    status_code=status.HTTP_200_OK,
    dependencies={"current_user": Provide(login_required)},
)
async def odk_creds_test(
    data: central_schemas.ODKCentral,
    current_user: object,
) -> None:
    """Test ODK Central credentials by attempting to open a session."""
    await central_crud.odk_credentials_test(data)


central_router = Router(
    path="/api/v1/central",
    tags=["api"],
    route_handlers=[odk_creds_test],
)
