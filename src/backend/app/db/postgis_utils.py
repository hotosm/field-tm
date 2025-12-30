# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""PostGIS and geometry handling helper funcs."""

import json
import logging
from datetime import datetime, timezone
from random import getrandbits
from typing import Optional, Union

import geojson
import geojson_pydantic
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from osm_data_client import RawDataOutputOptions, get_osm_data
from osm_fieldwork.data_models import data_models_path
from psycopg import AsyncConnection, ProgrammingError
from psycopg.rows import class_row, dict_row
from psycopg.types.json import Json
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.db.enums import DbGeomType, XLSFormType

log = logging.getLogger(__name__)


def timestamp():
    """Get the current time.

    Used to insert a current timestamp into Pydantic models.
    """
    return datetime.now(timezone.utc)


async def polygon_to_centroid(
    polygon: geojson.Polygon,
) -> Point:
    """Convert GeoJSON to shapely geometry."""
    return shape(polygon).centroid


async def featcol_to_flatgeobuf(
    db: AsyncConnection, geojson: geojson.FeatureCollection
) -> Optional[bytes]:
    """From a given FeatureCollection, return a memory flatgeobuf obj.

    NOTE this generate an fgb with string timestamps, not datetime.
    NOTE ogr2ogr would generate datetime, but parsing does not seem to work.

    Args:
        db (Connection): Database connection.
        geojson (geojson.FeatureCollection): a FeatureCollection object.

    Returns:
        flatgeobuf (bytes): a Python bytes representation of a flatgeobuf file.
    """
    geojson_with_props = add_required_geojson_properties(geojson)

    async with db.cursor() as cur:
        await cur.execute("""
            DROP TABLE IF EXISTS temp_features CASCADE;
        """)

        await cur.execute("""
            -- Wrap geometries in GeometryCollection
            CREATE TEMP TABLE IF NOT EXISTS temp_features(
                geom geometry(GeometryCollection, 4326),
                osm_id bigint,
                tags text,
                version integer,
                changeset integer,
                timestamp text
            );
        """)

        await cur.execute(
            """
            WITH data AS (SELECT CAST(%(geojson)s AS json) AS fc)
            INSERT INTO temp_features
                (geom, osm_id, tags, version, changeset, timestamp)
            SELECT
                ST_ForceCollection(ST_GeomFromGeoJSON(feat->>'geometry')) AS geom,
                regexp_replace(
                    (feat->'properties'->>'osm_id')::text, '[^0-9]', '', 'g'
                )::BIGINT as osm_id,
                (feat->'properties'->>'tags')::text as tags,
                (feat->'properties'->>'version')::integer as version,
                (feat->'properties'->>'changeset')::integer as changeset,
                (feat->'properties'->>'timestamp')::text as timestamp
            FROM json_array_elements((SELECT fc->'features' FROM data)) AS f(feat);
        """,
            {"geojson": json.dumps(geojson_with_props)},
        )

        await cur.execute("""
            -- Second param = generate with spatial index
            SELECT ST_AsFlatGeobuf(geoms, true)
            FROM (SELECT * FROM temp_features) AS geoms;
        """)
        # Get a memoryview object, then extract to Bytes
        flatgeobuf = await cur.fetchone()

    if flatgeobuf:
        return flatgeobuf[0]

    # Nothing returned (either no features passed, or failed)
    return None


