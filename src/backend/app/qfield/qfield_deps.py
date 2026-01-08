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
    """Login to QFieldCloud using session token."""
    if creds:
        qfc_url = creds.qfield_cloud_url
        qfc_user = creds.qfield_cloud_user
        qfc_password = creds.qfield_cloud_password
    else:
        qfc_url = settings.QFIELDCLOUD_URL
        qfc_user = settings.QFIELDCLOUD_USER
        qfc_password = settings.QFIELDCLOUD_PASSWORD.get_secret_value()
    loop = get_running_loop()
    client = await loop.run_in_executor(
        None,
        partial(Client, url=qfc_url),
    )

    try:
        # First generate a token in the client object state
        await loop.run_in_executor(
            None,
            partial(client.login, qfc_user, qfc_password),
        )

        if not client.token:
            msg = "QFieldCloud login failed. No token set."
            log.exception(msg)
            raise ValueError(msg)

        # Return a client with token explicitly set
        yield await loop.run_in_executor(
            None,
            partial(Client, url=qfc_url, token=client.token),
        )

    finally:
        try:
            await loop.run_in_executor(None, client.logout)
        except Exception as e:
            # Log but don’t suppress main exception
            log.warning(f"Failed to logout QFieldCloud client: {e}")
