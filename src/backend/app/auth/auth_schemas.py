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

from typing import Optional, TypedDict

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

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


class BaseUser(BaseModel):
    """Base user model to inherit."""

    model_config = ConfigDict(use_enum_values=True)

    username: str
    # TODO any usage of profile_img should be refactored out
    # in place of 'picture'
    profile_img: Optional[str] = None
    picture: Optional[str] = None
    role: Optional[UserRole] = UserRole.MAPPER


class AuthUser(BaseUser):
    """The user model returned from OSM OAuth2."""

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

    def model_post_init(self, ctx):
        """Temp workaround to convert oauth picture --> profile_img.

        TODO profile_img is used in the db for now, but will be refactored.
        """
        if self.picture:
            self.profile_img = self.picture


# NOTE we no longer use this, but is present as an example
# class AuthUserWithToken(AuthUser):
#     """Add the JWT token variable to AuthUser response."""
#     token: str


class FMTMUser(BaseUser):
    """User details returned to the frontend."""

    id: int
    project_roles: Optional[dict[int, ProjectRole]] = None
    orgs_managed: Optional[list[int]] = None

    def model_post_init(self, ctx):
        """Add to picture field, and remove the value for profile_img.

        We need this workaround as OSM returns profile_img in the response.
        """
        if self.profile_img:
            self.picture = self.profile_img
            self.profile_img = None
