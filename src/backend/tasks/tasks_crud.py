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

from geoalchemy2.shape import to_shape
from shapely.geometry import shape, mapping
from sqlalchemy.orm import Session
from typing import List
import json

from ..db import db_models
from ..db.postgis_utils import geometry_to_geojson
from ..tasks import tasks_schemas


# --------------
# ---- CRUD ----
# --------------

def get_tasks(db: Session, user_id: int, task_id: int, skip: int = 0, limit: int = 1000):
    if task_id:
        db_task = db.query(db_models.DbTask).filter(
            db_models.DbTask.id == task_id).offset(skip).limit(limit).first()
        return convert_to_app_task(db_task)
    if user_id:
        db_tasks = db.query(db_models.DbTask).filter(
            db_models.DbTask.locked_by == user_id).offset(skip).limit(limit).all()
    else:
        db_tasks = db.query(db_models.DbTask).offset(skip).limit(limit).all()
    return convert_to_app_tasks(db_tasks)

# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


def convert_to_app_task(db_task: db_models.DbTask):
    if db_task:
        app_task: tasks_schemas.Task = db_task

        if (db_task.outline):
            app_task.outline_geojson = geometry_to_geojson(db_task.outline)

        return app_task
    else:
        return None


def convert_to_app_tasks(db_tasks: List[db_models.DbTask]):
    if db_tasks and len(db_tasks) > 0:
        app_tasks = []
        for task in db_tasks:
            if task:
                app_tasks.append(convert_to_app_task(task))
        app_tasks_without_nones = [i for i in app_tasks if i is not None]
        return app_tasks_without_nones
    else:
        return []
