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

from fastapi import HTTPException
from loguru import logger as log
from psycopg import Connection
from psycopg.rows import class_row

from app.db.enums import (
    HTTPStatus,
    TaskStatus,
    get_action_for_status_change,
)
from app.db.models import DbTask, DbTaskHistory
from app.tasks import task_schemas


# TODO SQL refactor this to use case statements on /next
async def new_task_event(
    db: Connection, task_id: int, user_id: int, new_status: TaskStatus
):
    """Add a new entry to the task events."""
    log.debug(f"Checking if task ({task_id}) is already locked")
    task_entry = await DbTask.one(db, task_id)

    if task_entry and task_entry.task_status in [
        TaskStatus.LOCKED_FOR_MAPPING,
        TaskStatus.LOCKED_FOR_VALIDATION,
    ]:
        if task_entry.actioned_by_uid != user_id:
            msg = f"Task is locked by user {task_entry.username}"
            log.error(msg)
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=msg)

    log.info(f"Updating task ID {task_id} to status {new_status}")
    new_event = task_schemas.TaskHistoryIn(
        task_id=task_id,
        user_id=user_id,
        action=get_action_for_status_change(new_status),
        # NOTE we don't include a comment unless necessary
    )
    new_task_event = await DbTaskHistory.create(db, new_event)
    return new_task_event


async def get_project_task_activity(
    db: Connection,
    project_id: int,
    days: int,
) -> task_schemas.TaskHistoryCount:
    """Get number of tasks mapped and validated for project.

    Args:
        project_id (int): The ID of the project.
        days (int): The number of days to consider for the
            task activity (default: 10).
        db (Connection): The database connection.

    Returns:
        list[task_schemas.TaskHistoryCount]: A list of task history counts.
    """
    end_date = datetime.now() - timedelta(days=days)

    sql = """
        SELECT
            to_char(action_date::date, 'dd/mm/yyyy') as date,
            COUNT(*) FILTER (WHERE action = 'VALIDATED') AS validated,
            COUNT(*) FILTER (WHERE action = 'MARKED_MAPPED') AS mapped
        FROM
            task_history
        WHERE
            project_id = %(project_id)s
            AND action_date >= %(end_date)s
        GROUP BY
            action_date::date
        ORDER BY
            action_date::date;
    """

    async with db.cursor(row_factory=class_row(task_schemas.TaskHistoryCount)) as cur:
        await cur.execute(sql, {"project_id": project_id, "end_date": end_date})
        return await cur.fetchall()
