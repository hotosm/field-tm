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
from typing import List, Optional, Union

from dateutil import parser
from geojson_pydantic import Feature as GeojsonFeature
from pydantic import BaseModel, SecretStr
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator

from app.config import decrypt_value, encrypt_value
from app.db import db_models
from app.models.enums import ProjectPriority, ProjectStatus, TaskSplitType
from app.tasks import tasks_schemas
from app.users.user_schemas import User


class ODKCentral(BaseModel):
    """ODK Central credentials."""

    odk_central_url: str
    odk_central_user: str
    odk_central_password: SecretStr

    def model_post_init(self, ctx):
        """Run logic after model object instantiated."""
        # Decrypt odk central password from database
        self.odk_central_password = SecretStr(
            decrypt_value(self.odk_central_password.get_secret_value())
        )

    @field_validator("odk_central_password", mode="before")
    @classmethod
    def encrypt_odk_password(cls, value: str) -> SecretStr:
        """Encrypt the ODK Central password before db insertion."""
        return SecretStr(encrypt_value(value))

    @field_validator("odk_central_url", mode="before")
    @classmethod
    def remove_trailing_slash(cls, value: str) -> str:
        """Remove trailing slash from ODK Central URL."""
        if value.endswith("/"):
            return value[:-1]
        return value


class ProjectInfo(BaseModel):
    """Basic project info."""

    name: str
    short_description: str
    description: str


class ProjectUpdate(BaseModel):
    """Update project."""

    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None


class ProjectUpload(BaseModel):
    """Upload new project."""

    author: User
    project_info: ProjectInfo
    xform_title: Optional[str]
    odk_central: ODKCentral
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None
    task_split_type: Optional[TaskSplitType] = None
    task_split_dimension: Optional[int] = None
    task_num_buildings: Optional[int] = None
    data_extract_type: Optional[str] = None

    # city: str
    # country: str


class Feature(BaseModel):
    """Features used for Task definitions."""

    id: int
    geometry: Optional[GeojsonFeature] = None


class ProjectSummary(BaseModel):
    """Project summaries."""

    id: int = -1
    priority: ProjectPriority = ProjectPriority.MEDIUM
    priority_str: str = priority.name
    title: Optional[str] = None
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

    @classmethod
    def from_db_project(
        cls,
        project: db_models.DbProject,
    ) -> "ProjectSummary":
        """Generate model from database obj."""
        priority = project.priority
        return cls(
            id=project.id,
            priority=priority,
            priority_str=priority.name,
            title=project.title,
            location_str=project.location_str,
            description=project.description,
            total_tasks=project.total_tasks,
            tasks_mapped=project.tasks_mapped,
            num_contributors=project.num_contributors,
            tasks_validated=project.tasks_validated,
            tasks_bad=project.tasks_bad,
            hashtags=project.hashtags,
            organisation_id=project.organisation_id,
            organisation_logo=project.organisation_logo,
        )


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

    id: int
    odkid: int
    author: User
    project_info: ProjectInfo
    status: ProjectStatus
    # location_str: str
    outline_geojson: Optional[GeojsonFeature] = None
    project_tasks: Optional[List[tasks_schemas.Task]]
    xform_title: Optional[str] = None
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None


class ProjectOut(ProjectBase):
    """Project display to user."""

    project_uuid: uuid.UUID = uuid.uuid4()


class ReadProject(ProjectBase):
    """Redundant model for refactor."""

    project_uuid: uuid.UUID = uuid.uuid4()
    location_str: Optional[str] = None


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
