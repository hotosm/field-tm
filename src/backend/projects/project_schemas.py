# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

from pydantic import BaseModel
from typing import List, Any
from shapely.geometry import shape

from ..users.user_schemas import User
from ..models.enums import ProjectStatus, ProjectPriority
from ..tasks import tasks_schemas


class ProjectInfo(BaseModel):
    locale: str
    name: str
    short_description: str
    description: str
    instructions: str
    per_task_instructions: str

    class Config:
        orm_mode = True


class BETAProjectUpload(BaseModel):
    author: User
    project_info: ProjectInfo
    city: str
    country: str


class ProjectSummary(BaseModel):
    id: int = -1
    priority: ProjectPriority = ProjectPriority.MEDIUM
    title: str = None
    location_str: str = None
    description: str = None
    total_tasks: int = None
    tasks_mapped: int = None
    tasks_validated: int = None
    tasks_bad_imagery: int = None

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    id: int
    author: User
    default_locale: str
    project_info: List[ProjectInfo]
    status: ProjectStatus
    location_str: str
    outline_geojson: str = None
    project_tasks: List[tasks_schemas.Task] = None

    class Config:
        orm_mode = True


class Project(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    pass
