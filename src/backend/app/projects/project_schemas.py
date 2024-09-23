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
"""Pydantic schemas for Projects."""

import uuid
from datetime import datetime
from typing import Any, List, Optional, Union

from dateutil import parser
from geojson_pydantic import Feature, FeatureCollection, MultiPolygon, Polygon
from loguru import logger as log
from pydantic import BaseModel, Field, computed_field
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator, model_validator
from shapely import wkb
from typing_extensions import Self

from app.config import HttpUrlStr, decrypt_value, encrypt_value, settings
from app.db.postgis_utils import (
    featcol_to_wkb_geom,
    geojson_to_featcol,
    get_address_from_lat_lon,
    merge_polygons,
    read_wkb,
    wkb_geom_to_feature,
    write_wkb,
)
from app.models.enums import ProjectPriority, ProjectStatus, TaskSplitType, XLSFormType
from app.tasks import tasks_schemas
from app.users.user_schemas import User


class ODKCentral(BaseModel):
    """ODK Central credentials."""

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    @field_validator("odk_central_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return None
        if value.endswith("/"):
            return value[:-1]
        return value

    @model_validator(mode="after")
    def all_odk_vars_together(self) -> Self:
        """Ensure if one ODK variable is set, then all are."""
        if any(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ) and not all(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ):
            err = "All ODK details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)
        return self


class ODKCentralIn(ODKCentral):
    """ODK Central credentials inserted to database."""

    @field_validator("odk_central_password", mode="after")
    @classmethod
    def encrypt_odk_password(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Central password before db insertion."""
        if not value:
            return None
        return encrypt_value(value)


class ODKCentralDecrypted(BaseModel):
    """ODK Central credentials extracted from database.

    WARNING never return this as a response model.
    WARNING or log to the terminal.
    """

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    def model_post_init(self, ctx):
        """Run logic after model object instantiated."""
        # Decrypt odk central password from database
        if self.odk_central_password:
            if isinstance(self.odk_central_password, str):
                password = self.odk_central_password
            else:
                password = self.odk_central_password
            self.odk_central_password = decrypt_value(password)

    @field_validator("odk_central_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return None
        if value.endswith("/"):
            return value[:-1]
        return value


class ProjectInfo(BaseModel):
    """Basic project info."""

    name: str
    short_description: str
    description: str
    per_task_instructions: Optional[str] = None


class ProjectIn(BaseModel):
    """Upload new project."""

    project_info: ProjectInfo
    xform_category: str
    custom_tms_url: Optional[str] = None
    organisation_id: Optional[int] = None
    hashtags: Optional[str] = None
    task_split_type: Optional[TaskSplitType] = None
    task_split_dimension: Optional[int] = None
    task_num_buildings: Optional[int] = None
    data_extract_type: Optional[str] = None
    outline_geojson: Union[FeatureCollection, Feature, MultiPolygon, Polygon]
    location_str: Optional[str] = None

    @computed_field
    @property
    def outline(self) -> Optional[Any]:
        """Compute WKBElement geom from geojson."""
        if not self.outline_geojson:
            return None

        outline = geojson_to_featcol(self.outline_geojson.model_dump())
        outline_merged = merge_polygons(outline)

        return featcol_to_wkb_geom(outline_merged)

    @computed_field
    @property
    def centroid(self) -> Optional[Any]:
        """Compute centroid for project outline."""
        if not self.outline:
            return None
        return write_wkb(read_wkb(self.outline).centroid)

    @computed_field
    @property
    def project_name_prefix(self) -> str:
        """Compute project name prefix with underscores."""
        return self.project_info.name.replace(" ", "_").lower()

    @field_validator("hashtags", mode="after")
    @classmethod
    def validate_hashtags(cls, hashtags: Optional[str]) -> List[str]:
        """Validate hashtags.

        - Receives a string and parsed as a list of tags.
        - Commas or semicolons are replaced with spaces before splitting.
        - Add '#' to hashtag if missing.
        - Also add default '#FMTM' tag.
        """
        if hashtags is None:
            return ["#FMTM"]

        hashtags = hashtags.replace(",", " ").replace(";", " ")
        hashtags_list = hashtags.split()

        # Add '#' to hashtag strings if missing
        hashtags_with_hash = [
            f"#{hashtag}" if hashtag and not hashtag.startswith("#") else hashtag
            for hashtag in hashtags_list
        ]

        if "#FMTM" not in hashtags_with_hash:
            hashtags_with_hash.append("#FMTM")

        return hashtags_with_hash

    @model_validator(mode="after")
    def generate_location_str(self) -> Self:
        """Generate location string after centroid is generated.

        NOTE chaining computed_field didn't seem to work here so a
        model_validator was used for final stage validation.
        """
        if not self.centroid:
            log.warning("Project has no centroid, location string not determined")
            return self

        if self.location_str is not None:
            # Prevent running triggering multiple times if already set
            return self

        geom = read_wkb(self.centroid)
        latitude, longitude = geom.y, geom.x
        address = get_address_from_lat_lon(latitude, longitude)
        self.location_str = address if address is not None else ""
        return self


class ProjectUpload(ProjectIn, ODKCentralIn):
    """Project upload details, plus ODK credentials."""

    pass


class ProjectPartialUpdate(BaseModel):
    """Update projects metadata."""

    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[List[str]] = None
    per_task_instructions: Optional[str] = None

    @computed_field
    @property
    def project_name_prefix(self) -> Optional[str]:
        """Compute project name prefix with underscores."""
        if not self.name:
            return None
        return self.name.replace(" ", "_").lower()


class ProjectUpdate(ProjectUpload):
    """Update project."""

    pass


class GeojsonFeature(BaseModel):
    """Features used for Task definitions."""

    id: int
    geometry: Optional[Feature] = None


class ProjectSummary(BaseModel):
    """Project summaries."""

    id: int
    priority: ProjectPriority
    title: Optional[str] = None
    # NOTE we cannot be WKBElement element here, as it can't be serialized
    centroid: Optional[Any]
    location_str: Optional[str] = None
    description: Optional[str] = None
    total_tasks: Optional[int] = None
    tasks_mapped: Optional[int] = None
    num_contributors: Optional[int] = None
    tasks_validated: Optional[int] = None
    tasks_bad: Optional[int] = None
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None
    organisation_logo: Optional[str] = None

    @field_serializer("centroid")
    def get_coord_from_centroid(self, value) -> Optional[list[float]]:
        """Get the cetroid coordinates from WBKElement."""
        if value is None:
            return None
        centroid_point = read_wkb(value)
        centroid = [centroid_point.x, centroid_point.y]
        return centroid


class PaginationInfo(BaseModel):
    """Pagination JSON return."""

    has_next: bool
    has_prev: bool
    next_num: Optional[int]
    page: int
    pages: int
    prev_num: Optional[int]
    per_page: int
    total: int


class PaginatedProjectSummaries(BaseModel):
    """Project summaries + Pagination info."""

    results: List[ProjectSummary]
    pagination: PaginationInfo


class ProjectBase(BaseModel):
    """Base project model."""

    outline: Any = Field(exclude=True)
    odk_form_id: Optional[str] = Field(exclude=True)

    id: int
    odkid: int
    author: User
    project_info: ProjectInfo
    status: ProjectStatus
    created: datetime
    # location_str: str
    xform_category: Optional[XLSFormType] = None
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None

    @computed_field
    @property
    def outline_geojson(self) -> Optional[Feature]:
        """Compute the geojson outline from WKBElement outline."""
        if not self.outline:
            return None
        geometry = wkb.loads(bytes(self.outline.data))
        bbox = geometry.bounds  # Calculate bounding box
        geom_geojson = wkb_geom_to_feature(
            geometry=self.outline,
            properties={"id": self.id, "bbox": bbox},
            id=self.id,
        )
        return Feature(**geom_geojson)

    @computed_field
    @property
    def organisation_logo(self) -> Optional[str]:
        """Get the organisation logo url from the S3 bucket."""
        if not self.organisation_id:
            return None

        return (
            f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}"
            f"/{self.organisation_id}/logo.png"
        )

    @computed_field
    @property
    def xform_id(self) -> Optional[str]:
        """Generate from odk_form_id.

        TODO this could be refactored out in future.
        """
        if not self.odk_form_id:
            return None
        return self.odk_form_id


class ProjectWithTasks(ProjectBase):
    """Project plus list of tasks objects."""

    tasks: Optional[List[tasks_schemas.Task]]


class ProjectOut(ProjectWithTasks):
    """Project display to user."""

    project_uuid: uuid.UUID = uuid.uuid4()


class ReadProject(ProjectWithTasks):
    """Redundant model for refactor."""

    odk_token: Optional[str] = None
    project_uuid: uuid.UUID = uuid.uuid4()
    location_str: Optional[str] = None
    data_extract_url: Optional[str] = None
    custom_tms_url: Optional[str] = None

    @field_serializer("odk_token")
    def decrypt_password(self, value: str) -> Optional[str]:
        """Decrypt the ODK Token extracted from the db."""
        if not value:
            return ""

        return decrypt_value(value)


class BackgroundTaskStatus(BaseModel):
    """Background task status for project related tasks."""

    status: str
    message: Optional[str] = None


class ProjectDashboard(BaseModel):
    """Project details dashboard."""

    project_name_prefix: str
    organisation_name: str
    total_tasks: int
    created: datetime
    organisation_logo: Optional[str] = None
    total_submission: Optional[int] = None
    total_contributors: Optional[int] = None
    last_active: Optional[Union[str, datetime]] = None

    @field_serializer("last_active")
    def get_last_active(self, value, values):
        """Date of last activity on project."""
        if value is None:
            return None

        last_active = parser.parse(value).replace(tzinfo=None)
        current_date = datetime.now()

        time_difference = current_date - last_active

        days_difference = time_difference.days

        if days_difference == 0:
            return "today"
        elif days_difference == 1:
            return "yesterday"
        elif days_difference < 7:
            return f'{days_difference} day{"s" if days_difference > 1 else ""} ago'
        else:
            return last_active.strftime("%d %b %Y")
