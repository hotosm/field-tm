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

import logging
from typing import Union

import psycopg
from psycopg.types.json import Json
from shapely.geometry import Polygon

log = logging.getLogger(__name__)


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


def aoi_to_postgis(conn: psycopg.Connection, geom: Polygon) -> None:
    """Export a GeoDataFrame to the project_aoi table in PostGIS.

    Uses a new cursor on existing connection, but not committed directly.

    Args:
        geom (Polygon): The shapely geom to insert.
        conn (psycopg.Connection): The PostgreSQL connection.

    Returns:
        None
    """
    log.debug("Adding AOI to project_aoi table")

    sql_insert = """
        INSERT INTO project_aoi (geom)
        VALUES (ST_SetSRID(CAST(%s AS GEOMETRY), 4326))
        RETURNING id, geom;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(sql_insert, (geom.wkb_hex,))
            cur.close()
    except Exception as e:
        log.error(f"Error during database operations: {e}")
        conn.rollback()  # Rollback in case of error


def insert_geom(cur: psycopg.Cursor, table_name: str, **kwargs) -> None:
    """Insert an OSM geometry into the database.

    Does not commit the values automatically.

    Args:
        cur (psycopg.Cursor): The PostgreSQL cursor.
        table_name (str): The name of the table to insert data into.
        **kwargs: Keyword arguments representing the values to be inserted.

    Returns:
        None
    """
    query = (
        f"INSERT INTO {table_name} (geom, osm_id, tags) "
        "VALUES (%(geom)s, %(osm_id)s, %(tags)s)"
    )
    if "tags" in kwargs:
        kwargs["tags"] = Json(kwargs["tags"])
    cur.execute(query, kwargs)
