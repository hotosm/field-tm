"""Populate total_tasks for old projects."""

import asyncio

from psycopg import AsyncConnection

from app.config import settings


async def populate_total_tasks():
    """Populate total_tasks for all projects where it's NULL or 0."""
    async with await AsyncConnection.connect(settings.FMTM_DB_URL) as db:
        async with db.cursor() as cur:
            sql = """
                UPDATE projects
                SET total_tasks = (
                    SELECT COALESCE(MAX(project_task_index), 0)
                    FROM public.tasks
                    WHERE projects.id = tasks.project_id
                )
                WHERE total_tasks IS NULL OR total_tasks = 0;
            """
            await cur.execute(sql)
            await db.commit()

    print("✅ Total tasks populated successfully")


if __name__ == "__main__":
    asyncio.run(populate_total_tasks())
