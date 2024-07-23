# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""PostGIS and geometry handling helper funcs."""

import json
import logging
from asyncio import gather
from datetime import datetime, timezone
from io import BytesIO
from random import getrandbits
from typing import Optional, Union

import geojson
import requests
from fastapi import HTTPException
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from osm_fieldwork.data_models import data_models_path
from osm_rawdata.postgres import PostgresClient
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import XLSFormType

log = logging.getLogger(__name__)
API_URL = settings.RAW_DATA_API_URL


def timestamp():
    """Get the current time.

    Used to insert a current timestamp into Pydantic models.
    """
    return datetime.now(timezone.utc)


def read_wkb(wkb: WKBElement):
    """Load a WKBElement and return a shapely geometry."""
    return to_shape(wkb)


def write_wkb(shape):
    """Load shapely geometry and output WKBElement."""
    return from_shape(shape)


def wkb_geom_to_feature(
    geometry: WKBElement, properties: Optional[dict] = None, id: Optional[int] = None
) -> dict:
    """Convert SQLAlchemy geometry to GeoJSON Feature dict."""
    return {
        "type": "Feature",
        "geometry": mapping(read_wkb(geometry)),
        "properties": properties,
        "id": id,
        # bbox=shape.bounds,
    }


def featcol_to_wkb_geom(
    featcol: geojson.FeatureCollection,
) -> Optional[WKBElement]:
    """Convert GeoJSON to SQLAlchemy geometry."""
    features = featcol.get("features", [])

    if len(features) > 1 and features[0].get("type") == "MultiPolygon":
        featcol = multipolygon_to_polygon(featcol)
        features = featcol.get("features", [])

    geometry = features[0].get("geometry")
    shapely_geom = shape(geometry)
    return write_wkb(shapely_geom)


def get_centroid(
    geometry: WKBElement,
    properties: Optional[dict] = None,
    id: Optional[int] = None,
) -> dict:
    """Convert SQLAlchemy geometry to Centroid GeoJSON.

    If no id or properties fields are passed, returns the coordinate only.
    Else returns a Feature GeoJSON.
    """
    shape = to_shape(geometry)
    point = shape.centroid
    if not properties and not id:
        return point
    geojson = {
        "type": "Feature",
        "geometry": mapping(point),
        "properties": properties,
        "id": id,
    }
    return geojson


async def featcol_to_flatgeobuf(
    db: Session, geojson: geojson.FeatureCollection
) -> Optional[bytes]:
    """From a given FeatureCollection, return a memory flatgeobuf obj.

    NOTE this generate an fgb with string timestamps, not datetime.
    NOTE ogr2ogr would generate datetime, but parsing does not seem to work.

    Args:
        db (Session): SQLAlchemy db session.
        geojson (geojson.FeatureCollection): a FeatureCollection object.

    Returns:
        flatgeobuf (bytes): a Python bytes representation of a flatgeobuf file.
    """
    geojson_with_props = add_required_geojson_properties(geojson)

    sql = text(
        """
        DROP TABLE IF EXISTS temp_features CASCADE;

        -- Wrap geometries in GeometryCollection
        CREATE TEMP TABLE IF NOT EXISTS temp_features(
            geom geometry(GeometryCollection, 4326),
            osm_id integer,
            tags text,
            version integer,
            changeset integer,
            timestamp text
        );

        WITH data AS (SELECT CAST(:geojson AS json) AS fc)
        INSERT INTO temp_features
            (geom, osm_id, tags, version, changeset, timestamp)
        SELECT
            ST_ForceCollection(ST_GeomFromGeoJSON(feat->>'geometry')) AS geom,
            regexp_replace(
                (feat->'properties'->>'osm_id')::text, '[^0-9]', '', 'g'
            )::integer as osm_id,
            (feat->'properties'->>'tags')::text as tags,
            (feat->'properties'->>'version')::integer as version,
            (feat->'properties'->>'changeset')::integer as changeset,
            (feat->'properties'->>'timestamp')::text as timestamp
        FROM json_array_elements((SELECT fc->'features' FROM data)) AS f(feat);

        -- Second param = generate with spatial index
        SELECT ST_AsFlatGeobuf(geoms, true)
        FROM (SELECT * FROM temp_features) AS geoms;
    """
    )

    # Run the SQL
    result = db.execute(sql, {"geojson": json.dumps(geojson_with_props)})
    # Get a memoryview object, then extract to Bytes
    flatgeobuf = result.first()

    if flatgeobuf:
        return flatgeobuf[0].tobytes()

    # Nothing returned (either no features passed, or failed)
    return None


