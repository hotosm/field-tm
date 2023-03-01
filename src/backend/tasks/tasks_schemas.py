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


import enum
from datetime import datetime
from typing import List

from geojson_pydantic import Feature
from pydantic import BaseModel

from ..models.enums import TaskStatus


def get_task_status_strings():
    names = [option.name for option in TaskStatus]
    options = {names[i]: names[i] for i in range(len(names))}
    return enum.Enum("TaskStatusOptions", options)


# Dynamically creates String Enums for API based on Task Status options
TaskStatusOption = get_task_status_strings()


class TaskHistoryBase(BaseModel):
    id: int
    action_text: str
    action_date: datetime

    class Config:
        orm_mode = True


class TaskHistoryOut(TaskHistoryBase):
    pass


class TaskBase(BaseModel):
    id: int
    project_id: int
    project_task_index: int
    project_task_name: str
    outline_geojson: Feature
    outline_centroid: Feature
    # initial_feature_count: int
    task_status: TaskStatus
    locked_by_uid: int = None
    locked_by_username: str = None
    task_history: List[TaskHistoryBase]

    class Config:
        orm_mode = True


class Task(TaskBase):
    # geometry_geojson: str
    qr_code_base64: str
    task_status_str: TaskStatusOption
    pass


class TaskOut(TaskBase):
    pass


class TaskDetails(TaskBase):
    pass
