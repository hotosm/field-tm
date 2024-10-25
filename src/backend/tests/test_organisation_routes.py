# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Tests for organisation routes."""

import pytest


async def test_get_organisation(client, organisation):
    """Test get list of organisations."""
    response = await client.get("/organisation/")
    assert response.status_code == 200

    data = response.json()[-1]

    assert organisation.id == data["id"]
    assert organisation.name == data["name"]
    assert organisation.description == data["description"]


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
