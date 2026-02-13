#!/bin/python3

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

"""Class and helper methods for task splitting."""

import argparse
import asyncio
import json
import logging
import math
import sys
from pathlib import Path
from typing import Optional, Tuple, Union

import geojson
from geojson import Feature, FeatureCollection, GeoJSON
from osm_data_client import get_osm_data
from psycopg import Connection
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

from area_splitter import SplittingAlgorithm, algorithms_path
from area_splitter.db import (
    aoi_to_postgis,
    close_connection,
    create_connection,
    create_tables,
    drop_tables,
    insert_geom,
)

log = logging.getLogger(__name__)


def _fetch_extract_from_raw_data_api(aoi_geojson: FeatureCollection) -> dict:
    """Fetch an OSM extract from raw-data-api-py and return parsed GeoJSON."""

    async def _get_data() -> dict:
        result = await get_osm_data(
            aoi_geojson,
            fileName="area_splitter",
            outputType="geojson",
            bindZip=False,
            useStWithin=False,
            filters={
                "tags": {
                    "all_geometry": {
                        "building": [],
                        "highway": [],
                        "waterway": [],
                        "railway": [],
                        "aeroway": [],
                    }
                }
            },
        )
        with open(result.path, encoding="utf-8") as extract_file:
            return json.load(extract_file)

    return asyncio.run(_get_data())


