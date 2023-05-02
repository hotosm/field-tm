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

import pytest
from fastapi import status

from app.users import user_schemas
from app.users.user_crud import create_user


@pytest.fixture
def users(db):
    create_user(db, user_schemas.UserIn(username="admin", password="admin"))
    create_user(db, user_schemas.UserIn(username="niraj", password="niraj"))
    create_user(db, user_schemas.UserIn(username="test", password="test"))


def test_list_users(users, client):
    response = client.get("/users")
    assert len(response.json()) == 3


def test_create_users(client):
    response = client.post("/users/", json={"username": "test3", "password": "test1"})
    assert response.status_code == status.HTTP_200_OK

    response = client.post("/users/", json={"username": "niraj", "password": "niraj"})
    assert response.status_code == status.HTTP_200_OK

    response = client.post("/users/", json={"username": "niraj"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.post("/users/", json={"username": "niraj", "password": "niraj"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Username already registered"}