async def flatgeobuf_to_featcol(
    db: Session, flatgeobuf: bytes
) -> Optional[geojson.FeatureCollection]:
    """Converts FlatGeobuf data to GeoJSON.

    Extracts single geometries from wrapped GeometryCollection if used.

    Args:
        db (Session): SQLAlchemy db session.
        flatgeobuf (bytes): FlatGeobuf data in bytes format.

    Returns:
        geojson.FeatureCollection: A FeatureCollection object.
    """
    sql = text(
        """
        DROP TABLE IF EXISTS public.temp_fgb CASCADE;

        SELECT ST_FromFlatGeobufToTable('public', 'temp_fgb', :fgb_bytes);

        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(feature)
        ) AS feature_collection
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_GeometryN(fgb_data.geom, 1))::jsonb,
                'id', fgb_data.osm_id::VARCHAR,
                'properties', jsonb_build_object(
                    'osm_id', fgb_data.osm_id,
                    'tags', fgb_data.tags,
                    'version', fgb_data.version,
                    'changeset', fgb_data.changeset,
                    'timestamp', fgb_data.timestamp
                )::jsonb
            ) AS feature
            FROM (
                SELECT
                    geom,
                    osm_id,
                    tags,
                    version,
                    changeset,
                    timestamp
                FROM ST_FromFlatGeobuf(null::temp_fgb, :fgb_bytes)
            ) AS fgb_data
        ) AS features;
    """
    )

    try:
        result = db.execute(sql, {"fgb_bytes": flatgeobuf})
        feature_collection = result.first()
    except ProgrammingError as e:
        log.error(e)
        log.error(
            "Attempted flatgeobuf --> geojson conversion failed. "
            "Perhaps there is a duplicate 'id' column?"
        )
        return None

    if feature_collection:
        return geojson.loads(json.dumps(feature_collection[0]))

    return None


async def split_geojson_by_task_areas(
    db: Session,
    featcol: geojson.FeatureCollection,
    project_id: int,
) -> Optional[dict[int, geojson.FeatureCollection]]:
    """Split GeoJSON into tagged task area GeoJSONs.

    NOTE inserts feature.properties.osm_id as feature.id for each feature.
    NOTE ST_Within used on polygon centroids to correctly capture the geoms per task.

    Args:
        db (Session): SQLAlchemy db session.
        featcol (bytes): Data extract feature collection.
        project_id (int): The project ID for associated tasks.

    Returns:
        dict[int, geojson.FeatureCollection]: {task_id: FeatureCollection} mapping.
    """
    sql = text(
        """
        -- Drop table if already exists
        DROP TABLE IF EXISTS temp_features CASCADE;

        -- Create a temporary table to store the parsed GeoJSON features
        CREATE TEMP TABLE temp_features (
            id VARCHAR,
            geometry GEOMETRY,
            properties JSONB
        );

        -- Insert parsed geometries and properties into the temporary table
        INSERT INTO temp_features (id, geometry, properties)
        SELECT
            (feature->'properties'->>'osm_id')::VARCHAR AS id,
            ST_SetSRID(ST_GeomFromGeoJSON(feature->>'geometry'), 4326) AS geometry,
            jsonb_set(
                jsonb_set(
                    feature->'properties',
                    '{task_id}', to_jsonb(tasks.project_task_index), true
                ),
                '{project_id}', to_jsonb(tasks.project_id), true
            ) AS properties
        FROM (
            SELECT jsonb_array_elements(CAST(:geojson_featcol AS jsonb)->'features')
            AS feature
        ) AS features
        JOIN tasks ON tasks.project_id = :project_id
        WHERE
            ST_Within(
                ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(feature->>'geometry'), 4326)
                ), tasks.outline);

        -- Retrieve task outlines based on the provided project_id
        SELECT
            tasks.project_task_index AS task_id,
            jsonb_build_object(
                'type', 'FeatureCollection',
                'features', jsonb_agg(feature)
            ) AS task_features
        FROM
            tasks
        LEFT JOIN LATERAL (
            SELECT
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(temp_features.geometry)::jsonb,
                    'id', temp_features.id::VARCHAR,
                    'properties', temp_features.properties
                ) AS feature
            FROM (
                SELECT DISTINCT ON (geometry)
                    id,
                    geometry,
                    properties
                FROM temp_features
            ) AS temp_features
            WHERE
                ST_Within(ST_Centroid(temp_features.geometry), tasks.outline)
        ) AS feature ON true
        WHERE
            tasks.project_id = :project_id
        GROUP BY
            tasks.project_task_index;
        """
    )

    try:
        result = db.execute(
            sql,
            {
                "geojson_featcol": json.dumps(featcol),
                "project_id": project_id,
            },
        )
        feature_collections = result.all()

    except ProgrammingError as e:
        log.error(e)
        log.error("Attempted geojson task splitting failed")
        return None

    if feature_collections:
        # NOTE the feature collections are nested in a tuple, first remove
        task_geojson_dict = {
            record[0]: geojson.loads(json.dumps(record[1]))
            for record in feature_collections
        }
        return task_geojson_dict

    return None


