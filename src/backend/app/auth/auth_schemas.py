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
"""Pydantic models for Auth."""

from typing import Optional, TypedDict

from pydantic import BaseModel, ConfigDict, computed_field

from app.db.enums import ProjectRole, UserRole
from app.db.models import DbProject, DbUser


class ProjectUserDict(TypedDict):
    """Dict of both DbProject & DbUser."""

    user: DbUser
    project: DbProject


class BaseUser(BaseModel):
    """Base user model to inherit."""

    model_config = ConfigDict(use_enum_values=True)

    sub: str
    username: str
    # TODO any usage of profile_img should be refactored out
    # in place of 'picture'
    profile_img: Optional[str] = None
    email: Optional[str] = None
    picture: Optional[str] = None
    role: Optional[UserRole] = UserRole.MAPPER


class AuthUser(BaseUser):
    """The user model returned from OAuth2."""

    def __init__(self, **data):
        """Initializes the AuthUser class."""
        super().__init__(**data)

    @computed_field
    @property
    def id(self) -> str:
        """Compute id from sub field."""
        return self.sub.split("|")[1]

    @computed_field
    @property
    def provider(self) -> str:
        """Compute provider from sub field."""
        return self.sub.split("|")[0]

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

    sub: str
    project_roles: Optional[dict[int, ProjectRole]] = None

    def model_post_init(self, ctx):
        """Add to picture field, and remove the value for profile_img.

        We need this workaround as OSM returns profile_img in the response.
        """
        if self.profile_img:
            self.picture = self.profile_img
            self.profile_img = None


class ExternalUserIn(BaseModel):
    """Create a FieldTM user from an external platform."""

    id: str
    platform: str  # the name of the platform, used for sub `platform|id`
    username: str
    email: Optional[str] = None
    picture: Optional[str] = None
