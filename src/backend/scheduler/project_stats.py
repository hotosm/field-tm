#!/usr/bin/env python

"""Updates project data stats every 10 minutes."""

import asyncio
import sys

from psycopg import AsyncConnection

from app.config import settings
from app.db.postgis_utils import timestamp

DB_URL = settings.FMTM_DB_URL.unicode_string()

# Create materialized view to store project stats for faster query:
# Here we retrieve:
#  - Total number of contributors (task / entity events)
#  - Total number of complete submissions
#  - Total number of tasks mapped
#  - Total number of task validated as bad
#  - Total number of task validated as good
# Previously we did a big join of all data in the entire database. Now instead:
#  - Uses scalar subqueries, filtered by project_id = p.id (one row per project)
#  - All metrics are isolated subqueries, using indexes efficiently
#  - No big joins, no GROUP BY, no row explosions
#  - Each subquery uses narrow filters (WHERE project_id = p.id)
# NOTE as FieldTM scales and projects increase, we could swap the final
# NOTE    WHERE p.id IN (SELECT p FROM projects);
# NOTE to take a narrower range of IDs and do schedule partial updates to
# NOTE avoid refreshing all in one go.
# TODO performance of this takes ~15ms. Consider moving back to models.py logic.
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
        (
            SELECT COUNT(DISTINCT user_sub)
            FROM task_events
            WHERE project_id = p.id
        ) AS num_contributors,
        (
            SELECT COUNT(DISTINCT entity_id)
            FROM odk_entities
            WHERE project_id = p.id
            AND status = 'SURVEY_SUBMITTED'
        ) AS total_submissions,
        (
            SELECT COUNT(*)
            FROM latest_task_events
            WHERE project_id = p.id AND event = 'FINISH'
        ) AS tasks_mapped,
        (
            SELECT COUNT(*)
            FROM latest_task_events
            WHERE project_id = p.id AND event = 'BAD'
        ) AS tasks_bad,
        (
            SELECT COUNT(*)
            FROM latest_task_events
            WHERE project_id = p.id AND event = 'GOOD'
        ) AS tasks_validated
    FROM projects p;
    -- where p.id in (SELECT id FROM projects);
"""

CREATE_UNIQUE_INDEX_SQL = """
    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_project_stats
    ON mv_project_stats (project_id);
"""

REFRESH_MATERIALIZED_VIEW_SQL = """
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_stats;
"""


async def main():
    """Main function for cron execution."""
    try:
        async with await AsyncConnection.connect(DB_URL, autocommit=True) as db:
            async with db.cursor() as cur:
                # First ensure the view exists
                print(f"Creating materialized view for project stats: {timestamp()}")
                await cur.execute(CREATE_MATERIALIZED_VIEW_SQL)
                print(f"Materialized view created successfully: {timestamp()}")

                # Create the index
                print("Creating index for new materialized view")
                await cur.execute(CREATE_UNIQUE_INDEX_SQL)
                print("Unique index created successfully.")

                # Then refresh it (once)
                print(f"Refreshing materialized view once: {timestamp()}")
                await cur.execute(REFRESH_MATERIALIZED_VIEW_SQL)
                print(f"Materialized view refreshed successfully: {timestamp()}")

    except Exception as e:
        print(f"Error in project stats update: {e}")
        # Exit with non-zero status to indicate failure

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
