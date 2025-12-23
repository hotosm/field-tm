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


async def test_helper_odk_creds_test(client):
    """Unit tests for the helper routes in the Litestar application.

    This module tests the `/central/test-credentials` endpoint,
    mocking the ODK credentials verification logic to ensure the route
    responds correctly without making real network calls.
    """
    with patch(
        "app.central.central_crud.odk_credentials_test", new_callable=AsyncMock
    ) as mock_test_odk:
        response = await client.post(
            "/central/test-credentials",
            params={
                "odk_central_url": "http://central:8383",
                "odk_central_user": "admin@hotosm.org",
                "odk_central_password": "Password1234",
            },
        )
        assert response.status_code == 200
        mock_test_odk.assert_awaited_once()


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
