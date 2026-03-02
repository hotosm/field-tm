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

"""QFieldCloud dependency wrappers."""

import logging
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from functools import partial
from typing import Optional

from qfieldcloud_sdk.sdk import Client

from app.config import settings
from app.qfield.qfield_schemas import QFieldCloud

log = logging.getLogger(__name__)


@asynccontextmanager
async def qfield_client(creds: Optional[QFieldCloud] = None):
    """Async context manager that yields an authenticated QFieldCloud SDK Client.

    The SDK ``Client`` exposes *synchronous* methods, so callers must wrap them
    with ``loop.run_in_executor(…)`` when calling from async code.

    The yielded client has a ``username`` attribute set for downstream use.
    """
    if creds:
        qfc_url = creds.qfield_cloud_url
        qfc_user = creds.qfield_cloud_user
        qfc_password = creds.qfield_cloud_password
    else:
        qfc_url = settings.QFIELDCLOUD_URL
        qfc_user = settings.QFIELDCLOUD_USER
        qfc_password = (
            settings.QFIELDCLOUD_PASSWORD.get_secret_value()
            if settings.QFIELDCLOUD_PASSWORD
            else ""
        )

    if not all([qfc_url, qfc_user, qfc_password]):
        raise ValueError(
            "QFieldCloud credentials (URL, user, password) are not configured. "
            "Set QFIELDCLOUD_URL, QFIELDCLOUD_USER, and QFIELDCLOUD_PASSWORD, "
            "or provide custom credentials."
        )

    loop = get_running_loop()
    login_client = await loop.run_in_executor(
        None,
        partial(Client, url=qfc_url),
    )

    try:
        # Authenticate to obtain a session token
        await loop.run_in_executor(
            None,
            partial(login_client.login, qfc_user, qfc_password),
        )

        if not login_client.token:
            raise ValueError("QFieldCloud login failed: no token received.")

        # Build a fresh client with the token (avoids credential leakage)
        authed_client = await loop.run_in_executor(
            None,
            partial(Client, url=qfc_url, token=login_client.token),
        )
        # Attach the username so callers can resolve project ownership
        authed_client.username = qfc_user
        yield authed_client

    finally:
        try:
            await loop.run_in_executor(None, login_client.logout)
        except Exception as e:
            # Log but never suppress the main exception
            log.warning("Failed to logout QFieldCloud client: %s", e)
