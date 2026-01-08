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

"""Tests for user / auth endpoints."""


async def test_nothing():
    """Dummy test to stop exit code 5."""
    assert True


# import pytest

# from app.users import user_schemas
# from app.users.user_crud import create_user


# @pytest_asyncio.fixture
# async def users(db):
#     create_user(db, user_schemas.UserIn(username="admin", password="admin"))
#     create_user(db, user_schemas.UserIn(username="niraj", password="niraj"))
#     create_user(db, user_schemas.UserIn(username="test", password="test"))


# async def test_list_users(users, client):
#     response = await client.get("/users")
#     assert len(response.json()) == 3


# async def test_create_users(client):
#     response = await client.post(
#         "/users",
#         json={"username": "test3", "password": "test1"},
#     )
#     assert response.status_code == 200

#     response = await client.post(
#         "/users",
#         json={"username": "niraj", "password": "niraj"},
#     )
#     assert response.status_code == 200

#     response = await client.post("/users", json={"username": "niraj"})
#     assert response.status_code == 422

#     response = await client.post(
#         "/users",
#         json={"username": "niraj", "password": "niraj"},
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Username already registered"}