async def flatgeobuf_to_featcol(
    db: AsyncConnection, flatgeobuf: bytes
) -> Optional[geojson.FeatureCollection]:
    """Converts FlatGeobuf data to GeoJSON.

    Extracts single geometries from wrapped GeometryCollection if used.

    Args:
        db (Connection): Database connection.
        flatgeobuf (bytes): FlatGeobuf data in bytes format.

    Returns:
        geojson.FeatureCollection: A FeatureCollection object.
    """
    try:
        async with db.cursor() as cur:
            await cur.execute("""
                DROP TABLE IF EXISTS public.temp_fgb CASCADE;
            """)

            await cur.execute(
                """
                SELECT ST_FromFlatGeobufToTable('public', 'temp_fgb', %(fgb_bytes)s);
            """,
                {"fgb_bytes": flatgeobuf},
            )

            # Set row_factory to parse geojson
            cur.row_factory = class_row(geojson_pydantic.FeatureCollection)
            await cur.execute(
                """
                WITH feature_data AS MATERIALIZED (
                    SELECT
                        geom,
                        osm_id,
                        tags,
                        version,
                        changeset,
                        timestamp
                    FROM ST_FromFlatGeobuf(null::temp_fgb, %(fgb_bytes)s)
                ),
                processed_features AS MATERIALIZED (
                    SELECT jsonb_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(ST_GeometryN(geom, 1))::jsonb,
                        'id', osm_id::VARCHAR,
                        'properties', jsonb_build_object(
                            'osm_id', osm_id,
                            'tags', tags,
                            'version', version,
                            'changeset', changeset,
                            'timestamp', timestamp
                        )
                    ) AS feature
                    FROM feature_data
                )
                SELECT
                    'FeatureCollection' as type,
                    COALESCE(jsonb_agg(feature), '[]'::jsonb) AS features
                FROM processed_features;
            """,
                {"fgb_bytes": flatgeobuf},
            )
            featcol = await cur.fetchone()

            await cur.execute("""
                DROP TABLE IF EXISTS public.temp_fgb CASCADE;
            """)
    except ProgrammingError as e:
        log.error(e)
        log.error(
            "Attempted flatgeobuf --> geojson conversion failed. "
            "Perhaps there is a duplicate 'id' column?"
        )
        return None

    return geojson.loads(featcol.model_dump_json()) if featcol else None


async def split_geojson_by_task_areas(
    db: AsyncConnection,
    featcol: geojson.FeatureCollection,
    project_id: int,
    geom_type: DbGeomType = DbGeomType.POLYGON,
) -> Optional[dict[int, geojson.FeatureCollection]]:
    """Split GeoJSON into tagged task area GeoJSONs.

    NOTE batch inserts feature.properties.osm_id as feature.id for each feature.
    NOTE ST_Within used on polygon centroids and ST_Intersects used on linear features
    to correctly capture the geoms per task.

    Args:
        db (Connection): Database connection.
        featcol (geojson.FeatureCollection): Data extract feature collection.
        project_id (int): The project ID for associated tasks.
        geom_type (str): The geometry type of the features.

    Returns:
        dict[int, geojson.FeatureCollection]: {task_id: FeatureCollection} mapping.
    """
    try:
        features = featcol["features"]
        use_st_intersects = geom_type == "POLYLINE"

        feature_ids = []
        feature_properties = []
        feature_geometries = []
        result_dict = {}
        for f in features:
            feature_ids.append(str(f["properties"].get("osm_id")))
            feature_properties.append(Json(f["properties"]))
            feature_geometries.append(json.dumps(f["geometry"]))

        # Choose spatial join logic based on geometry type
        spatial_join_condition = (
            "ST_Intersects(f.geom, t.outline)"
            if use_st_intersects
            else "ST_Within(ST_Centroid(f.geom), t.outline)"
        )

        async with db.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"""
                WITH feature_data AS (
                    SELECT DISTINCT ON (geom)
                        unnest(%s::TEXT[]) AS id,
                        unnest(%s::JSONB[]) AS properties,
                        ST_SetSRID(ST_GeomFromGeoJSON(unnest(%s::TEXT[])), 4326) AS geom
                ),
                task_features AS (
                    SELECT
                        t.project_task_index AS task_id,
                        jsonb_build_object(
                            'type', 'Feature',
                            'id', f.id,
                            'geometry', ST_AsGeoJSON(f.geom)::jsonb,
                            'properties', jsonb_set(
                                jsonb_set(
                                    f.properties,
                                    '{{task_id}}',
                                    to_jsonb(t.project_task_index)
                                ),
                                '{{project_id}}', to_jsonb(%s)
                            )
                        ) AS feature
                    FROM tasks t
                    JOIN feature_data f
                    ON {spatial_join_condition}
                    WHERE t.project_id = %s
                )
                SELECT
                    task_id,
                    jsonb_agg(feature) AS features
                FROM task_features
                GROUP BY task_id;
                """,
                (
                    feature_ids,
                    feature_properties,
                    feature_geometries,
                    project_id,
                    project_id,
                ),
            )

            # Convert results into GeoJSON FeatureCollection
            result_dict = {
                rec["task_id"]: geojson.FeatureCollection(features=rec["features"])
                for rec in await cur.fetchall()
            }
            if not result_dict:
                msg = f"Failed to split project ({project_id}) geojson by task areas."
                log.exception(msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=msg,
                )

            if len(result_dict) < 1:
                msg = (
                    f"Attempted splitting project ({project_id}) geojson by task areas,"
                    "but no data was returned."
                )
                log.warning(msg)
                return None
            return result_dict

    except ProgrammingError as e:
        log.error(e)
        log.error("Attempted geojson task splitting failed")
        return None


