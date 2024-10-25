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
"""Pydantic models overriding base DbUser fields."""

from typing import Annotated, Optional

from pydantic import BaseModel, Field

from app.db.enums import UserRole
from app.db.models import DbUser, DbUserRole


class UserIn(DbUser):
    """User details for insert into DB."""

    # Only id and username are mandatory
    # NOTE this is a unique case where the primary key is not auto-generated
    # NOTE we use the OSM ID in most cases, which is unique from OSM
    pass


class UserOut(DbUser):
    """User with ID and role."""

    # Mandatory user role field
    role: UserRole


class UserRole(BaseModel):
    """User role only."""

    role: UserRole


# Models for DbUserRole


class UserRolesOut(DbUserRole):
    """User role for a specific project."""

    # project_id is redundant if the user specified it in the endpoint
    project_id: Annotated[Optional[int], Field(exclude=True)] = None
