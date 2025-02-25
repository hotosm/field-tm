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

"""ODK Central dependency wrappers."""

from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from fastapi.exceptions import HTTPException
from osm_fieldwork.OdkCentralAsync import OdkDataset, OdkForm

from app.central.central_schemas import ODKCentralDecrypted
from app.db.enums import HTTPStatus


@asynccontextmanager
async def get_odk_dataset(odk_creds: ODKCentralDecrypted):
    """Wrap getting an OdkDataset object with ConnectionError handling."""
    try:
        async with OdkDataset(
            url=odk_creds.odk_central_url,
            user=odk_creds.odk_central_user,
            passwd=odk_creds.odk_central_password,
        ) as odk_central:
            yield odk_central
    except ConnectionError as conn_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str(conn_error)
        ) from conn_error


@asynccontextmanager
async def get_async_odk_form(odk_creds: ODKCentralDecrypted):
    """Wrap getting an OdkDataset object with ConnectionError handling."""
    try:
        async with OdkForm(
            url=odk_creds.odk_central_url,
            user=odk_creds.odk_central_user,
            passwd=odk_creds.odk_central_password,
        ) as odk_central:
            yield odk_central
    except ConnectionError as conn_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str(conn_error)
        ) from conn_error


async def validate_xlsform_extension(xlsform: UploadFile):
    """Validate an XLSForm has .xls or .xlsx extension."""
    filename = Path(xlsform.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".xls", ".xlsx"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Provide a valid .xls or .xlsx file",
        )
    return BytesIO(await xlsform.read())


async def read_xlsform(xlsform: UploadFile) -> BytesIO:
    """Read an XLSForm, validate extension, return wrapped in BytesIO."""
    return await validate_xlsform_extension(xlsform)