def add_required_geojson_properties(
    geojson: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Add required geojson properties if not present.

    This step is required prior to flatgeobuf generation,
    else the workflows of conversion between the formats will fail.
    """
    features = geojson.get("features", [])
    current_date = timestamp()

    for feature in features:
        properties = feature.get("properties", {})
        # Check for id type embedded in properties
        if feature_id := feature.get("id"):
            # osm_id property exists, set top level id
            properties["osm_id"] = feature_id
        else:
            osm_id = (
                properties.get(
                    "osm_id"
                )  # osm_id property takes priority (i.e. it's from OSM)
                or properties.get("id")
                or properties.get("fid")  # fid is typical from tools like QGIS
                # Random id
                # NOTE 32-bit int is max supported by standard postgres Integer
                # 0 to 1073741823 (collision chance is extremely low for ≤20k entities)
                or getrandbits(30)
            )

            if isinstance(osm_id, str) and "/" in osm_id:
                osm_id = osm_id.split("/")[0]

            # Ensure negative osm_id if it's derived
            # NOTE this is important to denote the geom is not from OSM
            if not properties.get("osm_id"):
                osm_id = -abs(int(osm_id))

            feature["id"] = str(osm_id)
            properties["osm_id"] = osm_id

        # Set default values efficiently
        properties.setdefault("tags", "")
        properties.setdefault("version", 1)
        properties.setdefault("changeset", 1)
        properties.setdefault("timestamp", str(current_date))
        properties.setdefault("created_by", "")

        feature["properties"] = properties

    return geojson


def normalise_featcol(featcol: geojson.FeatureCollection) -> geojson.FeatureCollection:
    """Normalise a FeatureCollection into a standardised format.

    The final FeatureCollection will only contain:
    - Polygon
    - LineString
    - Point

    Processed:
    - MultiPolygons will be divided out into individual polygons.
    - GeometryCollections wrappers will be stripped out.
    - Removes any z-dimension coordinates, e.g. [43, 32, 0.0]

    Args:
        featcol: A parsed FeatureCollection.

    Returns:
        geojson.FeatureCollection: A normalised FeatureCollection.
    """

    def strip_z_coord(coords):
        if isinstance(coords[0], (int, float)):  # single coordinate [x, y, z?]
            return coords[:2]  # drop z if present
        return [strip_z_coord(c) for c in coords]

    for feat in featcol.get("features", []):
        geom = feat.get("geometry")

        # Strip out GeometryCollection wrappers
        if (
            geom.get("type") == "GeometryCollection"
            and len(geom.get("geometries", [])) == 1
        ):
            feat["geometry"] = geom.get("geometries")[0]

        # Remove any z-dimension coordinates recursively, for any geom type
        coords = geom.get("coordinates")
        if coords is not None:
            geom["coordinates"] = strip_z_coord(coords)

    # Convert MultiPolygon type --> individual Polygons
    return multigeom_to_singlegeom(featcol)


def geojson_to_featcol(geojson_obj: dict) -> geojson.FeatureCollection:
    """Enforce GeoJSON is wrapped in FeatureCollection.

    The type check is done directly from the GeoJSON to allow parsing
    from different upstream libraries (e.g. geojson_pydantic).
    """
    # We do a dumps/loads cycle to strip any extra obj logic
    geojson_type = json.loads(json.dumps(geojson_obj)).get("type")

    if geojson_type == "FeatureCollection":
        log.debug("Already in FeatureCollection format, reparsing")
        features = geojson_obj.get("features")
    elif geojson_type == "Feature":
        log.debug("Converting Feature to FeatureCollection")
        features = [geojson_obj]
    else:
        log.debug("Converting Geometry to FeatureCollection")
        features = [geojson.Feature(geometry=geojson_obj)]

    featcol = geojson.FeatureCollection(features=features)

    return normalise_featcol(featcol)


def parse_geojson_file_to_featcol(
    geojson_raw: Union[str, bytes],
) -> Optional[geojson.FeatureCollection]:
    """Parse geojson string or file content to FeatureCollection."""
    geojson_parsed = geojson.loads(geojson_raw)
    featcol = geojson_to_featcol(geojson_parsed)
    # Exit early if no geoms
    if not featcol.get("features", []):
        return None
    return featcol


def featcol_keep_single_geom_type(
    featcol: geojson.FeatureCollection,
    geom_type: Optional[str] = None,
) -> geojson.FeatureCollection:
    """Strip out any geometries not matching the dominant geometry type."""
    features = featcol.get("features", [])

    if not geom_type:
        # Default to keep the predominant geometry type
        geom_type = get_featcol_dominant_geom_type(featcol)

    features_filtered = [
        feature
        for feature in features
        if feature.get("geometry", {}).get("type", "") == geom_type
    ]

    return geojson.FeatureCollection(features_filtered)


def get_featcol_dominant_geom_type(featcol: geojson.FeatureCollection) -> str:
    """Get the predominant geometry type in a FeatureCollection."""
    geometry_counts = {"Polygon": 0, "Point": 0, "LineString": 0}

    for feature in featcol.get("features", []):
        geometry_type = feature.get("geometry", {}).get("type", "")
        if geometry_type in geometry_counts:
            geometry_counts[geometry_type] += 1

    return max(geometry_counts, key=lambda key: geometry_counts[key])


async def check_crs(input_geojson: Union[dict, geojson.FeatureCollection]):
    """Validate CRS is valid for a geojson."""
    log.debug("validating coordinate reference system")

    def is_valid_crs(crs_name):
        valid_crs_list = [
            "urn:ogc:def:crs:OGC:1.3:CRS84",
            "urn:ogc:def:crs:EPSG::4326",
            "WGS 84",
        ]
        return crs_name in valid_crs_list

    def is_valid_coordinate(coord):
        if coord is None:
            return False
        return -180 <= coord[0] <= 180 and -90 <= coord[1] <= 90

    error_message = (
        "ERROR: Unsupported coordinate system, it is recommended to use a "
        "GeoJSON file in WGS84(EPSG 4326) standard."
    )
    if "crs" in input_geojson:
        crs = input_geojson.get("crs", {}).get("properties", {}).get("name")
        if not is_valid_crs(crs):
            log.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        return

    if (input_geojson_type := input_geojson.get("type")) == "FeatureCollection":
        features = input_geojson.get("features", [])
        coordinates = (
            features[-1].get("geometry", {}).get("coordinates", []) if features else []
        )
    elif input_geojson_type == "Feature":
        coordinates = input_geojson.get("geometry", {}).get("coordinates", [])
    else:
        coordinates = input_geojson.get("coordinates", {})

    first_coordinate = None
    if coordinates:
        while isinstance(coordinates, list):
            first_coordinate = coordinates
            coordinates = coordinates[0]

    error_message = (
        "ERROR: The coordinates within the GeoJSON file are not valid. "
        "Is the file empty?"
    )
    if not is_valid_coordinate(first_coordinate):
        log.error(error_message)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )


async def geojson_to_javarosa_geom(geojson_geometry: dict) -> str:
    """Convert a GeoJSON geometry to JavaRosa format string.

    This format is unique to ODK and the JavaRosa XForm processing library.
    Example JavaRosa polygon (semicolon separated):
    -8.38071535576881 115.640801902838 0.0 0.0;
    -8.38074220774489 115.640848633963 0.0 0.0;
    -8.38080128208577 115.640815355738 0.0 0.0;
    -8.38077407987063 115.640767444534 0.0 0.0;
    -8.38071535576881 115.640801902838 0.0 0.0

    Args:
        geojson_geometry (dict): The GeoJSON geometry.

    Returns:
        str: A string representing the geometry in JavaRosa format.
    """
    if geojson_geometry is None:
        return ""

    coordinates = geojson_geometry.get("coordinates", [])
    geometry_type = geojson_geometry["type"]

    # Normalise single geometries into the same structure as multi-geometries
    # We end up with three levels of nesting for the processing below
    if geometry_type == "Point":
        # Format [x, y]
        coordinates = [[coordinates]]
    elif geometry_type in ["LineString", "MultiPoint"]:
        # Format [[x, y], [x, y]]
        coordinates = [coordinates]
    elif geometry_type in ["Polygon", "MultiLineString"]:
        # Format [[[x, y], [x, y]]]
        pass
    elif geometry_type == "MultiPolygon":
        # Format [[[[x, y], [x, y]]]], flatten coords
        coordinates = [coord for poly in coordinates for coord in poly]
    else:
        raise ValueError(f"Unsupported GeoJSON geometry type: {geometry_type}")

    # Prepare the JavaRosa format by iterating over coordinates
    javarosa_geometry = []
    for polygon_or_line in coordinates:
        for lon, lat in polygon_or_line:
            javarosa_geometry.append(f"{lat} {lon} 0.0 0.0")

    return ";".join(javarosa_geometry)


async def javarosa_to_geojson_geom(javarosa_geom_string: str) -> dict:
    """Convert a JavaRosa format string to GeoJSON geometry.

    The geometry type is automatically inferred from the geometry
    coordinate structure.

    Args:
        javarosa_geom_string (str): The JavaRosa geometry.

    Returns:
        dict: A geojson geometry.
    """
    if not javarosa_geom_string or not isinstance(javarosa_geom_string, str):
        return {}

    coordinates = []

    for point_str in javarosa_geom_string.strip().split(";"):
        parts = point_str.strip().split()

        # Expect at least lat and lon
        if len(parts) < 2:
            continue

        try:
            lat = float(parts[0])
            lon = float(parts[1])
            coordinates.append([lon, lat])
        except ValueError:
            continue  # Skip if conversion fails

    if not coordinates:
        return {}

    # Determine geometry type
    if len(coordinates) == 1:
        geom_type = "Point"
        coordinates = coordinates[0]  # Flatten for Point
    elif (
        coordinates[0] == coordinates[-1] and len(coordinates) >= 4
    ):  # Check if closed loop
        geom_type = "Polygon"
        coordinates = [coordinates]  # Wrap in extra list for Polygon
    else:
        geom_type = "LineString"

    return {"type": geom_type, "coordinates": coordinates}


def multigeom_to_singlegeom(
    featcol: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Converts any Multi(xxx) geometry types to list of individual geometries.

    Args:
        featcol : A GeoJSON FeatureCollection of geometries.

    Returns:
        geojson.FeatureCollection: A GeoJSON FeatureCollection containing
            single geometry types only: Polygon, LineString, Point.
    """

    def split_multigeom(geom, properties):
        """Splits multi-geometries into individual geometries."""
        return [
            geojson.Feature(geometry=mapping(single_geom), properties=properties)
            for single_geom in geom.geoms
        ]

    final_features = []

    for feature in featcol.get("features", []):
        properties = feature.get("properties", {})
        try:
            geom = shape(feature["geometry"])
        except ValueError:
            log.warning(f"Geometry is not valid, so was skipped: {feature['geometry']}")
        if geom.geom_type.startswith("Multi"):
            # Handle all MultiXXX types
            final_features.extend(split_multigeom(geom, properties))
        else:
            # Handle single geometry types
            final_features.append(
                geojson.Feature(
                    geometry=mapping(geom),
                    properties=properties,
                )
            )

    return geojson.FeatureCollection(final_features)


def remove_holes(polygon: Polygon):
    """Detect and remove holes within a polygon."""
    if polygon.interiors:
        return Polygon(polygon.exterior)  # Keep only the exterior ring
    return polygon


def create_single_polygon(multipolygon: MultiPolygon, dissolve_polygon: bool):
    """If a MultiPolygon can create a common exterior ring, return a single AOI Polygon.

    Otherwise, dissolve the polygons with convex hull.
    """
    unified = [Polygon(poly.exterior) for poly in multipolygon.geoms]
    merged_polygon = unary_union(unified)

    if merged_polygon.geom_type == "MultiPolygon":
        polygons = [
            Polygon(poly.exterior) for poly in merged_polygon.geoms if poly.is_valid
        ]
        union_poly = unary_union(polygons)

        if union_poly.geom_type == "Polygon":
            return union_poly

        if union_poly.geom_type == "MultiPolygon" and dissolve_polygon:
            # disjoint polygons
            return union_poly.convex_hull

    return merged_polygon


def ensure_right_hand_rule(polygon: Polygon):
    """Check if a polygon follows the right-hand rule, fix it if not."""
    if polygon.exterior.is_ccw:  # If counter-clockwise, reverse it
        return Polygon(
            polygon.exterior.coords[::-1],
            [interior.coords[::-1] for interior in polygon.interiors],
        )
    return polygon


def clean_geom(geom):
    """Clean geometries based on their type."""
    if isinstance(geom, (LineString, MultiLineString)):
        lines = geom.geoms if isinstance(geom, MultiLineString) else [geom]
        cleaned_lines = []
        for line in lines:
            buffered = line.buffer(0.0001)
            if buffered.is_valid:
                cleaned_lines.append(buffered)
        return cleaned_lines

    if geom.geom_type in {"Polygon", "MultiPolygon"}:
        if geom.geom_type == "MultiPolygon":
            return [ensure_right_hand_rule(remove_holes(p)) for p in geom.geoms]
        return [ensure_right_hand_rule(remove_holes(geom))]

    return [geom]


def merge_polygons(
    featcol: geojson.FeatureCollection,
    merge: bool = True,
    dissolve_polygon: bool = False,
) -> geojson.FeatureCollection:
    """Merge or clean geometries in a FeatureCollection.

    LineStrings are converted to polygons using buffer.

    Args:
        featcol: a FeatureCollection containing geometries.
        dissolve_polygon: True to dissolve polygons to single polygon.
        merge: True to merge geometries into a single polygon.

    Returns:
        geojson.FeatureCollection: a FeatureCollection of a single Polygon.
    """
    try:
        features = featcol.get("features", [])
        geom_list, properties = [], {}

        if not merge:
            cleaned = []
            for feature in features:
                for g in clean_geom(shape(feature["geometry"])):
                    cleaned.append(
                        geojson.Feature(
                            geometry=mapping(g),
                            properties=feature.get("properties", {}),
                        )
                    )
            return geojson.FeatureCollection(cleaned)

        for feature in features:
            properties = feature.get("properties", {})
            geom_list.extend(clean_geom(shape(feature["geometry"])))

        if not geom_list:
            raise ValueError("No valid geometries found in the FeatureCollection")

        # Merge all geometries into a single polygon
        merged_geom = create_single_polygon(MultiPolygon(geom_list), dissolve_polygon)
        # Ensure we have a valid polygon
        if not merged_geom.is_valid:
            merged_geom = merged_geom.buffer(0)  # Clean the geometry

        # Create FeatureCollection
        return geojson.FeatureCollection(
            [geojson.Feature(geometry=mapping(merged_geom), properties=properties)]
        )
    except Exception as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Couldn't merge the geometries into a polygon: {str(e)}",
        ) from e


