"""Upload submission data for active projectsto S3."""

import asyncio
import logging

from psycopg import AsyncConnection

from app.config import settings
from app.submissions.submission_crud import trigger_upload_submissions

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def upload_project_submissions_to_s3():
    """Upload submission data to S3."""
    try:
        async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
            log.info("Starting upload of submission data to S3")
            await trigger_upload_submissions(db)
            log.info("Finished uploading submission data to S3")
    except Exception as e:
        log.error(f"Error during upload: {e}")


if __name__ == "__main__":
    asyncio.run(upload_project_submissions_to_s3())
