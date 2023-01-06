# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

import enum
import datetime
from email.policy import default


class DisplayProject:
    id: int
    author_id: int
    created: datetime
    author_username: str
    description: str


class UITask:
    status: str
    feature_id: int
    name: str
    qr_code: str
    outline: str
    uid: int
    locked_by: int
    centroid: str
    centroid_lat: int
    centroid_long: int
