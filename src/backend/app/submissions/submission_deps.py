# Copyright (c) Humanitarian OpenStreetMap Team
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

"""Submission dependency wrappers."""

from io import BytesIO
from typing import Optional

from fastapi import UploadFile


async def read_submission_uploads(
    submission_files: Optional[list[UploadFile]] = None,
) -> Optional[dict[str, BytesIO]]:
    """Read all uploaded submission attachments for upload to ODK Central."""
    if not submission_files:
        return None

    file_data_dict = {
        file.filename: BytesIO(await file.read()) for file in submission_files
    }
    return file_data_dict
