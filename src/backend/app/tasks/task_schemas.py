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

from typing import Annotated, Optional
from uuid import UUID

from geojson_pydantic import Polygon
from pydantic import BaseModel, Field, computed_field

from app.db.enums import TaskAction, TaskStatus, get_status_for_action
from app.db.models import DbTask, DbTaskHistory

# NOTE we don't have a TaskIn as tasks are only generated once during project creation


class TaskOut(DbTask):
    """Task for serialising and display."""

    # Parse as geojson_pydantic.Polygon
    outline: Polygon


class TaskHistoryIn(DbTaskHistory):
    """Create a new task event."""

    # Exclude, as the uuid is generated in the database
    event_id: Annotated[Optional[UUID], Field(exclude=True)] = None
    # Exclude, as we get the project_id in the db from the task id
    project_id: Annotated[Optional[int], Field(exclude=True)] = None

    # Omit computed fields
    username: Annotated[Optional[str], Field(exclude=True)] = None
    profile_img: Annotated[Optional[str], Field(exclude=True)] = None


class TaskHistoryOut(DbTaskHistory):
    """A task event to display to the user."""

    # Ensure project_id is removed, as we only use this to query for tasks
    project_id: Annotated[Optional[int], Field(exclude=True)] = None
    # We calculate the 'status' field in place of the action enum
    action: Annotated[Optional[TaskAction], Field(exclude=True)] = None

    @computed_field
    @property
    def status(self) -> Optional[TaskStatus]:
        """Get the status from the recent action.

        TODO remove this, replace with 'action' or similar?
        """
        if not self.action:
            return None
        return get_status_for_action(self.action)


class TaskHistoryCount(BaseModel):
    """Task mapping history status counts per day."""

    date: str
    validated: int
    mapped: int
