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
"""Pydantic schemas for FMTM task areas."""

from datetime import datetime
from typing import Any, List, Optional

from geojson_pydantic import Feature as GeojsonFeature
from loguru import logger as log
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, computed_field
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator

from app.config import decrypt_value
from app.db.postgis_utils import geometry_to_geojson, get_centroid
from app.models.enums import TaskStatus


class TaskHistoryBase(BaseModel):
    """Task mapping history."""

    id: int
    action_text: str
    action_date: datetime


class TaskHistoryOut(TaskHistoryBase):
    """Task mapping history display."""

    status: str
    username: str
    profile_img: Optional[str]


class TaskHistoryCount(BaseModel):
    """Task mapping history display."""

    date: str
    validated: int
    mapped: int


class Task(BaseModel):
    """Core fields for a Task."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_default=True,
    )

    # Excluded
    lock_holder: Any = Field(exclude=True)
    outline: Any = Field(exclude=True)

    id: int
    project_id: int
    project_task_index: int
    project_task_name: str
    outline_geojson: Optional[GeojsonFeature] = None
    outline_centroid: Optional[GeojsonFeature] = None
    initial_feature_count: Optional[int] = None
    task_status: TaskStatus
    locked_by_uid: Optional[int] = None
    locked_by_username: Optional[str] = None
    task_history: Optional[List[TaskHistoryBase]] = None
    odk_token: Optional[str] = None

    @field_validator("outline_geojson", mode="before")
    @classmethod
    def get_geojson_from_outline(cls, value: Any, info: ValidationInfo) -> str:
        """Get outline_geojson from Shapely geom."""
        if outline := info.data.get("outline"):
            properties = {
                "fid": info.data.get("project_task_index"),
                "uid": info.data.get("id"),
                "name": info.data.get("project_task_name"),
            }
            log.debug("Converting task outline to geojson")
            return geometry_to_geojson(outline, properties, info.data.get("id"))
        return None

    @field_validator("outline_centroid", mode="before")
    @classmethod
    def get_centroid_from_outline(
        cls, value: Any, info: ValidationInfo
    ) -> Optional[str]:
        """Get outline_centroid from Shapely geom."""
        if outline := info.data.get("outline"):
            properties = {
                "fid": info.data.get("project_task_index"),
                "uid": info.data.get("id"),
                "name": info.data.get("project_task_name"),
            }
            log.debug("Converting task outline to geojson")
            return get_centroid(outline, properties, info.data.get("id"))
        return None

    @field_serializer("locked_by_uid")
    def get_locked_by_uid(self, value: str) -> Optional[str]:
        """Get lock uid from lock_holder details."""
        if self.lock_holder:
            return self.lock_holder.id
        return None

    @field_serializer("locked_by_username")
    def get_locked_by_username(self, value: str) -> Optional[str]:
        """Get lock username from lock_holder details."""
        if self.lock_holder:
            return self.lock_holder.username
        return None

    @field_serializer("odk_token")
    def decrypt_password(self, value: str) -> Optional[str]:
        """Decrypt the ODK Token extracted from the db."""
        if not value:
            return ""

        return decrypt_value(value)


class ReadTask(Task):
    """Task details plus updated task history."""

    task_history: Optional[List[TaskHistoryOut]] = None


class TaskHistory(BaseModel):
    """Task history details."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    # Excluded
    user: Any = Field(exclude=True)

    task_id: int
    action_text: str
    action_date: datetime

    @computed_field
    @property
    def username(self) -> Optional[str]:
        """Get username from user db obj."""
        if self.user:
            return self.user.username
        return None

    @computed_field
    @property
    def profile_img(self) -> Optional[str]:
        """Get profile_img from user db obj."""
        if self.user:
            return self.user.profile_img
        return None

    @computed_field
    @property
    def status(self) -> Optional[str]:
        """Extract status from standard format action_text."""
        if self.action_text:
            split_text = self.action_text.split()
            if len(split_text) > 5:
                return split_text[5]
            else:
                return self.action_text
        return None