class FMTMSplitter:
    """A class to split polygons."""

    def __init__(
        self,
        aoi_obj: Optional[Union[str, FeatureCollection, dict]] = None,
    ):
        """This class splits a polygon into tasks using a variety of algorithms.

        Args:
            aoi_obj (str, FeatureCollection): Input AOI, either a file path,
                or GeoJSON string.

        Returns:
            instance (FMTMSplitter): An instance of this class
        """
        # Parse AOI, merge if multiple geometries
        if aoi_obj:
            geojson = self.input_to_geojson(aoi_obj)
            self.aoi = self.geojson_to_shapely_polygon(geojson)

        # Init split features
        self.split_features = None

    @staticmethod
    def input_to_geojson(
        input_data: Union[str, FeatureCollection, dict], merge: bool = False
    ) -> GeoJSON:
        """Parse input data consistently to a GeoJSON obj."""
        log.info(f"Parsing GeoJSON from type {type(input_data)}")
        if (
            isinstance(input_data, str)
            and len(input_data) < 250
            and Path(input_data).is_file()
        ):
            # Impose restriction for path lengths <250 chars
            with open(input_data) as jsonfile:
                try:
                    parsed_geojson = geojson.load(jsonfile)
                except json.decoder.JSONDecodeError as e:
                    raise OSError(
                        f"File exists, but content is invalid JSON: {input_data}"
                    ) from e

        elif isinstance(input_data, FeatureCollection):
            parsed_geojson = input_data
        elif isinstance(input_data, dict):
            parsed_geojson = geojson.loads(geojson.dumps(input_data))
        elif isinstance(input_data, str):
            geojson_truncated = (
                input_data if len(input_data) < 250 else f"{input_data[:250]}..."
            )
            log.debug(f"GeoJSON string passed: {geojson_truncated}")
            parsed_geojson = geojson.loads(input_data)
        else:
            err = (
                f"The specified AOI is not valid (must be geojson or str): {input_data}"
            )
            log.error(err)
            raise ValueError(err)

        return parsed_geojson

    @staticmethod
    def geojson_to_featcol(
        geojson: Union[FeatureCollection, Feature, dict],
    ) -> FeatureCollection:
        """Standardise any geojson type to FeatureCollection."""
        # Parse and unparse geojson to extract type
        if isinstance(geojson, FeatureCollection):
            # Handle FeatureCollection nesting
            features = geojson.get("features", [])
        elif isinstance(geojson, Feature):
            # Must be a list
            features = [geojson]
        else:
            # A standard geometry type. Has coordinates, no properties
            features = [Feature(geometry=geojson)]
        return FeatureCollection(features)

    @staticmethod
    def geojson_to_shapely_polygon(
        geojson: Union[FeatureCollection, Feature, dict],
    ) -> Polygon:
        """Parse GeoJSON and return shapely Polygon.

        The GeoJSON may be of type FeatureCollection, Feature, or Polygon,
        but should only contain one Polygon geometry in total.
        """
        features = FMTMSplitter.geojson_to_featcol(geojson).get("features", [])
        log.debug("Converting AOI to Shapely geometry")

        if len(features) == 0:
            msg = "The input AOI contains no geometries."
            log.error(msg)
            raise ValueError(msg)
        elif len(features) > 1:
            msg = "The input AOI cannot contain multiple geometries."
            log.error(msg)
            raise ValueError(msg)

        return shape(features[0].get("geometry"))

    def meters_to_degrees(
        self, meters: float, reference_lat: float
    ) -> Tuple[float, float]:
        """Converts meters to degrees at a given latitude.

        Using WGS84 ellipsoidal calculations.

        Args:
            meters (float): The distance in meters to convert.
            reference_lat (float): The latitude at which to ,
            perform the conversion (in degrees).

        Returns:
            Tuple[float, float]: Degree values for latitude and longitude.
        """
        # INFO:
        # The geodesic distance is the shortest distance on the surface
        # of an ellipsoidal model of the earth

        lat_rad = math.radians(reference_lat)

        # Using WGS84 parameters
        a = 6378137.0  # Semi-major axis in meters
        f = 1 / 298.257223563  # Flattening factor

        # Applying formula
        e2 = (2 * f) - (f**2)  # Eccentricity squared
        n = a / math.sqrt(
            1 - e2 * math.sin(lat_rad) ** 2
        )  # Radius of curvature in the prime vertical
        m = (
            a * (1 - e2) / (1 - e2 * math.sin(lat_rad) ** 2) ** (3 / 2)
        )  # Radius of curvature in the meridian

        lat_deg_change = meters / m  # Latitude change in degrees
        lon_deg_change = meters / (n * math.cos(lat_rad))  # Longitude change in degrees

        # Convert changes to degrees by dividing by radians to degrees
        lat_deg_change = math.degrees(lat_deg_change)
        lon_deg_change = math.degrees(lon_deg_change)

        return lat_deg_change, lon_deg_change

    def frange(self, start: float, stop: float, step: float):
        """Range function that works with floats."""
        x = start
        while x <= stop:
            yield x
            x += step

    def splitBySquare(  # noqa: N802
        self,
        meters: int,
        db: Union[str, Connection],
        extract_geojson: Optional[Union[dict, FeatureCollection]] = None,
    ) -> FeatureCollection:
        """Split the polygon into squares.

        Args:
            meters (int):  The size of each task square in meters.
            db (str, psycopg.Connection): The db url, format:
                postgresql://myusername:mypassword@myhost:5432/mydatabase
                OR an psycopg connection object object that is reused.
                Passing an connection object prevents requiring additional
                database connections to be spawned.
            extract_geojson (dict, FeatureCollection): an OSM extract geojson,
                containing building polygons, or linestrings.

        Returns:
            data (FeatureCollection): A multipolygon of all the task boundaries.
        """
        log.debug("Splitting the AOI by squares")

        xmin, ymin, xmax, ymax = self.aoi.bounds

        reference_lat = (ymin + ymax) / 2
        length_deg, width_deg = self.meters_to_degrees(meters, reference_lat)

        # Create grid columns and rows based on the AOI bounds
        cols = list(self.frange(xmin, xmax + width_deg, width_deg))
        rows = list(self.frange(ymin, ymax + length_deg, length_deg))

        # Get existing db engine, or create new one
        conn = create_connection(db)

        with conn.cursor() as cur:
            # Drop the table if it exists
            cur.execute("DROP TABLE IF EXISTS temp_polygons;")
            # Create temporary table
            cur.execute("""
                CREATE TEMP TABLE temp_polygons (
                    id SERIAL PRIMARY KEY,
                    geom GEOMETRY(GEOMETRY, 4326),
                    area DOUBLE PRECISION
                );
            """)

            extract_geoms = []
            if extract_geojson:
                features = (
                    extract_geojson.get("features", extract_geojson)
                    if isinstance(extract_geojson, dict)
                    else extract_geojson.features
                )
                extract_geoms = [shape(feature["geometry"]) for feature in features]

            # Generate grid polygons and clip them by AOI
            polygons = []
            for x in cols[:-1]:
                for y in rows[:-1]:
                    grid_polygon = box(x, y, x + width_deg, y + length_deg)
                    clipped_polygon = grid_polygon.intersection(self.aoi)

                    if clipped_polygon.is_empty:
                        continue

                    # Check intersection with extract geometries if available
                    if extract_geoms:
                        if any(
                            geom.centroid.within(clipped_polygon)
                            for geom in extract_geoms
                        ):
                            polygons.append((clipped_polygon.wkt, clipped_polygon.wkt))

                    else:
                        polygons.append((clipped_polygon.wkt, clipped_polygon.wkt))

            insert_query = """
                    INSERT INTO temp_polygons (geom, area)
                    SELECT ST_GeomFromText(%s, 4326),
                    ST_Area(ST_GeomFromText(%s, 4326)::geography)
                """

            if polygons:
                cur.executemany(insert_query, polygons)

            area_threshold = 0.35 * (meters**2)

            cur.execute(
                f"""
                DO $$
                DECLARE
                    small_polygon RECORD;
                    nearest_neighbor RECORD;
                BEGIN
                DROP TABLE IF EXISTS small_polygons;
                CREATE TEMP TABLE small_polygons As
                    SELECT id, geom, area
                    FROM temp_polygons
                    WHERE area < {area_threshold};
                FOR small_polygon IN SELECT * FROM small_polygons
                LOOP
                    FOR nearest_neighbor IN
                    SELECT
                        id,
                        lp.geom AS large_geom,
                        ST_LENGTH2D(
                        ST_INTERSECTION(small_polygon.geom, geom)
                    ) AS shared_bound
                    FROM temp_polygons lp
                    WHERE id NOT IN (SELECT id FROM small_polygons)
                    AND ST_Touches(small_polygon.geom, lp.geom)
                    AND ST_GEOMETRYTYPE(
                        ST_INTERSECTION(small_polygon.geom, geom)
                    ) != 'ST_Point'
                    ORDER BY shared_bound DESC
                    LIMIT 1
                    LOOP
                        UPDATE temp_polygons
                        SET geom = ST_UNION(small_polygon.geom, geom)
                        WHERE id = nearest_neighbor.id;

                        DELETE FROM temp_polygons WHERE id = small_polygon.id;
                        EXIT;
                    END LOOP;
                END LOOP;
                END $$;
            """
            )

            cur.execute(
                """
                SELECT
                JSONB_BUILD_OBJECT(
                    'type', 'FeatureCollection',
                    'features', JSONB_AGG(feature)
                )
                FROM(
                    SELECT JSONB_BUILD_OBJECT(
                        'type', 'Feature',
                        'properties', JSONB_BUILD_OBJECT('area', (t.area)),
                        'geometry', ST_ASGEOJSON(t.geom)::json
                    ) AS feature
                    FROM temp_polygons as t
                ) AS features;
                """
            )
            self.split_features = cur.fetchone()[0]
        return self.split_features

    def splitBySQL(  # noqa: N802
        self,
        db: Union[str, Connection],
        algorithm: SplittingAlgorithm = SplittingAlgorithm.AVG_BUILDING_SKELETON,
        algorithm_params: Optional[dict] = None,
        osm_extract: Optional[Union[dict, FeatureCollection]] = None,
    ) -> FeatureCollection:
        """Split the polygon by features in the database using an SQL query.

        Args:
            db (str, psycopg.Connection): The db url, format:
                postgresql://myusername:mypassword@myhost:5432/mydatabase
                OR an psycopg connection object object that is reused.
                Passing an connection object prevents requiring additional
                database connections to be spawned.
            algorithm (SplittingAlgorithm): The algorithm to use.
            algorithm_params (dict): Dictionary of parameters for the algorithm.
                For building-based algorithms, should include 'num_buildings'.
            osm_extract (dict, FeatureCollection): an OSM extract geojson,
                containing building polygons, or linestrings.

        Returns:
            data (FeatureCollection): A multipolygon of all the task boundaries.
        """
        # Validation
        # FIXME this wasn't made a required param to maintain backward compatibility,
        # but should probably be updated
        if not osm_extract:
            msg = (
                "To use the FMTM splitting algo, an OSM data extract must be passed "
                "via param `osm_extract` as a geojson dict or FeatureCollection."
            )
            log.error(msg)
            raise ValueError(msg)

        # Validate that algorithm SQL file exists
        # Get SQL file path from algorithm
        if not algorithm.sql_path:
            msg = f"Algorithm {algorithm} does not have an SQL file path"
            log.error(msg)
            raise ValueError(msg)

        # Validate required parameters for the algorithm
        params = algorithm_params or {}
        missing_params = [
            param for param in algorithm.required_params if param not in params
        ]
        if missing_params:
            msg = (
                f"Algorithm {algorithm.value} requires the following parameters: "
                f"{', '.join(algorithm.required_params)}. "
                f"Missing: {', '.join(missing_params)}"
            )
            log.error(msg)
            raise ValueError(msg)

        # Get existing db engine, or create new one
        conn = create_connection(db)

        # Generate db tables if not exist
        log.debug("Generating required temp tables")
        create_tables(conn)

        # Add aoi to project_aoi table
        aoi_to_postgis(conn, self.aoi)

        def json_str_to_dict(json_item: Union[str, dict]) -> dict:
            """Convert a JSON string to dict."""
            if isinstance(json_item, dict):
                return json_item
            if isinstance(json_item, str):
                try:
                    return json.loads(json_item)
                except json.JSONDecodeError:
                    msg = f"Error decoding key in GeoJSON: {json_item}"
                    log.error(msg)
                    # Set tags to empty, skip feature
                    return {}

        # Insert data extract into db, using same cursor
        log.debug("Inserting data extract into db")
        cur = conn.cursor()
        for feature in osm_extract["features"]:
            # NOTE must handle format generated from FMTMSplitter __init__
            wkb_element = shape(feature["geometry"]).wkb_hex
            properties = feature.get("properties", {})
            if "tags" in properties.keys():
                # Sometimes tags are placed under tags key
                tags = properties.get("tags", {})
            else:
                # Sometimes tags are directly in properties
                tags = properties

            # Handle nested 'tags' key if present
            tags = json_str_to_dict(tags).get("tags", json_str_to_dict(tags))
            osm_id = properties.get("osm_id")

            # Common attributes for db tables
            common_args = dict(osm_id=osm_id, geom=wkb_element, tags=tags)

            # Insert building polygons
            # FIXME suggestion by @amitdkhan-pg
            # if "building" in tags:
            if tags.get("building") == "yes":
                insert_geom(cur, "ways_poly", **common_args)

            # Insert highway/waterway/railway polylines
            elif any(key in tags for key in ["highway", "waterway", "railway"]):
                insert_geom(cur, "ways_line", **common_args)

        # Use raw sql for view generation & remainder of script
        log.debug("Creating db view with intersecting polylines")
        cur.execute("""
            DROP VIEW IF EXISTS lines_view;

            CREATE VIEW lines_view AS
            SELECT w.tags, w.geom
            FROM ways_line w
            CROSS JOIN (SELECT geom FROM project_aoi LIMIT 1) p
            WHERE ST_Intersects(p.geom, w.geom)
        """)
        # Close current cursor
        cur.close()

        splitter_cursor = conn.cursor()
        log.debug("Collecting task splitting algorithm")

        sql_files = [
            "common/1-linear-features.sql",
            "common/2-group-buildings.sql",
            "common/3-cluster-buildings.sql",
            algorithm.sql_path,
            "common/5-alignment.sql",
            "common/6-extract.sql",
        ]

        log.info(f"Running task splitting algorithm parts in order: {sql_files}")

        for sql_file in sql_files:
            # Handle both Path objects and string paths
            if isinstance(sql_file, Path):
                sql_file_path = sql_file
            else:
                sql_file_path = algorithms_path / sql_file

            with open(sql_file_path) as raw_sql:
                query = raw_sql.read()
                # Replace all parameter placeholders in the SQL
                # Format: %(param_name)s
                sql_content = query
                for param_name, param_value in params.items():
                    placeholder = f"%({param_name})s"
                    sql_content = sql_content.replace(placeholder, str(param_value))
                splitter_cursor.execute(sql_content)

        features = splitter_cursor.fetchall()[0][0]["features"]
        if features:
            log.info(f"Query returned {len(features)} features")
        else:
            log.info("Query returned no features")

        self.split_features = FeatureCollection(features)

        # Drop tables & close (+commit) db connection
        drop_tables(conn)
        close_connection(conn)

        return self.split_features

    def splitByFeature(  # noqa: N802
        self,
        features: FeatureCollection,
    ) -> FeatureCollection:
        """Split the polygon by features in the database.

        Args:
            features(FeatureCollection): FeatureCollection of features
                to polygonise and return.

        Returns:
            data (FeatureCollection): A multipolygon of all the task boundaries.
        """
        log.debug("Polygonising the FeatureCollection features")
        # Extract all geometries from the input features
        geometries = []
        for feature in features["features"]:
            geom = feature["geometry"]
            if geom["type"] == "Polygon":
                geometries.append(shape(geom))
            elif geom["type"] == "LineString":
                geometries.append(shape(geom))
            else:
                log.warning(f"Ignoring unsupported geometry type: {geom['type']}")

        # Create a single MultiPolygon from all the polygons and linestrings
        multi_polygon = unary_union(geometries)

        # Clip the multi_polygon by the AOI boundary
        clipped_multi_polygon = multi_polygon.intersection(self.aoi)

        polygon_features = [
            Feature(geometry=polygon) for polygon in list(clipped_multi_polygon.geoms)
        ]

        # Convert the Polygon Features into a FeatureCollection
        self.split_features = FeatureCollection(features=polygon_features)

        return self.split_features

    def outputGeojson(  # noqa: N802
        self,
        filename: str = "output.geojson",
    ) -> None:
        """Output a geojson file from split features."""
        if not self.split_features:
            msg = "Feature splitting has not been executed. Do this first."
            log.error(msg)
            raise RuntimeError(msg)

        with open(filename, "w") as jsonfile:
            geojson.dump(self.split_features, jsonfile)
            log.debug(f"Wrote split features to {filename}")


