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
"""Tests for authenticated profile sync route."""

import pytest

from app.db.models import DbUser


@pytest.mark.asyncio
async def test_profile_me_returns_and_persists_authenticated_user(client, db):
    """GET /api/v1/auth/profile/me returns and persists the authenticated user."""
    resp = await client.get("/api/v1/auth/profile/me")
    assert resp.status_code == 200

    body = resp.json()
    assert body["sub"]
    assert body["username"]

    db_user = await DbUser.one(db, body["sub"])
    assert db_user.sub == body["sub"]
    assert db_user.username == body["username"]
    assert db_user.is_admin is body["is_admin"]