async def get_osm_geometries(osm_category, geometry):
    """Request a snapshot based on the provided geometry.

    Args:
        osm_category(str): feature category type (eg: buildings).
        geometry (str): The geometry data in JSON format.

    Returns:
        dict: The JSON response containing the snapshot data.
    """
    config_filename = XLSFormType(osm_category).name
    data_model = f"{data_models_path}/{config_filename}.json"
    geom_type = "polygon"

    if config_filename == "highways":
        geom_type = "line"

    with open(data_model, encoding="utf-8") as f:
        config_json = json.load(f)

    return await get_osm_data(
        geometry=geometry,
        outputType="geojson",
        output_options=RawDataOutputOptions(download_file=False),
        geometryType=[geom_type],
        bindZip=True,
        use_st_within=False,
        filters=config_json,
    )


# def geometries_almost_equal(
#     geom1: BaseGeometry, geom2: BaseGeometry, tolerance: float = 1e-6
# ) -> bool:
#     """Determine if two geometries are almost equal within a tolerance.

#     Args:
#         geom1 (BaseGeometry): First geometry.
#         geom2 (BaseGeometry): Second geometry.
#         tolerance (float): Tolerance level for almost equality.

#     Returns:
#         bool: True if geometries are almost equal else False.
#     """
#     return geom1.equals_exact(geom2, tolerance)


