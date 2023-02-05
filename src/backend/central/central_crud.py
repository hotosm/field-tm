# Copyright (c) 2023 Humanitarian OpenStreetMap Team
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

from fastapi import HTTPException
from fastapi.logger import logger as logger
from geoalchemy2.shape import to_shape
from shapely.geometry import shape, mapping
from sqlalchemy.orm import Session
from typing import List
import json
import base64
import epdb
from fastapi.responses import FileResponse

from ..env_utils import is_docker, config_env
from ..db import db_models
from ..db.postgis_utils import geometry_to_geojson, get_centroid
from ..models.enums import TaskStatus, TaskAction, get_action_for_status_change, verify_valid_status_update
from ..users import user_crud, user_schemas
from ..tasks import tasks_schemas
from ..central import central_schemas
from ..odkconvert.OdkCentral import OdkProject, OdkAppUser, OdkForm


from ..env_utils import is_docker, config_env

# FIXME: I am not sure this is thread-safe
project = OdkProject()
project.listProjects()
xform = OdkForm()

url = config_env["ODK_CENTRAL_URL"]
user = config_env["ODK_CENTRAL_USER"]
pw = config_env["ODK_CENTRAL_PASSWD"]
project.authenticate(url, user, pw)

def create_odk_project(name):
    result = project.createProject(name)
    project.id = result['id']
    logger.info(f"Project {name} has been created on the ODK Central server.")
    return result

def delete_odk_project(project_id: int):
    result = project.deleteProject(project_id)
    logger.info(f"Project {project_id} has been from the ODK Central server.")
    return result

def create_app_user(project_id: int, name: str):
    project.listAppUsers(project_id)
    user = project.findAppUser(name)
    if not user:
        appuser = OdkAppUser()
        result = appuser.create(user)
    return result

def delete_app_user(project_id: int, name: str):
    epdb.st()
