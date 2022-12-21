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

from ..models.enums import TaskStatus

class TaskBase(BaseModel):
    id: int
    project_id: int
    project_task_index: int
    project_task_name: str
    outline_geojson: str
    initial_feature_count: int
    task_status: TaskStatus

    class Config:
        orm_mode = True

class Task(TaskBase):
    geometry_geojson: str 
    pass

class TaskOut(TaskBase):
    pass

class TaskDetails(TaskBase):
    pass