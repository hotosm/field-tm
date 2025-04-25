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
"""Pydantic schemas for Field-TM task areas."""

from typing import Annotated, Optional
from uuid import UUID

from geojson_pydantic import Polygon
from pydantic import BaseModel, Field

from app.db.enums import MappingState
from app.db.models import DbTask, DbTaskEvent

# NOTE we don't have a TaskIn as tasks are only generated once during project creation


class TaskOut(DbTask):
    """Task for serialising and display."""

    # Parse as geojson_pydantic.Polygon
    outline: Polygon


class TaskEventIn(DbTaskEvent):
    """Create a new task event."""

    # Exclude, as the uuid is generated in the database
    event_id: Annotated[Optional[UUID], Field(exclude=True)] = None
    # Exclude, as we get the project_id in the db from the task id
    project_id: Annotated[Optional[int], Field(exclude=True)] = None
    # Exclude, as state is generated based on event type in db
    state: Annotated[Optional[MappingState], Field(exclude=True)] = None

    # Omit computed fields
    username: Annotated[Optional[str], Field(exclude=True)] = None
    profile_img: Annotated[Optional[str], Field(exclude=True)] = None


class TaskEventOut(DbTaskEvent):
    """A task event to display to the user."""

    # Ensure project_id is removed, as we only use this to query for tasks
    project_id: Annotated[Optional[int], Field(exclude=True)] = None


class TaskEventCount(BaseModel):
    """Task mapping history status counts per day."""

    date: str
    mapped: int
    validated: int
