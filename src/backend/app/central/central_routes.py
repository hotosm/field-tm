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
from litestar.params import Parameter

from app.auth.auth_deps import public_endpoint
from app.central import central_crud, central_schemas
from app.db.database import db_conn


@post(
    "/test-credentials",
    summary="Test ODK Central credentials by attempting to open a session.",
    status_code=status.HTTP_200_OK,
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
)
async def odk_creds_test(
    external_project_instance_url: str | None = Parameter(default=None),
    external_project_username: str | None = Parameter(default=None),
    external_project_password: str | None = Parameter(default=None),
) -> None:
    """Test ODK Central credentials by attempting to open a session."""
    odk_creds = central_schemas.ODKCentral(
        external_project_instance_url=external_project_instance_url,
        external_project_username=external_project_username,
        external_project_password=external_project_password,
    )
    await central_crud.odk_credentials_test(odk_creds)


central_router = Router(
    path="/api/v1/central",
    tags=["api"],
    route_handlers=[
        odk_creds_test,
    ],
)
