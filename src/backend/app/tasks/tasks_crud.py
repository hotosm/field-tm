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
import base64

from fastapi import HTTPException
from geoalchemy2.shape import from_shape
from geojson import dump
from loguru import logger as log
from osm_rawdata.postgres import PostgresClient
from shapely.geometry import shape
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..db import db_models
from ..models.enums import (
    TaskStatus,
    get_action_for_status_change,
    verify_valid_status_update,
)
from ..projects import project_crud
from ..users import user_crud


async def get_task_count_in_project(db: Session, project_id: int):
    query = text(f"""select count(*) from tasks where project_id = {project_id}""")
    result = db.execute(query)
    return result.fetchone()[0]


async def get_task_lists(db: Session, project_id: int):
    """Get a list of tasks for a project."""
    query = text(
        """
        SELECT id
        FROM tasks
        WHERE project_id = :project_id
    """
    )

    # Then execute the query with the desired parameter
    result = db.execute(query, {"project_id": project_id})

    # Fetch the result
    task_ids = [row.id for row in result]
    return task_ids


async def get_tasks(
    db: Session, project_id: int, user_id: int, skip: int = 0, limit: int = 1000
):
    if project_id:
        db_tasks = (
            db.query(db_models.DbTask)
            .filter(db_models.DbTask.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    elif user_id:
        db_tasks = (
            db.query(db_models.DbTask)
            .filter(db_models.DbTask.locked_by == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        db_tasks = db.query(db_models.DbTask).offset(skip).limit(limit).all()
    return db_tasks


async def get_task(db: Session, task_id: int):
    return db.query(db_models.DbTask).filter(db_models.DbTask.id == task_id).first()


async def update_task_status(
    db: Session, user_id: int, task_id: int, new_status: TaskStatus
):
    log.debug(f"Updating task ID {task_id} to status {new_status}")
    if not user_id:
        log.error(f"User id is not present: {user_id}")
        raise HTTPException(status_code=400, detail="User id required.")

    db_user = await user_crud.get_user(db, user_id)
    if not db_user:
        msg = f"User with id {user_id} does not exist."
        log.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    db_task = await get_task(db, task_id)
    log.debug(f"Returned task from db: {db_task}")

    if db_task:
        if db_task.task_status in [
            TaskStatus.LOCKED_FOR_MAPPING,
            TaskStatus.LOCKED_FOR_VALIDATION,
        ]:
            log.debug(f"Task {task_id} currently locked")
            if not (user_id is not db_task.locked_by):
                msg = (
                    f"User {user_id} with username {db_user.username} "
                    "has not locked this task."
                )
                log.error(msg)
                raise HTTPException(
                    status_code=401,
                    detail=msg,
                )

        if not verify_valid_status_update(db_task.task_status, new_status):
            msg = f"{new_status} is not a valid task status"
            log.error(msg)
            raise HTTPException(
                status_code=422,
                detail=msg,
            )

        # update history prior to updating task
        update_history = await create_task_history_for_status_change(
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
        return db_task

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Not a valid status update: {db_task.task_status.name} to {new_status.name}",
        )


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def create_task_history_for_status_change(
    db_task: db_models.DbTask, new_status: TaskStatus, db_user: db_models.DbUser
):
    msg = f"Status changed from {db_task.task_status.name} to {new_status.name} by: {db_user.username}"
    log.info(msg)

    new_task_history = db_models.DbTaskHistory(
        project_id=db_task.project_id,
        task_id=db_task.id,
        action=get_action_for_status_change(new_status),
        action_text=msg,
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


async def get_qr_codes_for_task(
    db: Session,
    task_id: int,
):
    task = await get_task(db=db, task_id=task_id)
    if task:
        if task.qr_code:
            log.debug(f"QR code found for task ID {task.id}. Converting to base64")
            qr_code = base64.b64encode(task.qr_code.image)
        else:
            log.debug(f"QR code not found for task ID {task.id}.")
            qr_code = None
        return {"id": task_id, "qr_code": qr_code}
    else:
        raise HTTPException(status_code=400, detail="Task does not exist")


async def get_task_by_id(db: Session, task_id: int):
    task = db.query(db_models.DbTask).filter(db_models.DbTask.id == task_id).first()
    print("Task ", task)
    return task


async def update_task_files(
    db: Session,
    project_id: int,
    project_odk_id: int,
    project_name: str,
    task_id: int,
    category: str,
    task_boundary: str,
):
    # This file will store osm extracts
    task_polygons = f"/tmp/{project_name}_{category}_{task_id}.geojson"

    # Update data extracts in the odk central
    pg = PostgresClient("underpass")

    category = "buildings"

    # This file will store osm extracts
    outfile = f"/tmp/test_project_{category}.geojson"

    # Delete all tasks of the project if there are some
    db.query(db_models.DbFeatures).filter(
        db_models.DbFeatures.task_id == task_id
    ).delete()

    # OSM Extracts
    outline_geojson = pg.getFeatures(
        boundary=task_boundary,
        filespec=outfile,
        polygon=True,
        xlsfile=f"{category}.xls",
        category=category,
    )

    updated_outline_geojson = {"type": "FeatureCollection", "features": []}

    # Collect feature mappings for bulk insert
    for feature in outline_geojson["features"]:
        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature["properties"]["title"] = ""

        feature_shape = shape(feature["geometry"])

        wkb_element = from_shape(feature_shape, srid=4326)
        updated_outline_geojson["features"].append(feature)

        db_feature = db_models.DbFeatures(
            project_id=project_id,
            geometry=wkb_element,
            properties=feature["properties"],
        )
        db.add(db_feature)
        db.commit()

    # Update task_polygons file containing osm extracts with the new geojson contents containing title in the properties.
    with open(task_polygons, "w") as jsonfile:
        jsonfile.truncate(0)  # clear the contents of the file
        dump(updated_outline_geojson, jsonfile)

    # Update the osm extracts in the form.
    central_crud.upload_xform_media(project_odk_id, task_id, task_polygons, None)

    return True


async def edit_task_boundary(db: Session, task_id: int, boundary: str):
    """Update the boundary polyon on the database."""
    geometry = boundary["features"][0]["geometry"]
    outline = shape(geometry)

    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.outline = outline.wkt
    db.commit()

    # Get category, project_name
    project_id = task.project_id
    project = await project_crud.get_project(db, project_id)
    category = project.xform_title
    project_name = project.project_name_prefix
    odk_id = project.odkid

    await update_task_files(
        db, project_id, odk_id, project_name, task_id, category, geometry
    )

    return True