def split_by_square(
    aoi: Union[str, FeatureCollection],
    db: Union[str, Connection],
    meters: int = 100,
    osm_extract: Union[str, FeatureCollection] = None,
    outfile: Optional[str] = None,
) -> FeatureCollection:
    """Split an AOI by square, dividing into an even grid.

    Args:
        aoi(str, FeatureCollection): Input AOI, either a file path,
            GeoJSON string, or FeatureCollection object.
        db (str, psycopg.Connection): The db url, format:
            postgresql://myusername:mypassword@myhost:5432/mydatabase
            OR an psycopg connection object object that is reused.
            Passing an connection object prevents requiring additional
            database connections to be spawned.
        meters(str, optional): Specify the square size for the grid.
            Defaults to 100m grid.
        osm_extract (str, FeatureCollection): an OSM extract geojson,
            containing building polygons, or linestrings.
            Optional param, if not included an extract is generated for you.
            It is recommended to leave this param as default, unless you know
            what you are doing.
        outfile(str): Output to a GeoJSON file on disk.

    Returns:
        features (FeatureCollection): A multipolygon of all the task boundaries.
    """
    # Parse AOI
    parsed_aoi = FMTMSplitter.input_to_geojson(aoi)
    aoi_featcol = FMTMSplitter.geojson_to_featcol(parsed_aoi)
    extract_geojson = None

    if osm_extract:
        extract_geojson = FMTMSplitter.input_to_geojson(osm_extract)

    # Handle multiple geometries passed
    if len(feat_array := aoi_featcol.get("features", [])) > 1:
        features = []
        for index, feat in enumerate(feat_array):
            featcol = split_by_square(
                FeatureCollection(features=[feat]),
                db,
                meters,
                None,
                f"{Path(outfile).stem}_{index}.geojson)" if outfile else None,
            )
            if feats := featcol.get("features", []):
                features += feats
        # Parse FeatCols into single FeatCol
        split_features = FeatureCollection(features)
    else:
        splitter = FMTMSplitter(aoi_featcol)
        split_features = splitter.splitBySquare(meters, db, extract_geojson)
        if not split_features:
            msg = "Failed to generate split features."
            log.error(msg)
            raise ValueError(msg)
        if outfile:
            splitter.outputGeojson(outfile)

    return split_features


