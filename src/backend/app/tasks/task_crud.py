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

from datetime import datetime, timedelta, timezone

from psycopg import Connection
from psycopg.rows import class_row

from app.central.central_crud import get_entities_data, update_entity_mapping_status
from app.db.enums import EntityState
from app.db.models import DbOdkEntities, DbProject
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


async def trigger_unlock_tasks(db: Connection):
    """Function to unlock_old_locked_tasks manually."""
    active_projects_query = """
        SELECT DISTINCT project_id
        FROM task_events
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """
    async with db.cursor() as cur:
        await cur.execute(active_projects_query)
        active_projects = await cur.fetchall()

    time_now = datetime.now(timezone.utc)
    threedaysago = (time_now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    onehourago = (time_now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    for (project_id,) in active_projects:
        project = await DbProject.one(db, project_id, True)

        recent_project_entities = await get_entities_data(
            project.odk_credentials, project.odkid, filter_date=threedaysago
        )
        # If there are recent entity updates, skip this project
        if recent_project_entities:
            continue

        await reset_entities_status(db, project.id, onehourago)

        # Only unlock tasks if there are no recent entity updates
        await unlock_old_locked_tasks(db, project.id)


async def reset_entities_status(db, project_id, filter_date):
    """Reset status for entities that have been 'open in ODK' for more than 1hr."""
    project = await DbProject.one(db, project_id, True)
    recent_opened_entities = await get_entities_data(
        project.odk_credentials,
        project.odkid,
        filter_date=filter_date,
    )
    for entity in recent_opened_entities:
        if entity["status"] != str(EntityState.OPENED_IN_ODK):
            continue
        await update_entity_mapping_status(
            project.odk_credentials,
            project.odkid,
            entity["id"],
            f"Task {entity['task_id']} Feature {entity['osm_id']}",
            str(EntityState.READY),
        )

    # Sync ODK entities in our database
    project_entities = await get_entities_data(project.odk_credentials, project.odkid)
    await DbOdkEntities.upsert(db, project.id, project_entities)


async def unlock_old_locked_tasks(db, project_id):
    """Unlock tasks locked for more than 3 days."""
    unlock_query = """
        WITH svc_user AS (
            SELECT id AS svc_user_id, username AS svc_username
            FROM users
            WHERE username = 'svcfmtm'
        ),
        recent_events AS (
            SELECT DISTINCT ON (t.id, t.project_id)
                t.id AS task_id,
                t.project_id,
                the.created_at AS last_event_time,
                the.event AS last_event
            FROM tasks t
            JOIN task_events the
                ON t.id = the.task_id
                AND t.project_id = the.project_id
                AND the.comment IS NULL
            WHERE t.project_id = %(project_id)s
            ORDER BY t.id, t.project_id, the.created_at DESC
        ),
        filtered_events AS (
            SELECT *
            FROM recent_events
            WHERE (
                (last_event = 'ASSIGN' AND last_event_time < NOW() - INTERVAL '3 days')
            OR
                (last_event = 'MAP' AND last_event_time < NOW() - INTERVAL '3 hours')
            )
        )
        INSERT INTO task_events (
            event_id,
            task_id,
            project_id,
            event,
            user_id,
            state,
            created_at,
            username
        )
        SELECT
            gen_random_uuid(),
            fe.task_id,
            fe.project_id,
            'RESET'::taskevent,
            svc.svc_user_id,
            'UNLOCKED_TO_MAP'::mappingstate,
            NOW(),
            svc.svc_username
        FROM filtered_events fe
        CROSS JOIN svc_user svc;
    """
    async with db.cursor() as cur:
        await cur.execute(unlock_query, {"project_id": project_id})
