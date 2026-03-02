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

"""ODK Central dependency wrappers."""

import json
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional
from urllib.parse import urlparse

from litestar import status_codes as status
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException
from osm_fieldwork.OdkCentralAsync import OdkDataset, OdkForm, OdkProject
from pyodk.client import Client

from app.central.central_schemas import ODKCentral
from app.config import settings


def _resolve_backend_odk_url(url: str) -> str:
    """Prefer the internal ODK URL for local public hostnames.

    In local Docker-based development, the backend cannot resolve public
    `*.localhost` hostnames used by the browser / proxy. In that case we keep
    the public URL for links and QR payloads, but route backend API calls
    through the internal service URL configured in `ODK_CENTRAL_URL`.
    """
    internal_url = str(settings.ODK_CENTRAL_URL or "")
    if not url or not internal_url:
        return url

    public_host = (urlparse(url).hostname or "").lower()
    internal_host = (urlparse(internal_url).hostname or "").lower()
    if not public_host or not internal_host or public_host == internal_host:
        return url

    if public_host == "localhost" or public_host.endswith(".localhost"):
        return internal_url

    return url


def _resolve_odk_creds(odk_creds: Optional[ODKCentral]) -> ODKCentral:
    """Resolve ODK credentials.

    The codebase often passes None to indicate "use env vars". Central client
    constructors require concrete credentials, so we materialize them here.
    """
    if odk_creds:
        backend_url = _resolve_backend_odk_url(
            str(odk_creds.external_project_instance_url or "")
        )
        if backend_url == odk_creds.external_project_instance_url:
            return odk_creds
        return ODKCentral(
            external_project_instance_url=backend_url,
            external_project_username=odk_creds.external_project_username,
            external_project_password=odk_creds.external_project_password,
        )

    return ODKCentral(
        external_project_instance_url=str(settings.ODK_CENTRAL_URL or ""),
        external_project_username=str(settings.ODK_CENTRAL_USER or ""),
        external_project_password=(
            settings.ODK_CENTRAL_PASSWD.get_secret_value()
            if settings.ODK_CENTRAL_PASSWD
            else ""
        ),
    )


def _strip_api_version(url: str) -> str:
    """Strip trailing /v1 or /v1/ from a URL.

    PyODK's Session.base_url_validate always appends /v1/, so we must
    ensure the base_url we provide does not already contain it.
    Without this, URLs like http://central:8383/v1 become
    http://central:8383/v1/v1/ causing 404 errors.
    """
    url = url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    return url


@asynccontextmanager
async def pyodk_client(odk_creds: Optional[ODKCentral]):
    """Async-compatible context manager for pyodk.Client.

    Offloads blocking Client(...) and client.__exit__ to a separate thread,
    and avoids blocking the async event loop in the endpoint.
    """
    creds = _resolve_odk_creds(odk_creds)
    base_url = _strip_api_version(creds.external_project_instance_url or "")

    with NamedTemporaryFile(mode="w", suffix=".toml", encoding="utf-8") as cfg:
        cfg.write("[central]\n")
        cfg.write(f"base_url = {json.dumps(base_url)}\n")
        cfg.write(f"username = {json.dumps(creds.external_project_username)}\n")
        cfg.write(f"password = {json.dumps(creds.external_project_password)}\n")
        cfg.flush()

        loop = get_running_loop()
        client = await loop.run_in_executor(
            None,
            lambda: Client(config_path=cfg.name).open(),
        )

        try:
            yield client
        finally:
            await loop.run_in_executor(None, client.close, None, None, None)


@asynccontextmanager
async def get_odk_dataset(odk_creds: Optional[ODKCentral]):
    """Wrap getting an OdkDataset object with ConnectionError handling."""
    creds = _resolve_odk_creds(odk_creds)
    try:
        async with OdkDataset(
            url=creds.external_project_instance_url,
            user=creds.external_project_username,
            passwd=creds.external_project_password,
        ) as odk_central:
            yield odk_central
    except ConnectionError as conn_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(conn_error),
        ) from conn_error


@asynccontextmanager
async def get_odk_project(odk_creds: Optional[ODKCentral]):
    """Wrap getting an OdkProject object with ConnectionError handling."""
    creds = _resolve_odk_creds(odk_creds)
    try:
        async with OdkProject(
            url=creds.external_project_instance_url,
            user=creds.external_project_username,
            passwd=creds.external_project_password,
        ) as odk_central:
            yield odk_central
    except ConnectionError as conn_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(conn_error),
        ) from conn_error


@asynccontextmanager
async def get_async_odk_form(odk_creds: Optional[ODKCentral]):
    """Wrap getting an OdkDataset object with ConnectionError handling."""
    creds = _resolve_odk_creds(odk_creds)
    try:
        async with OdkForm(
            url=creds.external_project_instance_url,
            user=creds.external_project_username,
            passwd=creds.external_project_password,
        ) as odk_central:
            yield odk_central
    except ConnectionError as conn_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(conn_error),
        ) from conn_error


async def validate_xlsform_extension(xlsform: UploadFile):
    """Validate an XLSForm has .xls or .xlsx extension."""
    filename = Path(xlsform.filename)
    file_ext = filename.suffix.lower()

    allowed_extensions = [".xls", ".xlsx"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide a valid .xls or .xlsx file",
        )
    return BytesIO(await xlsform.read())


async def read_xlsform(xlsform: UploadFile) -> BytesIO:
    """Read an XLSForm, validate extension, return wrapped in BytesIO."""
    return await validate_xlsform_extension(xlsform)


async def read_form_media(
    media_uploads: list[UploadFile],
) -> Optional[dict[str, BytesIO]]:
    """Read all uploaded form media for upload to ODK Central."""
    file_data_dict = {
        file.filename: BytesIO(await file.read()) for file in media_uploads
    }
    return file_data_dict
