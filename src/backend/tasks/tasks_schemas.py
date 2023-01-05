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
from geojson_pydantic import Feature, Point
import enum

from ..models.enums import TaskStatus


def get_task_status_strings():
    names = [option.name for option in TaskStatus]
    options = {names[i]: names[i] for i in range(len(names))}
    return enum.Enum('TaskStatusOptions', options)


# Dynamically creates String Enums for API based on Task Status options
TaskStatusOption = get_task_status_strings()


class TaskBase(BaseModel):
    id: int
    project_id: int
    project_task_index: int
    project_task_name: str
    outline_geojson: Feature
    outline_centroid: Feature
    initial_feature_count: int
    task_status: TaskStatus
    locked_by_uid: int = None

    class Config:
        orm_mode = True


class Task(TaskBase):
    geometry_geojson: str
    task_status_str: TaskStatusOption

    # qr_code_binary: bytes
    pass


class TaskOut(TaskBase):
    pass


class TaskDetails(TaskBase):
    pass
