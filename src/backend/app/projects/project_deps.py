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

"""Project dependencies for use in Depends."""

from typing import Optional

from async_lru import alru_cache
from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import db_models
from app.db.database import get_db
from app.models.enums import HTTPStatus
from app.projects import project_schemas


async def get_project_by_id(
    db: Session = Depends(get_db), project_id: Optional[int] = None
):
    """Get a single project by id."""
    if not project_id:
        # Skip if no project id passed
        # FIXME why do we need this?
        return None

    # TODO replace outline / centroid with geojson equivalent
    # TODO when we remove SQLALchemy
    # ST_AsGeoJSON(p.outline)::jsonb AS outline,
    # ST_AsGeoJSON(p.centroid)::jsonb AS centroid,
    query = text("""
        WITH latest_task_history AS (
            SELECT DISTINCT ON (task_id)
                task_id,
                action,
                action_date,
                user_id
            FROM
                task_history
            WHERE
                action != 'COMMENT'
            ORDER BY
                task_id, action_date DESC
        )
        SELECT
            p.*,
            ST_AsGeoJSON(p.outline)::jsonb AS outline,
            ST_AsGeoJSON(p.centroid)::jsonb AS centroid,
            JSON_BUILD_OBJECT(
                'project_id', pi.project_id,
                'project_id_str', pi.project_id_str,
                'name', pi.name,
                'short_description', pi.short_description,
                'description', pi.description,
                'text_searchable', pi.text_searchable,
                'per_task_instructions', pi.per_task_instructions
            ) AS project_info,
            JSON_BUILD_OBJECT(
                'id', project_author.id,
                'username', project_author.username
            ) AS author,
            COALESCE(
                JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'id', t.id,
                        'project_id', t.project_id,
                        'project_task_index', t.project_task_index,
                        'outline', ST_AsGeoJSON(t.outline)::jsonb,
                        'feature_count', t.feature_count,
                        'task_status', COALESCE(
                            latest_th.action,
                            'RELEASED_FOR_MAPPING'
                        ),
                        'locked_by_uid', COALESCE(
                            latest_user.id,
                            NULL
                        ),
                        'locked_by_username', COALESCE(
                            latest_user.username,
                            NULL
                        )
                    )
                ) FILTER (WHERE t.id IS NOT NULL), '[]'::json
            ) AS tasks
        FROM
            projects p
        LEFT JOIN
            project_info pi ON p.id = pi.project_id
        LEFT JOIN
            users project_author ON p.author_id = project_author.id
        LEFT JOIN
            tasks t ON p.id = t.project_id
        LEFT JOIN
            latest_task_history latest_th ON t.id = latest_th.task_id
        LEFT JOIN
            users latest_user ON latest_th.user_id = latest_user.id
        WHERE
            p.id = :project_id
        GROUP BY
            p.id, pi.project_id, project_author.id;
    """)

    result = db.execute(query, {"project_id": project_id})
    row = result.fetchone()

    # db_project = db.query(DbProject).filter(DbProject.id == project_id).first()
    if not row:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Project with ID {project_id} does not exist",
        )

    if row.odk_token is None:
        log.warning(
            f"Project ({row.id}) has no 'odk_token' set. The QRCode will not work!"
        )

    # FIXME Workaround to convert back to SQLAlchemy model for now
    # FIXME remove this once we remove SQLAlchemy
    project_dict = {**row._mapping}

    # FIXME this avoids an error as the fields do not exist on the model
    task_status_dict = {}
    task_lock_uid_dict = {}
    task_lock_user_dict = {}
    for task in project_dict["tasks"]:
        task_status_dict[task["id"]] = task["task_status"]
        del task["task_status"]
        task_lock_uid_dict[task["id"]] = task["locked_by_uid"]
        del task["locked_by_uid"]
        task_lock_user_dict[task["id"]] = task["locked_by_username"]
        del task["locked_by_username"]

    db_project = db_models.DbProject(**project_dict)

    for task in db_project.tasks:
        task.task_status = task_status_dict[task.id]
        task.locked_by_uid = task_lock_uid_dict[task.id]
        task.locked_by_username = task_lock_user_dict[task.id]

    return db_project


@alru_cache(maxsize=32)
async def get_odk_credentials(db: Session, project_id: int):
    """Get ODK credentials of a project, or default organization credentials."""
    sql = text("""
    SELECT
        COALESCE(
            NULLIF(projects.odk_central_url, ''),
            organisations.odk_central_url)
        AS odk_central_url,
        COALESCE(
            NULLIF(projects.odk_central_user, ''),
            organisations.odk_central_user)
        AS odk_central_user,
        COALESCE(
            NULLIF(projects.odk_central_password, ''),
            organisations.odk_central_password
        ) AS odk_central_password
    FROM
        projects
    LEFT JOIN
        organisations ON projects.organisation_id = organisations.id
    WHERE
        projects.id = :project_id
    """)
    result = db.execute(sql, {"project_id": project_id})
    creds = result.first()

    url = creds.odk_central_url
    user = creds.odk_central_user
    password = creds.odk_central_password

    log.debug(f"Retrieved ODK creds for project ({project_id}): {url} | {user}")

    return project_schemas.ODKCentralDecrypted(
        odk_central_url=url,
        odk_central_user=user,
        odk_central_password=password,
    )
