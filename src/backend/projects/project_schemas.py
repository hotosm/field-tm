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

from typing import List, Union

from geojson_pydantic import Feature
from pydantic import BaseModel
from typing import List

from ..models.enums import ProjectPriority, ProjectStatus
from ..tasks import tasks_schemas
from ..users.user_schemas import User


class ODKCentral(BaseModel):
    odk_central_url: str
    odk_central_user: str
    odk_central_password: str

    class Config:
        orm_mode = True


class ProjectInfo(BaseModel):
    name: str
    short_description: str
    description: str
    class Config:
        orm_mode = True

class ProjectUpdate(BaseModel):
    name: Union[str, None]
    short_description: Union[str, None]
    description: Union[str, None]


class BETAProjectUpload(BaseModel):
    author: User
    project_info: ProjectInfo
    xform_title: Union[str, None]
    odk_central : ODKCentral
    # city: str
    # country: str


class ProjectSummary(BaseModel):
    id: int = -1
    priority: ProjectPriority = ProjectPriority.MEDIUM
    priority_str: str = priority.name
    title: str = None
    location_str: str = None
    description: str = None
    num_contributors: int = None
    total_tasks: int = None
    tasks_mapped: int = None
    tasks_validated: int = None
    tasks_bad: int = None

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    id: int
    odkid: int
    author: User
    project_info: List[ProjectInfo]
    status: ProjectStatus
    # location_str: str
    outline_geojson: Feature = None
    project_tasks: List[tasks_schemas.Task] = None
    xform_title: str = None

    class Config:
        orm_mode = True


class ProjectOut(ProjectBase):
    pass


class Organisation(BaseModel):
    # id: int
    slug: str
    logo: str
    name: str
    description:str
    url:str
    type:int


class Feature(BaseModel):
    id: int
    project_id: int
    task_id: int
    geometry: Feature

    class Config:
        orm_mode = True