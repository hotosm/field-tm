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
"""Pydantic models for Users and Roles."""

from typing import Optional

from pydantic import BaseModel

from app.models.enums import UserRole


class UserBase(BaseModel):
    """Username only."""

    username: str


class User(UserBase):
    """User with ID."""

    id: int


class UserOut(UserBase):
    """User with ID and role."""

    id: int
    role: UserRole


class UserRole(BaseModel):
    """User role only."""

    role: UserRole


class UserRoles(BaseModel):
    """User details with role, org, and associated project."""

    user_id: int
    organization_id: Optional[int] = None
    project_id: Optional[int] = None
    role: UserRole
