#!/usr/bin/env python

"""Warn users and delete inactive accounts.

Runs on a schedule once per week Sunday 00:00

- Warning: 21, 14, 7 days before deletion.
- Deletion: 2yrs of inactivity.
"""

import asyncio
import logging

from psycopg import AsyncConnection

from app.config import settings
from app.users.user_crud import process_inactive_users

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def scheduled_process_inactive_users():
    """Process inactive users."""
    try:
        async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
            log.info("Starting processing inactive users")
            await process_inactive_users(db)
            log.info("Finished processing inactive users")
    except Exception as e:
        log.error(f"Error during processing: {e}")


if __name__ == "__main__":
    asyncio.run(scheduled_process_inactive_users())
