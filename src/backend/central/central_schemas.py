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

from pydantic import BaseModel
from datetime import datetime
from geojson_pydantic import Feature, Point
from typing import List
import enum
import logging.config
from fastapi.logger import logger as logger
from enum import Enum


class CentralBase(BaseModel):
    central_url: str

class Central(CentralBase):
    geometry_geojson: str
    # qr_code_binary: bytes

class CentralOut(CentralBase):
    logger.debug("Hello World!")

class CentralFileType(BaseModel):
    filetype: Enum('FileType', ['xform', 'extract', 'zip', 'xlsform', 'all'])
    logger.debug("Hello World!")

class CentralDetails(CentralBase):
    logger.debug("Hello World!")