def split_by_sql(
    aoi: Union[str, FeatureCollection],
    db: Union[str, Connection],
    num_buildings: Optional[int] = None,
    outfile: Optional[str] = None,
    osm_extract: Optional[Union[str, FeatureCollection]] = None,
    algorithm: Optional[SplittingAlgorithm] = None,
    algorithm_params: Optional[dict] = None,
) -> FeatureCollection:
    """Split an AOI with a field-tm algorithm.

    The query will optimise on the following:
    - Attempt to divide the aoi into tasks that contain approximately the
        number of buildings from `num_buildings` (or algorithm_params).
    - Split the task areas on major features such as roads an rivers, to
      avoid traversal of these features across task areas.

    Also has handling for multiple geometries within FeatureCollection object.

    Args:
        aoi(str, FeatureCollection): Input AOI, either a file path,
            GeoJSON string, or FeatureCollection object.
        db (str, psycopg.Connection): The db url, format:
            postgresql://myusername:mypassword@myhost:5432/mydatabase
            OR an psycopg connection object that is reused.
            Passing an connection object prevents requiring additional
            database connections to be spawned.
        num_buildings(int, optional): The number of buildings to optimise the FMTM
            splitting algorithm with (approx buildings per generated feature).
            Deprecated: Use algorithm_params instead. If algorithm_params is provided,
            this parameter is ignored.
        outfile(str): Output to a GeoJSON file on disk.
        osm_extract (str, FeatureCollection): an OSM extract geojson,
            containing building polygons, or linestrings.
            Optional param, if not included an extract is generated for you.
            It is recommended to leave this param as default, unless you know
            what you are doing.
        algorithm (SplittingAlgorithm, optional): The algorithm to use.
            Must be a building-based algorithm
            (AVG_BUILDING_VORONOI or AVG_BUILDING_SKELETON).
            Defaults to AVG_BUILDING_SKELETON.
        algorithm_params (dict, optional): Dictionary of parameters for the algorithm.
            Should include all parameters required by the algorithm
            (see algorithm.required_params).
            If not provided, will be constructed from num_buildings for backward
            compatibility.

    Returns:
        features (FeatureCollection): A multipolygon of all the task boundaries.
    """
    # Default algorithm if not provided
    if algorithm is None:
        algorithm = SplittingAlgorithm.AVG_BUILDING_SKELETON

    # Validate that algorithm has sql_path defined
    if not algorithm.sql_path:
        err = f"SplittingAlgorithm {algorithm} must have an sql_path defined."
        log.error(err)
        raise ValueError(err)

    # Prepare algorithm parameters
    # If algorithm_params is provided, use it; otherwise construct from
    # num_buildings for backward compatibility
    if algorithm_params is None:
        if not num_buildings:
            err = (
                f"Algorithm {algorithm.value} requires the following parameters: "
                f"{', '.join(algorithm.required_params)}. "
                f"Either provide algorithm_params dict or num_buildings (deprecated)."
            )
            log.error(err)
            raise ValueError(err)
        algorithm_params = {"num_buildings": num_buildings}

    # Validate required parameters for the algorithm
    missing_params = [
        param for param in algorithm.required_params if param not in algorithm_params
    ]
    if missing_params:
        err = (
            f"Algorithm {algorithm.value} requires the following parameters: "
            f"{', '.join(algorithm.required_params)}. "
            f"Missing: {', '.join(missing_params)}"
        )
        log.error(err)
        raise ValueError(err)

    # Parse AOI
    parsed_aoi = FMTMSplitter.input_to_geojson(aoi)
    aoi_featcol = FMTMSplitter.geojson_to_featcol(parsed_aoi)

    # Extracts and parse extract geojson
    if not osm_extract:
        extract_geojson = _fetch_extract_from_raw_data_api(aoi_featcol)

    else:
        extract_geojson = FMTMSplitter.input_to_geojson(osm_extract)

    if not extract_geojson:
        err = "A valid data extract must be provided."
        log.error(err)
        raise ValueError(err)

    # Handle multiple geometries passed
    if len(feat_array := aoi_featcol.get("features", [])) > 1:
        features = []
        for index, feat in enumerate(feat_array):
            featcol = split_by_sql(
                FeatureCollection(features=[feat]),
                db,
                num_buildings=algorithm_params.get("num_buildings")
                if "num_buildings" in algorithm_params
                else None,
                outfile=f"{Path(outfile).stem}_{index}.geojson)" if outfile else None,
                osm_extract=osm_extract,
                algorithm=algorithm,
                algorithm_params=algorithm_params,
            )
            feats = featcol.get("features", [])
            if feats:
                features += feats
        # Parse FeatCols into single FeatCol
        split_features = FeatureCollection(features)
    else:
        splitter = FMTMSplitter(aoi_featcol)
        split_features = splitter.splitBySQL(
            db, algorithm, algorithm_params, osm_extract=extract_geojson
        )
        if not split_features:
            msg = "Failed to generate split features."
            log.error(msg)
            raise ValueError(msg)
        if outfile:
            splitter.outputGeojson(outfile)

    return split_features


