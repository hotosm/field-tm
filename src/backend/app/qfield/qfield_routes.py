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
"""Routes to relay requests to QFieldCloud server (Litestar)."""

from litestar import Router, post
from litestar import status_codes as status
from litestar.di import Provide

from app.auth.auth_deps import public_endpoint
from app.db.database import db_conn
from app.qfield import qfield_schemas
from app.qfield.qfield_crud import qfc_credentials_test


@post(
    "/test-credentials",
    summary="Test QFieldCloud credentials by attempting to open a session.",
    dependencies={
        "db": Provide(db_conn),
        "current_user": Provide(public_endpoint),
    },
    status_code=status.HTTP_200_OK,
)
async def qfc_creds_test(
    qfc_creds: qfield_schemas.QFieldCloud,
) -> None:
    """Test QFieldCloud credentials by attempting to open a session."""
    await qfc_credentials_test(qfc_creds)


qfield_router = Router(
    path="/qfield",
    tags=["qfield"],
    route_handlers=[
        qfc_creds_test,
    ],
)
