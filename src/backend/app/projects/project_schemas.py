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
"""DTOs and schemas for project endpoints."""

from datetime import datetime
from typing import Annotated, Optional, Self, Union

from geojson_pydantic import (
    Feature,
    FeatureCollection,
    MultiPolygon,
    Polygon,
)
from litestar.dto import DataclassDTO, DTOConfig
from pydantic import BaseModel, Field, ValidationInfo
from pydantic.functional_validators import field_validator, model_validator

from app.central.central_schemas import ODKCentralDecrypted, ODKCentralIn
from app.config import decrypt_value, encrypt_value
from app.db.enums import (
    FieldMappingApp,
    ProjectStatus,
)
from app.db.models import DbProject, slugify
from app.db.postgis_utils import geojson_to_featcol, merge_polygons

# ============================================================================
# DTOs for endpoint responses
# ============================================================================


# DTO for project responses (excludes sensitive/internal fields)
class ProjectOut(DataclassDTO[DbProject]):
    """DTO that excludes sensitive fields from project responses."""

    config = DTOConfig(
        exclude={
            "xlsform_content",  # Don't serialize binary XLSForm content
            "external_project_password_encrypted",  # Don't expose encrypted passwords
        },
    )


# DTO for project summaries (subset of DbProject fields for listings)
# NOTE: For paginated responses, use PaginatedProjectSummariesOut instead
class ProjectSummary(DataclassDTO[DbProject]):
    """DTO for project summaries with subset of fields."""

    config = DTOConfig(
        include={
            "id",
            "project_name",
            "hashtags",
            "location_str",
            "description",
            "external_project_id",
            "external_project_instance_url",
            "status",
            "visibility",
            "field_mapping_app",
        },
    )


# ============================================================================
# Input validation models (used in routes but not DTOs)
# NOTE: These remain as Pydantic models because they have complex validation
# logic (hashtag parsing, GeoJSON merging, token encryption, etc.)
# ============================================================================


class StubProjectIn(BaseModel):
    """Input model for creating a project stub (with validators)."""

    project_name: str
    field_mapping_app: FieldMappingApp
    description: Optional[str] = None
    merge: bool = True
    outline: MultiPolygon | Polygon = None
    location_str: Optional[str] = None
    status: Optional[ProjectStatus] = None
    created_by_sub: Optional[str] = None
    hashtags: Optional[list[str]] = []
    slug: Optional[str] = None
    osm_category: Optional[str] = None

    @field_validator("hashtags", mode="before")
    @classmethod
    def validate_hashtags(
        cls,
        hashtags: Optional[str | list[str]],
    ) -> Optional[list[str]]:
        """Validate hashtags.

        - Receives a string and parsed as a list of tags.
        - Commas or semicolons are replaced with spaces before splitting.
        - Add '#' to hashtag if missing.
        """
        if hashtags is None:
            return None

        if isinstance(hashtags, str):
            hashtags = hashtags.replace(",", " ").replace(";", " ")
            hashtags_list = hashtags.split()
        else:
            hashtags_list = hashtags

        # Add '#' to hashtag strings if missing
        return [
            f"#{hashtag}" if hashtag and not hashtag.startswith("#") else hashtag
            for hashtag in hashtags_list
        ]

    @field_validator("outline", mode="before")
    @classmethod
    def parse_input_geojson(
        cls,
        value: FeatureCollection | Feature | MultiPolygon | Polygon,
        info: ValidationInfo,
    ) -> Optional[Union[Polygon, MultiPolygon]]:
        """Parse any format geojson into a single Polygon or MultiPolygon.

        NOTE we run this in mode='before' to allow parsing as Feature first.
        """
        if value is None:
            return None
        # FIXME also handle geometry collection type here
        # geojson_pydantic.GeometryCollection
        # FIXME update this to remove the Featcol parsing at some point
        featcol = geojson_to_featcol(value)
        merge = info.data.get("merge", True)
        merged_geojson = merge_polygons(
            featcol=featcol, merge=merge, dissolve_polygon=True
        )

        if merge:
            return merged_geojson.get("features")[0].get("geometry")
        else:
            geometries = [
                feature.get("geometry").get("coordinates")
                for feature in merged_geojson.get("features", [])
            ]
            return {"type": "MultiPolygon", "coordinates": geometries}

    @model_validator(mode="after")
    def append_fmtm_hashtag_and_slug(self) -> Self:
        """Append the #Field-TM hashtag and add URL slug."""
        # NOTE the slug is set here as the field_validator above
        # does not seem to work?
        self.slug = slugify(self.project_name)

        if not self.hashtags:
            self.hashtags = ["#Field-TM"]
        elif "#Field-TM" not in self.hashtags:
            self.hashtags.append("#Field-TM")
        return self


class ProjectInBase(StubProjectIn):
    """Base model for project insert / update (validators)."""

    # Override hashtag input to allow a single string input
    hashtags: Annotated[
        Optional[list[str] | str],
        Field(validate_default=True),
    ] = None
    project_name: Optional[str] = None

    # Token used for ODK appuser; encrypted at rest
    odk_token: Optional[str] = None

    # Add missing vars
    external_project_instance_url: Optional[str] = None
    external_project_id: Optional[int] = None
    external_project_username: Optional[str] = None
    external_project_password_encrypted: Optional[str] = None

    # Exclude (do not allow update)
    id: Annotated[Optional[int], Field(exclude=True)] = None
    field_mapping_app: Annotated[Optional[FieldMappingApp], Field(exclude=True)] = None
    outline: Annotated[Optional[dict], Field(exclude=True)] = None
    # Exclude (calculated fields)
    centroid: Annotated[Optional[dict], Field(exclude=True)] = None
    tasks: Annotated[Optional[list], Field(exclude=True)] = None
    bbox: Annotated[Optional[list[float]], Field(exclude=True)] = None
    last_active: Annotated[Optional[datetime], Field(exclude=True)] = None

    @field_validator("odk_token", mode="after")
    @classmethod
    def encrypt_token(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Token for insertion into the db."""
        if not value:
            return None
        return encrypt_value(value)


class ProjectIn(ProjectInBase, ODKCentralIn):
    """Input model for creating a project in ODK Central."""

    # Ensure geojson_pydantic.Polygon
    outline: Optional[Polygon] = None

    @property
    def odk_credentials(self) -> Optional[ODKCentralDecrypted]:
        """Convert ODK credentials to decrypted format.

        Return None to use defaults.
        """
        # If all ODK fields are None/empty, return None to use default env credentials
        if (
            not self.odk_central_url
            and not self.odk_central_user
            and not self.odk_central_password
        ):
            return None

        # Password comes in as plaintext from frontend (ODKCentralIn encrypts it for
        # storage)
        # But when reading from ProjectIn, it might already be encrypted if coming
        # from DB
        # For new projects, password should be plaintext from frontend
        password = self.odk_central_password
        if password:
            try:
                # Try to decrypt (if it's encrypted from DB)
                password = decrypt_value(password)
            except Exception:
                # If decryption fails, assume it's already plaintext (from frontend)
                pass

        return ODKCentralDecrypted(
            odk_central_url=self.odk_central_url,
            odk_central_user=self.odk_central_user,
            odk_central_password=password,
        )


class ProjectUpdate(ProjectInBase, ODKCentralIn):
    """Input model for updating a project (all fields optional)."""

    # Make required fields from StubProjectIn optional for updates
    project_name: Optional[str] = None
    field_mapping_app: Optional[FieldMappingApp] = None

    # Allow updating the name field
    name: Optional[str] = None
    # Override dict type to parse as Polygon
    outline: Optional[Polygon] = None