def split_by_features(
    aoi: Union[str, FeatureCollection],
    db_table: Optional[str] = None,
    geojson_input: Optional[Union[str, FeatureCollection]] = None,
    outfile: Optional[str] = None,
) -> FeatureCollection:
    """Split an AOI by geojson features or database features.

    Note: either db_table, or geojson_input must be passed.

    - By PG features: split by map features in a Postgres database table.
    - By GeoJSON features: split by map features from a GeoJSON file.

    Args:
        aoi(str, FeatureCollection): Input AOI, either a file path,
            GeoJSON string, or FeatureCollection object.
        geojson_input(str, FeatureCollection): Path to input GeoJSON file,
            a valid FeatureCollection, or GeoJSON string.
        db_table(str): A database table containing features to split by.
        outfile(str): Output to a GeoJSON file on disk.

    Returns:
        features (FeatureCollection): A multipolygon of all the task boundaries.

    """
    if not geojson_input and not db_table:
        err = "Either geojson_input or db_table must be passed."
        log.error(err)
        raise ValueError(err)

    # Parse AOI
    parsed_aoi = FMTMSplitter.input_to_geojson(aoi)
    aoi_featcol = FMTMSplitter.geojson_to_featcol(parsed_aoi)

    # Features from database
    if db_table:
        # data = f"PG:{db_table}"
        # TODO get input_features from db
        # input_features =
        # featcol = FMTMSplitter.geojson_to_featcol(input_features)
        raise NotImplementedError("Splitting from db features it not implemented yet.")

    # Features from geojson
    if geojson_input:
        input_parsed = FMTMSplitter.input_to_geojson(geojson_input)
        input_featcol = FMTMSplitter.geojson_to_featcol(input_parsed)

    if not isinstance(input_featcol, FeatureCollection):
        msg = (
            f"Could not parse geojson data from {geojson_input}"
            if geojson_input
            else f"Could not parse database data from {db_table}"
        )
        log.error(msg)
        raise ValueError(msg)

    # Handle multiple geometries passed
    if len(feat_array := aoi_featcol.get("features", [])) > 1:
        features = []
        for index, feat in enumerate(feat_array):
            featcol = split_by_features(
                FeatureCollection(features=[feat]),
                db_table,
                input_featcol,
                f"{Path(outfile).stem}_{index}.geojson)" if outfile else None,
            )
            feats = featcol.get("features", [])
            if feats:
                features += feats
        # Parse FeatCols into single FeatCol
        split_features = FeatureCollection(features)
    else:
        splitter = FMTMSplitter(aoi_featcol)
        split_features = splitter.splitByFeature(input_featcol)
        if not split_features:
            msg = "Failed to generate split features."
            log.error(msg)
            raise ValueError(msg)
        if outfile:
            splitter.outputGeojson(outfile)

    return split_features


