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
"""Tests for helper routes."""

from unittest.mock import AsyncMock, patch

import pytest
from app.central.central_routes import odk_creds_test


async def test_helper_odk_creds_test():
    """The surviving ODK JSON route should still validate credentials."""
    with patch(
        "app.central.central_routes.central_crud.odk_credentials_test",
        new_callable=AsyncMock,
    ) as mock_test_odk:
        await odk_creds_test.fn(
            external_project_instance_url="http://central:8383",
            external_project_username="admin@hotosm.org",
            external_project_password="Password1234",
        )

    mock_test_odk.assert_awaited_once()


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
