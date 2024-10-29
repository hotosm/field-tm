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

from datetime import timedelta

from psycopg import Connection
from psycopg.rows import class_row

from app.db.postgis_utils import timestamp
from app.tasks import task_schemas


async def get_project_task_activity(
    db: Connection,
    project_id: int,
    days: int,
) -> task_schemas.TaskEventCount:
    """Get number of tasks mapped and validated for project.

    Args:
        project_id (int): The ID of the project.
        days (int): The number of days to consider for the
            task activity (default: 10).
        db (Connection): The database connection.

    Returns:
        list[task_schemas.TaskEventCount]: A list of task event counts.
    """
    end_date = timestamp() - timedelta(days=days)

    sql = """
        SELECT
            to_char(created_at::date, 'dd/mm/yyyy') as date,
            COUNT(*) FILTER (WHERE state = 'UNLOCKED_DONE') AS validated,
            COUNT(*) FILTER (WHERE state = 'UNLOCKED_TO_VALIDATE') AS mapped
        FROM
            task_events
        WHERE
            project_id = %(project_id)s
            AND created_at >= %(end_date)s
        GROUP BY
            created_at::date
        ORDER BY
            created_at::date;
    """

    async with db.cursor(row_factory=class_row(task_schemas.TaskEventCount)) as cur:
        await cur.execute(sql, {"project_id": project_id, "end_date": end_date})
        return await cur.fetchall()
