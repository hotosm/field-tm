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
from fastapi.logger import logger as logger


class DebugBase(BaseModel):
    pass


class Debug(DebugBase):
    geometry_geojson: str
    # qr_code_binary: bytes
    pass


class DebugOut(DebugBase):
    logger.debug("Hello World!")
    pass


class DebugDetails(DebugBase):
    logger.debug("Hello World!")
    pass
