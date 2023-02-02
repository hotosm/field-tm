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

import base64
import json
from typing import List

from db import db_models
from db.postgis_utils import geometry_to_geojson, get_centroid
from fastapi import HTTPException
from geoalchemy2.shape import to_shape
from models.enums import (
    TaskAction,
    TaskStatus,
    get_action_for_status_change,
    verify_valid_status_update,
)
from shapely.geometry import mapping, shape
from sqlalchemy.orm import Session
from tasks import tasks_schemas
from users import user_crud, user_schemas

# --------------
# ---- CRUD ----
# --------------


def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 1000):
    if user_id:
        db_tasks = (
            db.query(db_models.DbTask)
            .filter(db_models.DbTask.locked_by == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        db_tasks = db.query(db_models.DbTask).offset(skip).limit(limit).all()
    return convert_to_app_tasks(db_tasks)


def get_task(db: Session, task_id: int, db_obj: bool = False):
    db_task = db.query(db_models.DbTask).filter(db_models.DbTask.id == task_id).first()
    if db_obj:
        return db_task
    return convert_to_app_task(db_task)


def update_task_status(db: Session, user_id: int, task_id: int, new_status: TaskStatus):
    if not user_id:
        raise HTTPException(status_code=400, detail="User id required.")

    db_user = user_crud.get_user(db, user_id, db_obj=True)
    if not db_user:
        raise HTTPException(
            status_code=400, detail=f"User with id {user_id} does not exist."
        )

    db_task = get_task(db, task_id, db_obj=True)

    if db_task:
        if (
            db_task.task_status
            in [TaskStatus.LOCKED_FOR_MAPPING, TaskStatus.LOCKED_FOR_VALIDATION]
        ) and user_id is not db_task.locked_by:
            raise HTTPException(
                status_code=401,
                detail=f"User {user_id} with username {db_user.username} has not locked this task.",
            )

        if verify_valid_status_update(db_task.task_status, new_status):
            # update history prior to updating task
            update_history = create_task_history_for_status_change(
                db_task, new_status, db_user
            )
            db.add(update_history)

            db_task.task_status = new_status

            if new_status in [
                TaskStatus.LOCKED_FOR_MAPPING,
                TaskStatus.LOCKED_FOR_VALIDATION,
            ]:
                db_task.locked_by = db_user.id
            else:
                db_task.locked_by = None

            if new_status == TaskStatus.MAPPED:
                db_task.mapped_by = db_user.id
            if new_status == TaskStatus.VALIDATED:
                db_task.validated_by = db_user.id
            if new_status == TaskStatus.INVALIDATED:
                db_task.mapped_by = None

            db.commit()
            db.refresh(db_task)

            return convert_to_app_task(db_task)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Not a valid status update: {db_task.task_status.name} to {new_status.name}",
        )


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


def create_task_history_for_status_change(
    db_task: db_models.DbTask, new_status: TaskStatus, db_user: db_models.DbUser
):
    new_task_history = db_models.DbTaskHistory(
        project_id=db_task.project_id,
        task_id=db_task.id,
        action=get_action_for_status_change(new_status),
        action_text=f"Status changed from {db_task.task_status.name} to {new_status.name} by: {db_user.username}",
        actioned_by=db_user,
        user_id=db_user.id,
    )

    # TODO add invalidation history
    # if new_status == TaskStatus.INVALIDATED:
    #     new_invalidation_history = db_models.DbTaskInvalidationHistory(
    #         project_id=db_task.project_id,
    #         task_id=db_task.id,
    #     )

    # TODO add mapping issue
    # if new_status == TaskStatus.BAD:

    return new_task_history


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


def convert_to_app_history(db_histories: List[db_models.DbTaskHistory]):
    if db_histories:
        app_histories: List[tasks_schemas.TaskHistoryBase] = []
        for db_history in db_histories:
            app_history = db_history
            app_history.obj = db_history.action_text
            app_histories.append(app_history)
        return app_histories
    return []


def convert_to_app_task(db_task: db_models.DbTask):
    if db_task:
        app_task: tasks_schemas.Task = db_task
        app_task.task_status_str = tasks_schemas.TaskStatusOption[
            app_task.task_status.name
        ]

        if db_task.outline:
            properties = {
                "fid": db_task.project_task_index,
                "uid": db_task.id,
                "name": db_task.project_task_name,
            }
            app_task.outline_geojson = geometry_to_geojson(db_task.outline, properties)
            app_task.outline_centroid = get_centroid(db_task.outline)

        if db_task.lock_holder:
            app_task.locked_by_uid = db_task.lock_holder.id
            app_task.locked_by_username = db_task.lock_holder.username

        if db_task.qr_code:
            app_task.qr_code_in_base64 = base64.b64encode(db_task.qr_code.image)

        if db_task.task_history:
            app_task.task_history = convert_to_app_history(db_task.task_history)

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