def check_overlap(geom1: BaseGeometry, geom2: BaseGeometry) -> float:
    """Determine if two geometries have a partial overlap.

    Args:
        geom1 (BaseGeometry): First geometry.
        geom2 (BaseGeometry): Second geometry.

    Returns:
        bool: True if geometries have a partial overlap, else False.
    """
    intersection = geom1.intersection(geom2)
    intersection_area = intersection.area

    geom1_area = geom1.area
    geom2_area = geom2.area

    # Calculate overlap percentage with respect to the smaller geometry
    smaller_area = min(geom1_area, geom2_area)
    overlap_percentage = (intersection_area / smaller_area) * 100
    return round(overlap_percentage, 2)


def conflate_features(
    input_features: list, osm_features: list, remove_conflated=False, tolerance=1e-6
):
    """Conflate input features with OSM features to identify overlaps.

    Args:
        input_features (list): A list of input features with geometries.
        osm_features (list): A list of OSM features with geometries.
        remove_conflated (bool): Flag to remove conflated features.
        tolerance (float): Tolerance level for almost equality.

    Returns:
        list: A list of features after conflation with OSM features.
    """
    osm_ids_in_subs = {int(feature["properties"]["xid"]) for feature in input_features}

    # filter and create a json with key osm_id and its feature
    osm_id_to_feature = {
        feature["properties"]["osm_id"]: feature
        for feature in osm_features
        if feature["properties"]["osm_id"] in osm_ids_in_subs
    }
    return_features = []

    for input_feature in input_features:
        osm_id = int(input_feature["properties"]["xid"])
        osm_feature = osm_id_to_feature.get(osm_id)  # get same feature from osm
        if not osm_feature:
            continue

        input_geometry = shape(input_feature["geometry"])
        osm_geometry = shape(osm_feature["geometry"])
        overlap_percent = check_overlap(input_geometry, osm_geometry)

        updated_input_feature = {
            "type": input_feature["type"],
            "geometry": input_feature["geometry"],
            "properties": {
                **input_feature["properties"],
                "overlap_percent": overlap_percent,
            },
        }
        updated_input_feature |= osm_feature["properties"]

        if overlap_percent < 90:
            corresponding_feature = {
                "type": "Feature",
                "geometry": mapping(osm_geometry),
                "properties": osm_feature["properties"],
            }
            return_features.append(corresponding_feature)

        return_features.append(updated_input_feature)

    return return_features
