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

from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    """A base model for user data."""

    username: str


class User(UserBase):
    """A model for user data in the database."""

    id: int


class UserOut(UserBase):
    """A model for user data when retrieving a user from the database."""

    id: int
    role: str


class UserRole(BaseModel):
    """A model for a user's role."""

    role: str


class UserRoles(BaseModel):
    """A model for assigning a role to a user.

    Attributes:
        user_id (int): The ID of the user to assign the role to.
        organization_id (Optional[int]): The ID of the organization to assign the role for. Defaults to None.
        project_id (Optional[int]): The ID of the project to assign the role for. Defaults to None.
        role (str): The role to assign to the user.
    """

    user_id: int
    organization_id: Optional[int] = None
    project_id: Optional[int] = None
    role: str
