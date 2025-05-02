#!/usr/bin/env python

"""Unlock tasks with no recent activity.

Runs on a schedule every three hours.

- If latest event is ASSIGN, then unlock if it was three days ago.
- If latest event was MAP and there has been no progress,
  then unlock within an three hours.
"""

import asyncio
import logging

from psycopg import AsyncConnection

from app.config import settings
from app.tasks.task_crud import trigger_unlock_tasks

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def scheduled_unlock_inactive_tasks():
    """Process inactive tasks."""
    try:
        async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
            log.info("Starting processing inactive tasks")
            await trigger_unlock_tasks(db)
            log.info("Finished processing inactive tasks")
    except Exception as e:
        log.error(f"Error during processing: {e}")


if __name__ == "__main__":
    asyncio.run(scheduled_unlock_inactive_tasks())
