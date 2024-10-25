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
"""Pydantic models for Auth."""

from typing import Any, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field
from pydantic.functional_validators import field_validator

from app.db.enums import ProjectRole, UserRole
from app.db.models import DbOrganisation, DbProject, DbUser


class OrgUserDict(TypedDict):
    """Dict of both DbOrganisation & DbUser."""

    user: DbUser
    org: DbOrganisation


class ProjectUserDict(TypedDict):
    """Dict of both DbProject & DbUser."""

    user: DbUser
    project: DbProject


class AuthUser(BaseModel):
    """The user model returned from OSM OAuth2."""

    model_config = ConfigDict(use_enum_values=True)

    username: str
    picture: Optional[str] = None
    role: Optional[UserRole] = UserRole.MAPPER

    _sub: str = PrivateAttr()  # it won't return this field

    def __init__(self, sub: str, **data):
        """Initializes the AuthUser class."""
        super().__init__(**data)
        self._sub = sub

    @computed_field
    @property
    def id(self) -> int:
        """Compute id from sub field."""
        sub = self._sub
        return int(sub.split("|")[1])


class AuthUserWithToken(AuthUser):
    """Add the JWT token variable to AuthUser response."""

    token: str


class FMTMUser(BaseModel):
    """User details returned to the frontend.

    TODO this should inherit from AuthUser and extend.
    TODO profile_img should be refactored to `picture`.
    """

    id: int
    username: str
    profile_img: str
    role: UserRole
    project_roles: Optional[dict[int, ProjectRole]] = {}
    orgs_managed: Optional[list[int]] = []

    @field_validator("role", mode="before")
    @classmethod
    def convert_user_role_str_to_ints(cls, role: Any) -> Optional[UserRole]:
        """User role strings returned from db converted to enum integers."""
        if not role:
            return None
        if isinstance(role, str):
            return UserRole[role]
        return role

    @field_validator("project_roles", mode="before")
    @classmethod
    def convert_project_role_str_to_ints(
        cls, roles: dict[int, Any]
    ) -> Optional[dict[int, ProjectRole]]:
        """User project strings returned from db converted to enum integers."""
        if not roles:
            return {}

        first_value = next(iter(roles.values()), None)
        if isinstance(first_value, str):
            return {id: ProjectRole[role] for id, role in roles.items()}

        return roles
