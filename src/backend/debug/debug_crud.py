# Copyright (c) 2022 Humanitarian OpenStreetMap Team
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
from geoalchemy2.shape import to_shape
from shapely.geometry import shape, mapping
from sqlalchemy.orm import Session
from typing import List
import json
import base64

from ..db import db_models
from ..db.postgis_utils import geometry_to_geojson, get_centroid
from ..models.enums import TaskStatus, TaskAction, get_action_for_status_change, verify_valid_status_update
from ..users import user_crud, user_schemas
from ..tasks import tasks_schemas


