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

from typing import List, Union, Optional

from geojson_pydantic import Feature
from pydantic import BaseModel

from ..models.enums import ProjectPriority, ProjectStatus
from ..tasks import tasks_schemas
from ..users.user_schemas import User


class ODKCentral(BaseModel):
    odk_central_url: str
    odk_central_user: str
    odk_central_password: str


class ProjectInfo(BaseModel):
    name: str
    short_description: str
    description: str


class ProjectUpdate(BaseModel):
    name: Union[str, None]
    short_description: Union[str, None]
    description: Union[str, None]


class BETAProjectUpload(BaseModel):
    author: User
    project_info: ProjectInfo
    xform_title: Union[str, None]
    odk_central: ODKCentral
    hashtags: Union[List[str], None]
    organisation_id: int = None
    # city: str
    # country: str


class ProjectSummary(BaseModel):
    id: int = -1
    priority: ProjectPriority = ProjectPriority.MEDIUM
    priority_str: str = priority.name
    title: Optional[str]
    location_str: Optional[str]
    description: Optional[str]
    total_tasks: Optional[int]
    tasks_mapped: Optional[int]
    num_contributors: Optional[int]
    tasks_validated: Optional[int]
    tasks_bad: Optional[int]
    hashtags: Optional[List[str]]
    organisation_id: Optional[int]
    organisation_logo: Optional[str]


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
    hashtags: List[str] = None
    organisation_id: int = None


class ProjectOut(ProjectBase):
    pass



class Feature(BaseModel):
    id: int
    project_id: int
    task_id: int = None
    geometry: Feature
