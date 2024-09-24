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
from typing import Any, Optional

from geojson_pydantic import Feature
from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.functional_validators import field_validator
from pydantic.types import UUID4

from app.models.enums import TaskAction, TaskStatus, get_status_for_action


class TaskHistoryBase(BaseModel):
    """Task mapping history."""

    event_id: UUID4
    action_text: Optional[str]
    action_date: datetime


class TaskHistoryOut(TaskHistoryBase):
    """Task mapping history display."""

    action: Any = Field(exclude=True)

    username: str
    profile_img: Optional[str]

    @computed_field
    @property
    def status(self) -> Optional[TaskStatus]:
        """Get the status from the recent action."""
        if not self.action:
            return None
        return get_status_for_action(self.action)


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
    outline: Any = Field(exclude=True)

    id: int
    project_id: int
    project_task_index: int
    feature_count: Optional[int] = None
    task_status: TaskStatus
    # TODO check the logic in project_deps, as it doesn't check if action is locked
    locked_by_uid: Optional[int] = None
    locked_by_username: Optional[str] = None

    @computed_field
    @property
    def outline_geojson(self) -> Optional[Feature]:
        """TODO this is now the same as self.outline."""
        if not self.outline:
            return None
        # TODO refactor to remove outline_geojson
        # TODO possibly also generate bbox for geojson in project_deps SQL?
        feat = {
            "type": "Feature",
            "geometry": self.outline,
            "id": self.id,
            "properties": {"fid": self.project_task_index, "uid": self.id},
        }
        return Feature(**feat)

    @field_validator("task_status", mode="before")
    @classmethod
    def enum_get_status_for_action(cls, value: str) -> TaskStatus:
        """Get the the int value from a string enum."""
        return get_status_for_action(TaskAction[value])


class TaskCommentResponse(TaskHistoryOut):
    """Wrapper Class for comment."""


class TaskCommentRequest(BaseModel):
    """Task comment form."""

    task_id: int
    project_id: int
    comment: str


class TaskHistory(BaseModel):
    """Task history details."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    # Excluded
    action: Any = Field(exclude=True)
    user: Any = Field(exclude=True)

    task_id: int
    action_text: Optional[str]
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
    def status(self) -> Optional[TaskStatus]:
        """Get the status from the recent action."""
        if not self.action:
            return None
        return get_status_for_action(self.action)
