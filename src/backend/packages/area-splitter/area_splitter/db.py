# Copyright (c) 2025 Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

"""DB models for temporary tables in splitBySQL."""

import json
import logging
from typing import Union

import psycopg
from psycopg.types.json import Json

log = logging.getLogger(__name__)

# Kept ~30s below the production nginx ingress `proxy-read-timeout` (300s) so
# Postgres cancels the splitter SQL before the reverse proxy gives up. Keep
# this value strictly below the ingress timeout when retuning either side.
DEFAULT_STATEMENT_TIMEOUT_MS = 270_000


def create_connection(db: Union[str, psycopg.Connection]) -> psycopg.Connection:
    """Get db connection from existing psycopg connection, or URL string.

    Args:
        db (str, psycopg.Connection):
            string or existing db connection.
            If `db` is a string, a new connection is generated.
            If `db` is a psycopg connection, the connection is reused.

    Returns:
        conn: DBAPI connection object to generate cursors from.
    """
    if isinstance(db, psycopg.Connection):
        conn = db
    elif isinstance(db, str):
        conn = psycopg.connect(db)
    else:
        msg = "The `db` variable is not a valid string or psycopg connection."
        log.error(msg)
        raise ValueError(msg)

    return conn


def configure_statement_timeout(
    cur: psycopg.Cursor,
    timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
) -> None:
    """Apply a transaction-local PostgreSQL statement timeout.

    This keeps long-running split SQL from exceeding Field-TM's production
    reverse-proxy timeout and turning into an opaque 504 response.
    """
    if timeout_ms <= 0:
        return

    cur.execute("SELECT set_config('statement_timeout', %s, true)", (str(timeout_ms),))


def close_connection(conn: psycopg.Connection):
    """Close the db connection."""
    # Execute all commands in a transaction before closing
    try:
        conn.commit()
    except Exception as e:
        log.error(e)
        log.error("Error committing psycopg transaction to db")
    finally:
        conn.close()


def create_tables(conn: psycopg.Connection):
    """Create tables required for splitting.

    Uses a new cursor on existing connection, but not committed directly.
    """
    # First drop tables if they exist
    drop_tables(conn)

    create_cmd = """
        CREATE TABLE project_aoi (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            geom GEOMETRY(GEOMETRY, 4326)
        );

        CREATE TABLE ways_poly (
            id SERIAL PRIMARY KEY,
            osm_id VARCHAR NULL,
            geom GEOMETRY(GEOMETRY, 4326) NOT NULL,
            tags JSONB NULL
        );

        CREATE TABLE ways_line (
            id SERIAL PRIMARY KEY,
            osm_id VARCHAR NULL,
            geom GEOMETRY(GEOMETRY, 4326) NOT NULL,
            tags JSONB NULL
        );

        -- Create indexes for geospatial and query performance
        CREATE INDEX idx_project_aoi_geom ON project_aoi USING GIST(geom);
        CREATE INDEX idx_ways_poly_geom ON ways_poly USING GIST(geom);
        CREATE INDEX idx_ways_poly_tags ON ways_poly USING GIN(tags);
        CREATE INDEX idx_ways_line_geom ON ways_line USING GIST(geom);
        CREATE INDEX idx_ways_line_tags ON ways_line USING GIN(tags);
    """
    log.debug(
        "Running tables create command for 'project_aoi', 'ways_poly', 'ways_line'"
    )
    with conn.cursor() as cur:
        cur.execute(create_cmd)


def drop_tables(conn: psycopg.Connection):
    """Drop all tables used for splitting.

    Uses a new cursor on existing connection, but not committed directly.
    """
    log.debug("Running tables cleanup")
    with conn.cursor() as cur:
        cur.execute("DROP VIEW IF EXISTS lines_view;")
        cur.execute("DROP TABLE IF EXISTS buildings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS clusteredbuildings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS dumpedpoints CASCADE;")
        cur.execute("DROP TABLE IF EXISTS lowfeaturecountpolygons CASCADE;")
        cur.execute("DROP TABLE IF EXISTS voronois CASCADE;")
        cur.execute("DROP TABLE IF EXISTS taskpolygons CASCADE;")
        cur.execute("DROP TABLE IF EXISTS unsimplifiedtaskpolygons CASCADE;")
        cur.execute("DROP TABLE IF EXISTS splitpolygons CASCADE;")
        cur.execute("DROP TABLE IF EXISTS project_aoi CASCADE;")
        cur.execute("DROP TABLE IF EXISTS ways_poly CASCADE;")
        cur.execute("DROP TABLE IF EXISTS ways_line CASCADE;")


def aoi_to_postgis(conn: psycopg.Connection, geom: dict) -> None:
    """Export a GeoJSON geometry dict to the project_aoi table in PostGIS.

    Uses a new cursor on existing connection, but not committed directly.

    Args:
        geom (dict): The GeoJSON geometry dict to insert.
        conn (psycopg.Connection): The PostgreSQL connection.

    Returns:
        None
    """
    log.debug("Adding AOI to project_aoi table")

    sql_insert = """
        INSERT INTO project_aoi (geom)
        VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
        RETURNING id, geom;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(sql_insert, (json.dumps(geom),))
    except Exception as e:
        log.error(f"Error during database operations: {e}")
        conn.rollback()  # Rollback in case of error


_BATCH_INSERT_TABLES = frozenset({"ways_poly", "ways_line"})


def insert_geoms_batch(
    cur: psycopg.Cursor,
    table_name: str,
    rows: list[dict],
) -> None:
    """Batch-insert OSM geometries into one of the splitter temp tables.

    Uses ``executemany`` (which psycopg3 pipelines when supported) so an
    extract with thousands of features costs a single round-trip block
    instead of one per feature.

    Args:
        cur: PostgreSQL cursor.
        table_name: Target table, must be ``ways_poly`` or ``ways_line``.
        rows: List of dicts with keys ``osm_id``, ``geom`` (GeoJSON str),
            and ``tags`` (dict).
    """
    if not rows:
        return
    if table_name not in _BATCH_INSERT_TABLES:
        # Defense in depth: table name is interpolated into SQL, so guard
        # against drift even though all callers pass a hardcoded value.
        raise ValueError(f"Unsupported table for batch insert: {table_name}")

    query = (
        f"INSERT INTO {table_name} (geom, osm_id, tags) "
        "VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326), %(osm_id)s, %(tags)s)"
    )
    prepared = [{**row, "tags": Json(row.get("tags"))} for row in rows]
    cur.executemany(query, prepared)
