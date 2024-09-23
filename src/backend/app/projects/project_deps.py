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

from app.db.database import get_db
from app.db.db_models import DbProject
from app.models.enums import HTTPStatus
from app.projects import project_schemas


async def get_project_by_id(
    db: Session = Depends(get_db), project_id: Optional[int] = None
) -> DbProject:
    """Get a single project by id."""
    if not project_id:
        # Skip if no project id passed
        # FIXME why do we need this?
        return None

    db_project = db.query(DbProject).filter(DbProject.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Project with ID {project_id} does not exist",
        )

    if db_project.odk_token == "":
        log.warning(
            f"Project ({db_project.id}) has no 'odk_token' set. "
            "The QRCode will not work!"
        )

    return db_project


@alru_cache(maxsize=32)
async def get_odk_credentials(db: Session, project_id: int):
    """Get ODK credentials of a project, or default organization credentials."""
    sql = text(
        """
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
    """
    )
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
