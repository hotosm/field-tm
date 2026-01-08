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
"""Auth schemas and DTOs."""

from typing import Optional, TypedDict

from litestar.dto import DataclassDTO, DTOConfig
from pydantic import BaseModel, ConfigDict, computed_field

from app.db.models import DbProject, DbUser


class ProjectUserDict(TypedDict):
    """Dict of both DbProject & DbUser."""

    user: DbUser
    project: DbProject


class AuthUser(BaseModel):
    """The user model returned from OAuth2."""

    model_config = ConfigDict(use_enum_values=True)

    sub: str
    username: str
    # TODO any usage of profile_img should be refactored out
    # in place of 'picture'
    profile_img: Optional[str] = None
    email: Optional[str] = None
    picture: Optional[str] = None
    is_admin: bool = False

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


# DTO for user details returned to frontend (includes project_roles)
class FMTMUser(DataclassDTO[DbUser]):
    """DTO for user details returned to frontend (includes project_roles)."""

    config = DTOConfig()
