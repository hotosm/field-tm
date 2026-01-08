# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Schemas for HTMX form submissions."""

from typing import Optional

from litestar.datastructures import UploadFile
from pydantic import BaseModel, ConfigDict


class XLSFormUploadData(BaseModel):
    """Schema for XLSForm upload via HTMX multipart form."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    xlsform: Optional[UploadFile] = None
    need_verification_fields: Optional[str] = "true"
    mandatory_photo_upload: Optional[str] = "false"
    use_odk_collect: Optional[str] = "false"
    default_language: Optional[str] = "english"
    template_form_id: Optional[str] = None
