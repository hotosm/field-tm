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
"""Logic for FMTM tasks."""

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from loguru import logger as log
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.db import db_models
from app.db.postgis_utils import timestamp
from app.models.enums import (
    HTTPStatus,
    TaskStatus,
    get_action_for_status_change,
)
from app.tasks import tasks_schemas


async def get_task_count_in_project(db: Session, project_id: int):
    """Get task count for a project."""
    query = text(f"""select count(*) from tasks where project_id = {project_id}""")
    result = db.execute(query)
    return result.fetchone()[0]


async def get_task_id_list(db: Session, project_id: int) -> list[int]:
    """Get a list of tasks id for a project."""
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
    """Get task details for a project."""
    if project_id:
        db_tasks = (
            db.query(db_models.DbTask)
            .filter(db_models.DbTask.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    # TODO update this logic to filter events related to user (locked_by removed)
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


async def get_task(db: Session, task_id: int) -> db_models.DbTask:
    """Get details for a specific task ID."""
    log.debug(f"Getting task with ID '{task_id}' from database")
    return db.query(db_models.DbTask).filter(db_models.DbTask.id == task_id).first()


async def new_task_event(
    db: Session, project_id: int, task_id: int, user_id: int, new_status: TaskStatus
):
    """Add a new entry to the task events."""
    log.debug(f"Checking if task ({task_id}) is already locked")
    query = text("""
        SELECT
            th.action,
            th.user_id,
            u.username
        FROM
            task_history th
        LEFT JOIN
            users u ON th.user_id = u.id
        WHERE
            th.task_id = :task_id
        ORDER BY
            th.action_date DESC
        LIMIT 1
    """)

    result = db.execute(query, {"task_id": task_id})
    history_entry = result.fetchone()

    if history_entry and history_entry.action in [
        TaskStatus.LOCKED_FOR_MAPPING.value,
        TaskStatus.LOCKED_FOR_VALIDATION.value,
    ]:
        if history_entry.user_id != user_id:
            msg = f"Task is locked by user {history_entry.username}"
            log.error(msg)
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=msg)

    log.info(f"Updating task ID {task_id} to status {new_status}")
    query = text("""
        WITH new_history AS (
            INSERT INTO task_history (
                event_id,
                project_id,
                task_id,
                user_id,
                action,
                action_text,
                action_date
            ) VALUES (
                gen_random_uuid(),
                :project_id,
                :task_id,
                :user_id,
                :new_status,
                'CHANGED TO MAPPED by svcfmtm',
                NOW()
            )
            RETURNING *
        )
        SELECT
            nh.event_id,
            nh.project_id,
            nh.task_id,
            nh.user_id,
            nh.action,
            nh.action_text,
            nh.action_date,
            u.username,
            u.profile_img
        FROM
            new_history nh
        LEFT JOIN
            users u ON nh.user_id = u.id;
    """)

    result = db.execute(
        query,
        {
            "project_id": project_id,
            "task_id": task_id,
            "user_id": user_id,
            "new_status": new_status.name,
        },
    )

    history_entry = result.fetchone()

    if not history_entry:
        raise HTTPException(
            status_code=400, detail="Failed to create task history entry."
        )

    db.commit()
    return history_entry


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def create_task_history_for_status_change(
    db_task: db_models.DbTask, new_status: TaskStatus, db_user: db_models.DbUser
):
    """Append task status change to task history."""
    msg = (
        f"Task {db_task.id} changed from {db_task.task_status.name} "
        f"to {new_status.name} by {db_user.username}"
    )
    log.info(msg)

    new_task_history = db_models.DbTaskHistory(
        event_id=uuid4(),
        project_id=db_task.project_id,
        task_id=db_task.id,
        action=get_action_for_status_change(new_status),
        action_text=msg,
        action_date=timestamp(),
        user_id=db_user.id,
    )

    return new_task_history


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


async def add_task_comments(
    db: Session, comment: tasks_schemas.TaskCommentRequest, user_id: int
):
    """Add a comment to a task.

    Parameters:
    - db: SQLAlchemy database session
    - comment: TaskCommentBase instance containing the comment details
    - user_id: OAuth user id.

    Returns:
    - Dictionary with the details of the added comment
    """
    # Construct the query to insert the comment and retrieve inserted comment details
    query = text(
        """
        INSERT INTO public.task_history (
            event_id, project_id, task_id, action,
            action_text, action_date, user_id
        )
        VALUES (
            gen_random_uuid(), :project_id, :task_id, 'COMMENT',
            :comment_text, :current_date, :user_id
        )
        RETURNING
            task_history.event_id,
            task_history.action_text,
            task_history.action_date,
            (SELECT username FROM users WHERE id = :user_id) AS username,
            (SELECT profile_img FROM users WHERE id = :user_id) AS profile_img;
    """
    )

    # Define a dictionary with the parameter values
    params = {
        "project_id": comment.project_id,
        "task_id": comment.task_id,
        "comment_text": comment.comment,
        "current_date": timestamp(),
        "user_id": user_id,
    }

    # Execute the query with the named parameters and commit the transaction
    result = db.execute(query, params)
    db.commit()

    # Fetch the first row of the query result
    row = result.fetchone()

    # Return the details of the added comment as a dictionary
    return {
        "event_id": row[0],
        "action": "COMMENT",
        "action_text": row[1],
        "action_date": row[2],
        "username": row[3],
        "profile_img": row[4],
    }


async def get_project_task_history(
    task_id: int,
    comment: bool,
    end_date: datetime,
    db: Session,
) -> list:
    """Retrieves the task history records for a specific project.

    Args:
        task_id (int): The task_id of the project.
        comment (bool): True or False, True to get comments
            from the project tasks and False by default for
            entire task status history.
        end_date (datetime, optional): The end date of the task history
            records to retrieve.
        db (Session): The database session.

    Returns:
        A list of task history records for the specified project.
    """
    query = """
        SELECT
            th.event_id, th.action, th.action_text, th.action_date,
            u.username, u.profile_img
        FROM public.task_history th
        LEFT JOIN users u
            ON u.id = th.user_id
        WHERE task_id = :task_id AND  action_date >= :end_date
    """

    query += " AND action = 'COMMENT'" if comment else " AND action != 'COMMENT'"
    query += " ORDER BY id DESC;"

    result = db.execute(
        text(query), {"task_id": task_id, "end_date": end_date}
    ).fetchall()
    task_history = [
        {
            "event_id": row[0],
            "action": "COMMENT" if comment else row[1],
            "action_text": row[2],
            "action_date": row[3],
            "username": row[4],
            "profile_img": row[5],
        }
        for row in result
    ]

    return task_history


async def count_validated_and_mapped_tasks(
    task_history: list, end_date: datetime
) -> list[tasks_schemas.TaskHistoryCount]:
    """Counts the number of validated and mapped tasks.

    Args:
        task_history: The task history records to count.
        end_date: The end date of the date range.

    Returns:
        A list of dictionaries with following keys:
        - 'date': The date in the format 'MM/DD'.
        - 'validated': The cumulative count of validated tasks.
        - 'mapped': The cumulative count of mapped tasks.
    """
    cumulative_counts = {}
    results = []

    current_date = end_date
    while current_date <= datetime.now():
        date_str = current_date.strftime("%m/%d")
        cumulative_counts = {"date": date_str, "validated": 0, "mapped": 0}
        results.append(cumulative_counts)
        current_date += timedelta(days=1)

    # Populate cumulative_counts with counts from task_history
    for history in task_history:
        for result in history:
            task_status = result.get("status")
            date_str = (result.get("action_date")).strftime("%m/%d")
            entry = next(
                (entry for entry in results if entry["date"] == date_str), None
            )

            if entry:
                if task_status == "VALIDATED":
                    entry["validated"] += 1
                elif task_status == "MAPPED":
                    entry["mapped"] += 1

    total_validated = 0
    total_mapped = 0

    for entry in results:
        total_validated += entry["validated"]
        total_mapped += entry["mapped"]
        entry.update({"validated": total_validated, "mapped": total_mapped})

    return results
