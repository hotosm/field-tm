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

from qfieldcloud_sdk.sdk import Client

from app.config import settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def qfield_client():
    """Login to QFieldCloud using session token."""
    if not settings.QFIELDCLOUD_TOKEN:
        log.error("QFieldCloud is not logged in")

    loop = get_running_loop()
    client = await loop.run_in_executor(
        None,
        partial(Client, url=settings.QFIELDCLOUD_URL, token=settings.QFIELDCLOUD_TOKEN),
    )

    try:
        # FIXME add logic to renew token if invalid when tested
        yield client
    finally:
        await loop.run_in_executor(None, client.logout)
