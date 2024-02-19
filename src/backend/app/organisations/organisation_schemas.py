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
"""Pydantic models for Organisations."""

from re import sub
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field, computed_field

from app.config import HttpUrlStr
from app.models.enums import CommunityType, OrganisationType
from app.projects.project_schemas import ODKCentralIn

# class OrganisationBase(BaseModel):
#     """Base model for organisation to extend."""


class OrganisationIn(ODKCentralIn):
    """Organisation to create from user input."""

    name: str = Field(Form(..., description="Organisation name"))
    description: Optional[str] = Field(
        Form(None, description="Organisation description")
    )
    url: Optional[HttpUrlStr] = Field(
        Form(None, description=("Organisation website URL"))
    )
    community_type: Optional[CommunityType] = Field(
        Form(None, description=("Organisation community type"))
    )

    @computed_field
    @property
    def slug(self) -> str:
        """Sanitise the organisation name for use in a URL."""
        if not self.name:
            return ""
        # Remove special characters and replace spaces with hyphens
        slug = sub(r"[^\w\s-]", "", self.name).strip().lower().replace(" ", "-")
        # Remove consecutive hyphens
        slug = sub(r"[-\s]+", "-", slug)
        return slug

    # TODO replace once computed logo complete below
    odk_central_url: Optional[HttpUrlStr] = Field(
        Form(None, description=("ODK Central URL"))
    )
    odk_central_user: Optional[str] = Field(
        Form(None, description=("ODK Central User"))
    )
    odk_central_password: Optional[str] = Field(
        Form(None, description=("ODK Central Password"))
    )

    # TODO decode base64 logo and upload in computed property
    # @computed_field
    # @property
    # def logo(self) -> Optional[str]:
    #     """Decode and upload logo to S3, return URL."""
    #     if not self.logo_base64:
    #         return None
    #     logo_decoded = base64.b64decode(self.logo_base64)
    #     # upload to S3
    #     return url


class OrganisationEdit(OrganisationIn):
    """Organisation to edit via user input."""

    # Override to make name optional
    name: Optional[str] = None


class OrganisationOut(BaseModel):
    """Organisation to display to user."""

    id: int
    name: str
    approved: bool
    type: OrganisationType
    logo: Optional[str]
    description: Optional[str]
    slug: Optional[str]
    url: Optional[str]
    odk_central_url: Optional[str]
