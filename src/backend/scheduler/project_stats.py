#!/usr/bin/env python

"""Updates project data stats every 10 minutes."""

import asyncio

from psycopg import AsyncConnection

from app.config import settings

DB_URL = settings.FMTM_DB_URL.unicode_string()

# create materialized view to store project stats faster faster query
CREATE_MATERIALIZED_VIEW_SQL = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_project_stats AS
    WITH latest_task_events AS (
        SELECT DISTINCT ON (ev.project_id, ev.task_id)
            ev.project_id,
            ev.task_id,
            ev.event_id,
            ev.event
        FROM task_events ev
        ORDER BY ev.project_id, ev.task_id, ev.created_at DESC
    )
    SELECT
        p.id AS project_id,
        COUNT(DISTINCT ev.user_sub) AS num_contributors,
        COUNT(
            DISTINCT CASE WHEN et.status = 'SURVEY_SUBMITTED'
            THEN et.entity_id END
        ) AS total_submissions,
        COUNT(
            DISTINCT CASE WHEN lte.event = 'FINISH'
            THEN lte.event_id END
        ) AS tasks_mapped,
        COUNT(
            DISTINCT CASE WHEN lte.event = 'BAD'
            THEN lte.event_id END
        ) AS tasks_bad,
        COUNT(
            DISTINCT CASE WHEN lte.event = 'GOOD'
            THEN lte.event_id END
        ) AS tasks_validated
    FROM projects p
    LEFT JOIN tasks t ON p.id = t.project_id
    LEFT JOIN task_events ev ON p.id = ev.project_id
    LEFT JOIN odk_entities et ON p.id = et.project_id
    LEFT JOIN latest_task_events lte ON p.id = lte.project_id
    GROUP BY p.id;
"""

REFRESH_MATERIALIZED_VIEW_SQL = """
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_stats;
"""
CREATE_UNIQUE_INDEX_SQL = """
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_project_stats
ON mv_project_stats (project_id);
"""


async def create_materialized_view():
    """Creates the materialized view."""
    async with await AsyncConnection.connect(DB_URL) as db:
        async with db.cursor() as cur:
            await cur.execute(CREATE_MATERIALIZED_VIEW_SQL)
            await db.commit()
            print("Materialized view created successfully.")

    # Run CREATE INDEX outside a transaction using autocommit
    async with await AsyncConnection.connect(DB_URL, autocommit=True) as db:
        async with db.cursor() as cur:
            await cur.execute(CREATE_UNIQUE_INDEX_SQL)
            print("Unique index created successfully.")


async def main():
    """Main function for cron execution."""
    try:
        # First ensure the view exists
        await create_materialized_view()

        # Then refresh it (once)
        async with await AsyncConnection.connect(DB_URL) as db:
            async with db.cursor() as cur:
                await cur.execute(REFRESH_MATERIALIZED_VIEW_SQL)
                await db.commit()
                print("Materialized view refreshed successfully.")

    except Exception as e:
        print(f"Error in project stats update: {e}")
        # Exit with non-zero status to indicate failure
        import sys

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