def main(args_list: list[str] | None = None):
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(
        prog="splitter.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This program splits a Polygon AOI into tasks",
        epilog="""
This program splits a Polygon (the Area Of Interest)

        The data source for existing data can'
be either the data extract used by the XLSForm, or a postgresql database.

    examples:
        area-splitter -b AOI.geojson -o out.geojson --meters 100

        Where AOI is the boundary of the project as a polygon
        And OUTFILE is a MultiPolygon output file,which defaults to fmtm.geojson
        The task splitting defaults to squares, 50 meters across. If -m is used
        then that also defaults to square splitting.
        """,
    )
    # The default SQL query for feature splitting
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument(
        "-o", "--outfile", default="fmtm.geojson", help="Output file from splitting"
    )
    parser.add_argument(
        "-m",
        "--meters",
        nargs="?",
        const=50,
        type=int,
        help="Size in meters if using square splitting",
    )
    parser.add_argument(
        "-number", "--number", nargs="?", const=5, help="Number of buildings in a task"
    )
    parser.add_argument("-b", "--boundary", required=True, help="Polygon AOI")
    parser.add_argument("-s", "--source", help="Source data, Geojson or PG:[dbname]")
    parser.add_argument(
        "-db",
        "--dburl",
        default="postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
        help="The database url string",
    )
    parser.add_argument(
        "-e", "--extract", help="The OSM data extract for fmtm splitter"
    )

    # Accept command line args, or func params
    args = parser.parse_args(args_list)
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Set logger
    logging.basicConfig(
        level="DEBUG" if args.verbose else "INFO",
        format=(
            "%(asctime)s.%(msecs)03d [%(levelname)s] "
            "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
        ),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Parse AOI file or string
    if not args.boundary:
        err = "You need to specify an AOI! (file or geojson string)"
        log.error(err)
        raise ValueError(err)

    if args.meters:
        split_by_square(
            args.boundary,
            db=args.dburl,
            meters=args.meters,
            outfile=args.outfile,
            osm_extract=args.extract,
        )
    elif args.number:
        split_by_sql(
            args.boundary,
            db=args.dburl,
            num_buildings=args.number,
            outfile=args.outfile,
            osm_extract=args.extract,
        )
    # Split by feature using geojson
    elif args.source and args.source[3:] != "PG:":
        split_by_features(
            args.boundary,
            geojson_input=args.source,
            outfile=args.outfile,
        )
    # Split by feature using db
    elif args.source and args.source[3:] == "PG:":
        split_by_features(
            args.boundary,
            db_table=args.source[:3],
            outfile=args.outfile,
        )

    else:
        log.warning("Not enough arguments passed")
        parser.print_help()
        return


if __name__ == "__main__":
    """
    This is just a hook so this file can be run standalone during development.
    """
    main()
