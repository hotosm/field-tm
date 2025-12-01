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
"""Pydantic models overriding base DbUser fields."""

from typing import Annotated, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.db.enums import ProjectRole, UserRole
from app.db.models import DbUser, DbUserInvite, DbUserRole
from app.projects.project_schemas import PaginationInfo


class UserIn(DbUser):
    """User details for insert into DB."""

    # Only id and username are mandatory
    # NOTE this is a unique case where the primary key is not auto-generated
    # NOTE we use the OSM ID in most cases, which is unique from OSM
    pass


class UserUpdate(DbUser):
    """User details for update in DB."""

    # Exclude (do not allow update)
    sub: Annotated[Optional[str], Field(exclude=True)] = None
    username: Annotated[Optional[str], Field(exclude=True)] = None
    registered_at: Annotated[Optional[AwareDatetime], Field(exclude=True)] = None
    tasks_mapped: Annotated[Optional[int], Field(exclude=True)] = None
    tasks_validated: Annotated[Optional[int], Field(exclude=True)] = None
    tasks_invalidated: Annotated[Optional[int], Field(exclude=True)] = None
    project_roles: Annotated[Optional[dict[int, ProjectRole]], Field(exclude=True)] = (
        None
    )
    orgs_managed: Annotated[Optional[list[int]], Field(exclude=True)] = None


class UserOut(DbUser):
    """User and role."""

    # Mandatory user role field
    role: UserRole


class UserRole(BaseModel):
    """User role only."""

    role: UserRole


# Models for DbUserRole


class UserRolesOut(DbUserRole):
    """User role for a specific project."""

    user_sub: str
    role: ProjectRole
    project_id: Optional[int] = None
    username: str


class PaginatedUsers(BaseModel):
    """Project summaries + Pagination info."""

    results: list[UserOut]
    pagination: PaginationInfo


class Usernames(BaseModel):
    """User info with username and their id."""

    sub: str
    username: str


class UserInviteIn(DbUserInvite):
    """Insert a user invite record."""

    # Exclude (fields auto-generated in db)
    token: Annotated[Optional[UUID], Field(exclude=True)] = None
    expires_at: Annotated[Optional[AwareDatetime], Field(exclude=True)] = None
    created_at: Annotated[Optional[AwareDatetime], Field(exclude=True)] = None
    # project_id is included in the URL anyway
    project_id: Annotated[Optional[int], Field(exclude=True)] = None

    # Set default role
    role: Optional[ProjectRole] = ProjectRole.MAPPER


class UserInviteUpdate(UserInviteIn):
    """Update a user invite record, mostly to update timestamps."""

    # Allow setting new expiry (plus used_at field)
    expires_at: Optional[AwareDatetime] = None
