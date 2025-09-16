#!/usr/bin/env python

"""Refresh user submission counts every day."""

import asyncio
import logging

from psycopg import AsyncConnection

from app.config import settings
from app.users.user_crud import calculate_submission_stats, update_submission_counts

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def refresh_user_submission_count():
    """Refresh user submission counts."""
    try:
        async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
            log.info("Starting refreshing user submission counts")
            await update_submission_counts(db)
            await calculate_submission_stats(db)
            log.info("Finished refreshing user submission counts")
    except Exception as e:
        log.error(f"Error during processing: {e}")


if __name__ == "__main__":
    asyncio.run(refresh_user_submission_count())
