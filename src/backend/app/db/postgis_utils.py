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
"""PostGIS helper funcs for DB-backed geometry operations."""

import json
import logging
from datetime import datetime, timezone
from random import getrandbits
from typing import Optional

import geojson
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from psycopg import AsyncConnection, ProgrammingError, sql
from psycopg.rows import dict_row
from psycopg.types.json import Json

from app.db.enums import DbGeomType

log = logging.getLogger(__name__)


async def split_geojson_by_task_areas(
    db: AsyncConnection,
    featcol: geojson.FeatureCollection,
    project_id: int,
    task_boundaries: Optional[dict] = None,
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
        task_boundaries (dict): Task boundaries as GeoJSON
            FeatureCollection.
        geom_type (str): The geometry type of the features.

    Returns:
        dict[int, geojson.FeatureCollection]: {task_id: FeatureCollection} mapping.
    """
    try:
        if not task_boundaries or not task_boundaries.get("features"):
            log.warning(
                "No task boundaries found for project "
                f"{project_id}, returning empty task extract dict"
            )
            return {}

        feature_ids, feature_properties, feature_geometries = _split_feature_arrays(
            featcol["features"]
        )
        task_indices, task_geometries = _split_task_boundary_arrays(
            task_boundaries["features"],
        )
        if not task_geometries:
            log.warning(
                f"No valid task boundary geometries found for project {project_id}"
            )
            return {}

        records = await _split_task_feature_records(
            db,
            feature_ids,
            feature_properties,
            feature_geometries,
            task_indices,
            task_geometries,
            project_id,
            geom_type == "POLYLINE",
        )
        return _split_records_to_feature_collections(records, project_id)
    except ProgrammingError as e:
        log.error(e)
        log.error("Attempted geojson task splitting failed")
        return None


def _split_feature_arrays(
    features: list[dict],
) -> tuple[list[str], list[Json], list[str]]:
    """Convert source features into array payloads for SQL unnest."""
    feature_ids = []
    feature_properties = []
    feature_geometries = []
    for feature in features:
        feature_ids.append(str(feature["properties"].get("osm_id")))
        feature_properties.append(Json(feature["properties"]))
        feature_geometries.append(json.dumps(feature["geometry"]))
    return feature_ids, feature_properties, feature_geometries


def _split_task_boundary_arrays(
    task_boundary_features: list[dict],
) -> tuple[list[int], list[str]]:
    """Convert task boundaries into array payloads for SQL unnest."""
    task_indices = []
    task_geometries = []
    for idx, task_feature in enumerate(task_boundary_features, start=1):
        if not task_feature.get("geometry"):
            continue
        task_geometries.append(json.dumps(task_feature["geometry"]))
        task_indices.append(idx)
    return task_indices, task_geometries


def _split_spatial_join_condition(use_st_intersects: bool) -> str:
    """Return the spatial join SQL predicate for the feature geometry type."""
    if use_st_intersects:
        return "ST_Intersects(f.geom, t.geom)"
    return "ST_Within(ST_Centroid(f.geom), t.geom)"


async def _split_task_feature_records(
    db: AsyncConnection,
    feature_ids: list[str],
    feature_properties: list[Json],
    feature_geometries: list[str],
    task_indices: list[int],
    task_geometries: list[str],
    project_id: int,
    use_st_intersects: bool,
) -> list[dict]:
    """Execute the SQL split query and return raw task-feature records."""
    spatial_join_condition = _split_spatial_join_condition(use_st_intersects)
    async with db.cursor(row_factory=dict_row) as cur:
        query = sql.SQL(
            """
            WITH feature_data AS (
                SELECT DISTINCT ON (geom)
                    unnest(%s::TEXT[]) AS id,
                    unnest(%s::JSONB[]) AS properties,
                    ST_SetSRID(ST_GeomFromGeoJSON(unnest(%s::TEXT[])), 4326) AS geom
            ),
            task_boundaries AS (
                SELECT
                    unnest(%s::INTEGER[]) AS task_index,
                    ST_SetSRID(ST_GeomFromGeoJSON(unnest(%s::TEXT[])), 4326) AS geom
            ),
            task_features AS (
                SELECT
                    t.task_index AS task_id,
                    jsonb_build_object(
                        'type', 'Feature',
                        'id', f.id,
                        'geometry', ST_AsGeoJSON(f.geom)::jsonb,
                        'properties', jsonb_set(
                            jsonb_set(
                                f.properties,
                                '{{task_id}}',
                                to_jsonb(t.task_index)
                            ),
                            '{{project_id}}', to_jsonb(%s)
                        )
                    ) AS feature
                FROM task_boundaries t
                JOIN feature_data f
                ON {spatial_join_condition}
            )
            SELECT
                task_id,
                jsonb_agg(feature) AS features
            FROM task_features
            GROUP BY task_id;
            """
        ).format(spatial_join_condition=sql.SQL(spatial_join_condition))
        await cur.execute(
            query,
            (
                feature_ids,
                feature_properties,
                feature_geometries,
                task_indices,
                task_geometries,
                project_id,
            ),
        )
        return await cur.fetchall()


def _split_records_to_feature_collections(
    records: list[dict],
    project_id: int,
) -> Optional[dict[int, geojson.FeatureCollection]]:
    """Convert raw SQL rows into task-id keyed feature collections."""
    result_dict = {
        rec["task_id"]: geojson.FeatureCollection(features=rec["features"])
        for rec in records
    }
    if not result_dict:
        msg = f"Failed to split project ({project_id}) geojson by task areas."
        log.exception(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )
    return result_dict


def add_required_geojson_properties(
    geojson: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Add required geojson properties if not present."""
    features = geojson.get("features", [])
    current_date = datetime.now(timezone.utc)

    for feature in features:
        properties = feature.get("properties", {})
        # Check for id type embedded in properties
        if feature_id := feature.get("id"):
            properties["osm_id"] = feature_id
        else:
            osm_id = (
                properties.get("osm_id")
                or properties.get("id")
                or properties.get("fid")
                # NOTE 32-bit int is max supported by standard postgres Integer
                or getrandbits(30)
            )

            if isinstance(osm_id, str) and "/" in osm_id:
                osm_id = osm_id.split("/")[0]

            # Ensure negative osm_id if it's derived
            if not properties.get("osm_id"):
                osm_id = -abs(int(osm_id))

            feature["id"] = str(osm_id)
            properties["osm_id"] = osm_id

        properties.setdefault("tags", "")
        properties.setdefault("version", 1)
        properties.setdefault("changeset", 1)
        properties.setdefault("timestamp", str(current_date))
        properties.setdefault("created_by", "")

        feature["properties"] = properties

    return geojson