def add_required_geojson_properties(
    geojson: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Add required geojson properties if not present.

    This step is required prior to flatgeobuf generation,
    else the workflows of conversion between the formats will fail.
    """
    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})

        # The top level id is defined, set to osm_id
        if feature_id := feature.get("id"):
            properties["osm_id"] = feature_id

        # Check for id type embedded in properties
        if osm_id := properties.get("osm_id"):
            # osm_id property exists, set top level id
            feature["id"] = f"{osm_id}"
        else:
            if prop_id := properties.get("id"):
                # id is nested in properties, use that
                feature["id"] = f"{prop_id}"
                properties["osm_id"] = prop_id
            elif fid := properties.get("fid"):
                # The default from QGIS
                feature["id"] = f"{fid}"
                properties["osm_id"] = fid
            else:
                # Random id
                # NOTE 32-bit int is max supported by standard postgres Integer
                random_id = getrandbits(30)
                feature["id"] = f"{random_id}"
                properties["osm_id"] = random_id

        # Other required fields
        if not properties.get("tags"):
            properties["tags"] = ""
        if not properties.get("version"):
            properties["version"] = 1
        if not properties.get("changeset"):
            properties["changeset"] = 1
        if not properties.get("timestamp"):
            properties["timestamp"] = timestamp().strftime("%Y-%m-%dT%H:%M:%S")

    return geojson


def normalise_featcol(featcol: geojson.FeatureCollection) -> geojson.FeatureCollection:
    """Normalise a FeatureCollection into a standadised format.

    The final FeatureCollection will only contain:
    - Polygon
    - Polyline
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
    for feat in featcol.get("features", []):
        geom = feat.get("geometry")

        # Strip out GeometryCollection wrappers
        if (
            geom.get("type") == "GeometryCollection"
            and len(geom.get("geometries", [])) == 1
        ):
            feat["geometry"] = geom.get("geometries")[0]

        # Remove any z-dimension coordinates
        coords = geom.get("coordinates")
        if isinstance(coords, list) and len(coords) == 3:
            coords.pop()

    # Convert MultiPolygon type --> individual Polygons
    return multipolygon_to_polygon(featcol)


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


def featcol_keep_dominant_geom_type(
    featcol: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Strip out any geometries not matching the dominant geometry type."""
    features = featcol.get("features", [])
    geom_type = get_featcol_dominant_geom_type(featcol)

    features_filtered = [
        feature
        for feature in features
        if feature.get("geometry", {}).get("type", "") == geom_type
    ]

    return geojson.FeatureCollection(features_filtered)


def get_featcol_dominant_geom_type(featcol: geojson.FeatureCollection) -> str:
    """Get the predominant geometry type in a FeatureCollection."""
    geometry_counts = {"Polygon": 0, "Point": 0, "Polyline": 0}

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
            raise HTTPException(status_code=400, detail=error_message)
        return

    log.warning(input_geojson)
    log.warning(input_geojson.get("type"))
    if (input_geojson_type := input_geojson.get("type")) == "FeatureCollection":
        features = input_geojson.get("features", [])
        log.warning(features)
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

    log.warning(coordinates)
    if not is_valid_coordinate(first_coordinate):
        log.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)


def get_address_from_lat_lon(latitude, longitude):
    """Get address using Nominatim, using lat,lon."""
    base_url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "format": "json",
        "lat": latitude,
        "lon": longitude,
        "zoom": 18,
    }
    headers = {
        # Set the language to English
        "Accept-Language": "en",
        # Referer or User-Agent required as per usage policy:
        # https://operations.osmfoundation.org/policies/nominatim
        "Referer": settings.FMTM_DOMAIN,
    }

    log.debug(
        f"Getting Nominatim address from project lat ({latitude}) lon ({longitude})"
    )
    response = requests.get(base_url, params=params, headers=headers)
    if (status_code := response.status_code) != 200:
        log.error(f"Getting address string failed: {status_code}")
        return None

    data = response.json()
    log.debug(f"Nominatim response: {data}")

    address = data.get("address", None)
    if not address:
        log.error(f"Getting address string failed: {status_code}")
        return None

    country = address.get("country", "")
    city = address.get("city", "")
    state = address.get("state", "")

    address_str = f"{city},{country}" if city else f"{state},{country}"

    if not address_str or address_str == ",":
        log.error("Getting address string failed")
        return None

    return address_str


async def get_address_from_lat_lon_async(latitude, longitude):
    """Async wrapper for get_address_from_lat_lon."""
    return get_address_from_lat_lon(latitude, longitude)


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

    coordinates = []
    if geojson_geometry["type"] in ["Point", "LineString", "MultiPoint"]:
        coordinates = [[geojson_geometry.get("coordinates", [])]]
    elif geojson_geometry["type"] in ["Polygon", "MultiLineString"]:
        coordinates = geojson_geometry.get("coordinates", [])
    elif geojson_geometry["type"] == "MultiPolygon":
        # Flatten the list structure to get coordinates of all polygons
        coordinates = sum(geojson_geometry.get("coordinates", []), [])
    else:
        raise ValueError("Unsupported GeoJSON geometry type")

    javarosa_geometry = []
    for polygon in coordinates:
        for lon, lat in polygon:
            javarosa_geometry.append(f"{lat} {lon} 0.0 0.0")

    return ";".join(javarosa_geometry)


async def javarosa_to_geojson_geom(javarosa_geom_string: str, geom_type: str) -> dict:
    """Convert a JavaRosa format string to GeoJSON geometry.

    Args:
        javarosa_geom_string (str): The JavaRosa geometry.
        geom_type (str): The geometry type.

    Returns:
        dict: A geojson geometry.
    """
    if javarosa_geom_string is None:
        return {}

    if geom_type == "Point":
        lat, lon, _, _ = map(float, javarosa_geom_string.split())
        geojson_geometry = {"type": "Point", "coordinates": [lon, lat]}
    elif geom_type == "Polyline":
        coordinates = [
            [float(coord) for coord in reversed(point.split()[:2])]
            for point in javarosa_geom_string.split(";")
        ]
        geojson_geometry = {"type": "LineString", "coordinates": coordinates}
    elif geom_type == "Polygon":
        coordinates = [
            [
                [float(coord) for coord in reversed(point.split()[:2])]
                for point in coordinate.split(";")
            ]
            for coordinate in javarosa_geom_string.split(",")
        ]
        geojson_geometry = {"type": "Polygon", "coordinates": coordinates}
    else:
        raise ValueError("Unsupported GeoJSON geometry type")

    return geojson_geometry


async def feature_geojson_to_entity_dict(
    feature: dict,
) -> dict:
    """Convert a single GeoJSON to an Entity dict for upload."""
    feature_id = feature.get("id")

    geometry = feature.get("geometry", {})
    javarosa_geom = await geojson_to_javarosa_geom(geometry)

    # NOTE all properties MUST be string values for Entities, convert
    properties = {
        str(key): str(value) for key, value in feature.get("properties", {}).items()
    }
    # Set to TaskStatus enum READY value (0)
    properties["status"] = "0"

    task_id = properties.get("task_id")
    entity_label = f"Task {task_id} Feature {feature_id}"

    return {entity_label: {"geometry": javarosa_geom, **properties}}


async def task_geojson_dict_to_entity_values(task_geojson_dict):
    """Convert a dict of task GeoJSONs into data for ODK Entity upload."""
    asyncio_tasks = []
    for _, geojson_dict in task_geojson_dict.items():
        features = geojson_dict.get("features", [])
        asyncio_tasks.extend(
            [feature_geojson_to_entity_dict(feature) for feature in features if feature]
        )

    entity_values = await gather(*asyncio_tasks)
    # Merge all dicts into a single dict
    return {k: v for result in entity_values for k, v in result.items()}


def multipolygon_to_polygon(
    featcol: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Converts a GeoJSON FeatureCollection of MultiPolygons to Polygons.

    Args:
        featcol : A GeoJSON FeatureCollection containing MultiPolygons/Polygons.

    Returns:
        geojson.FeatureCollection: A GeoJSON FeatureCollection containing Polygons.
    """
    final_features = []

    for feature in featcol.get("features", []):
        properties = feature["properties"]
        try:
            geom = shape(feature["geometry"])
        except ValueError:
            log.warning(f"Geometry is not valid, so was skipped: {feature['geometry']}")
            continue

        if geom.geom_type == "Polygon":
            final_features.append(geojson.Feature(geometry=geom, properties=properties))
        elif geom.geom_type == "MultiPolygon":
            final_features.extend(
                geojson.Feature(geometry=polygon_coords, properties=properties)
                for polygon_coords in geom.geoms
            )

    return geojson.FeatureCollection(final_features)


def merge_polygons(
    featcol: geojson.FeatureCollection,
    dissolve_polygon: bool = True,
) -> geojson.FeatureCollection:
    """Merge multiple Polygons or MultiPolygons into a single Polygon.

    Args:
        featcol: a FeatureCollection containing geometries.
        dissolve_polygon: True to dissolve polygons to single polygon.

    Returns:
        geojson.FeatureCollection: a FeatureCollection of a single Polygon.
    """
    geom_list = []

    try:
        features = featcol.get("features", [])

        for feature in features:
            polygon = shape(feature["geometry"])
            geom_list.append(polygon)

        merged_polygon = unary_union(geom_list)
        merged_geojson = mapping(merged_polygon)

        # MultiPolygons are stripped out earlier
        if dissolve_polygon:
            merged_polygon = merged_polygon.convex_hull
            merged_geojson = mapping(merged_polygon)
            log.warning(
                "Resulted GeoJSON contains disjoint Polygons. "
                "Adjacent polygons are preferred."
            )
        return geojson.FeatureCollection([geojson.Feature(geometry=merged_geojson)])
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Couldn't merge the multipolygon to polygon: {str(e)}",
        ) from e


def get_osm_geometries(form_category, geometry):
    """Request a snapshot based on the provided geometry.

    Args:
        form_category(str): feature category type (eg: buildings).
        geometry (str): The geometry data in JSON format.

    Returns:
        dict: The JSON response containing the snapshot data.
    """
    config_filename = XLSFormType(form_category).name
    data_model = f"{data_models_path}/{config_filename}.yaml"

    with open(data_model, "rb") as data_model_yaml:
        extract_config = BytesIO(data_model_yaml.read())

    pg = PostgresClient(
        "underpass",
        extract_config,
        auth_token=settings.RAW_DATA_API_AUTH_TOKEN
        if settings.RAW_DATA_API_AUTH_TOKEN
        else None,
    )
    return pg.execQuery(
        geometry,
        extra_params={
            "outputType": "geojson",
            "bind_zip": True,
            "useStWithin": False,
        },
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
            "id": input_feature["properties"]["xid"],
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
                "id": osm_feature["properties"].pop("osm_id"),
                "geometry": mapping(osm_geometry),
                "properties": osm_feature["properties"],
            }
            return_features.append(corresponding_feature)

        return_features.append(updated_input_feature)

    return return_features
