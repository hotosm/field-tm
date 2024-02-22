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

from typing import Any, Optional, Union

from fastapi import Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_models import DbProject
from app.models.enums import HTTPStatus
from app.projects import project_crud, project_schemas


async def get_project_by_id(
    db: Session = Depends(get_db), project_id: Optional[int] = None
) -> DbProject:
    """Get a single project by id."""
    if not project_id:
        # Skip if no project id passed
        return None

    db_project = db.query(DbProject).filter(DbProject.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Project with ID {project_id} does not exist",
        )

    return db_project


async def get_odk_credentials(db: Session, project: Union[int, Any]):
    """Get odk credentials of project."""
    if isinstance(project, int):
        db_project = await project_crud.get_project(db, project)
    else:
        db_project = project

    odk_credentials = {
        "odk_central_url": db_project.odk_central_url,
        "odk_central_user": db_project.odk_central_user,
        "odk_central_password": db_project.odk_central_password,
    }

    return project_schemas.ODKCentralDecrypted(**odk_credentials)
