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
"""DTO definitions for user endpoints."""

from litestar.dto import DataclassDTO, DTOConfig

from app.db.models import DbUser


# Response DTO for full user details (excluding project_roles relationship)
class UserOut(DataclassDTO[DbUser]):
    """DTO that excludes project_roles from user responses."""

    config = DTOConfig(exclude={"project_roles"})


# PATCH DTO for partial user updates
class UserUpdate(DataclassDTO[DbUser]):
    """DTO for partial user updates."""

    config = DTOConfig(
        include={
            "is_admin",
            "name",
            "city",
            "country",
            "profile_img",
            "email_address",
        },
        partial=True,
    )


# DTO for lightweight username listing (sub + username only)
class Usernames(DataclassDTO[DbUser]):
    """DTO for lightweight username listing."""

    config = DTOConfig(include={"sub", "username"})
