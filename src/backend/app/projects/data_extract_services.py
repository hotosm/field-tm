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
"""Download, validate and save OSM data extracts for a project."""

import json
import logging
from asyncio import TimeoutError as AsyncTimeoutError

import httpx
from geojson_aoi import parse_aoi
from osm_fieldwork.json_data_models import data_models_path
from psycopg import AsyncConnection

from app.config import settings
from app.db.enums import XLSFormType
from app.db.models import DbProject
from app.errors import (
    NotFoundError,
    ServiceError,
    UpstreamError,
    ValidationError,
)
from app.helpers.geometry_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    featcol_polygons_to_centroids,
)
from app.projects import project_crud, project_deps, project_schemas

log = logging.getLogger(__name__)


def _extract_config_path(osm_category: str) -> str:
    """Resolve the data-model config path for an OSM category."""
    try:
        osm_category_enum = XLSFormType[osm_category.lower()]
    except (KeyError, AttributeError):
        osm_category_enum = XLSFormType.buildings
    return f"{data_models_path}/{osm_category_enum.name}.json"


def _configure_extract_sources(
    config_data: dict,
    geom_type: str,
    centroid: bool,
) -> tuple[dict, list[str]]:
    """Select raw-data-api source tables and geometry types.

    Point mode with centroid=True includes polygon centroids and existing nodes.
    """
    geom_type_lower = geom_type.lower()
    source_table_config = {
        ("polygon", False): ["ways_poly"],
        ("polygon", True): ["ways_poly"],
        ("point", False): ["nodes"],
        ("point", True): ["ways_poly", "nodes"],
        ("polyline", False): ["ways_line"],
        ("polyline", True): ["ways_line"],
    }
    config_data["from"] = source_table_config.get((geom_type_lower, centroid))

    geometry_types_config = {
        ("polygon", False): ["polygon"],
        ("polygon", True): ["polygon"],
        ("point", False): ["point"],
        ("point", True): ["polygon", "point"],
        ("polyline", False): ["line"],
        ("polyline", True): ["line"],
    }
    geometry_types = geometry_types_config.get(
        (geom_type_lower, centroid), [geom_type_lower]
    )
    return config_data, geometry_types


async def _download_extract_geojson(download_url: str) -> dict:
    """Download and parse the GeoJSON payload from the raw-data extract URL."""
    # No total cap (large extracts can take minutes); bound on stalls only.
    timeout = httpx.Timeout(300, connect=30)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(download_url)
    except httpx.HTTPError as e:
        raise ServiceError("Failed to download GeoJSON from extract URL.") from e
    if response.is_error:
        raise ServiceError("Failed to download GeoJSON from extract URL.")
    text_content = response.text

    try:
        geojson_data = json.loads(text_content)
    except json.JSONDecodeError as e:
        raise ServiceError("Failed to parse GeoJSON data from download.") from e

    if not isinstance(geojson_data, dict):
        raise ServiceError("Downloaded extract is not valid GeoJSON data.")
    return geojson_data


def _validate_downloaded_geojson(geojson_data: dict) -> dict:
    """Validate the downloaded GeoJSON payload and normalize empty features."""
    features = geojson_data.get("features")
    if features is None:
        features = []
        geojson_data["features"] = features
    if not isinstance(features, list):
        raise ServiceError("Downloaded GeoJSON has invalid feature structure.")
    if len(features) == 0:
        raise ValidationError(
            "No data found in OSM. Please continue with the Collect New "
            "Data Only option."
        )
    return geojson_data


def _expected_extract_output_geom(geometry_types: list[str], centroid: bool) -> str:
    """Return the GeoJSON geometry type expected from raw-data-api."""
    # Points when centroid=True (computed after download) or when the only
    # source is `point`; `line` stays as LineString; otherwise Polygon.
    if centroid or geometry_types == ["point"]:
        return "Point"
    if geometry_types == ["line"]:
        return "LineString"
    return "Polygon"


async def _request_osm_data_extract(
    project_id: int,
    aoi_featcol: dict,
    geometry_types: list[str],
    config_data: dict,
):
    """Request a raw-data-api extract and map common failures to service errors."""
    try:
        return await project_crud.generate_data_extract(
            project_id,
            aoi_featcol,
            geometry_types,
            config_data,
            centroid=False,
            use_st_within=True,
        )
    except UpstreamError as exc:
        raise ServiceError(
            "OSM data extraction timed out or failed upstream. "
            "Please reduce the AOI size or choose Collect New Data Only."
        ) from exc
    except AsyncTimeoutError as exc:
        raise ServiceError(
            "OSM data extraction timed out. "
            "Please reduce the AOI size or choose Collect New Data Only."
        ) from exc


def _parse_polygon_extract_geojson(geojson_data: dict) -> dict:
    """Run polygon-only PostGIS normalization for polygon extracts."""
    try:
        return parse_aoi(settings.FTM_DB_URL, geojson_data)
    except TypeError as exc:
        raise ValidationError(
            "No valid geometries found in OSM for the selected extract "
            "settings. Please continue with the Collect New Data Only option."
        ) from exc


def _normalize_downloaded_extract(
    geojson_data: dict,
    expected_output_geom: str,
) -> dict:
    """Normalize and filter downloaded extract GeoJSON to one output geometry."""
    # parse_aoi drops non-polygons; point and line extracts must skip it.
    featcol = (
        _parse_polygon_extract_geojson(geojson_data)
        if expected_output_geom == "Polygon"
        else geojson_data
    )

    if not featcol or not isinstance(featcol, dict) or not featcol.get("features"):
        raise ValidationError(
            "No valid geometries found in OSM for the selected extract settings. "
            "Please continue with the Collect New Data Only option."
        )

    return featcol_keep_single_geom_type(featcol, expected_output_geom)


async def download_osm_data(
    db: AsyncConnection,
    project_id: int,
    osm_category: str = "buildings",
    geom_type: str = "POLYGON",
    centroid: bool = False,
) -> dict:
    """Download and validate a project's OSM extract as a GeoJSON FeatureCollection.

    Raises NotFoundError for a missing outline or ServiceError on extraction failure.
    """
    project = await project_deps.get_project_by_id(db, project_id)

    outline = project.outline
    if not outline:
        raise NotFoundError("Project outline not found.")

    aoi_featcol = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": outline, "properties": {}}],
    }

    with open(_extract_config_path(osm_category), encoding="utf-8") as f:
        config_data = json.load(f)
    config_data, geometry_types = _configure_extract_sources(
        config_data,
        geom_type,
        centroid,
    )
    expected_output_geom = _expected_extract_output_geom(geometry_types, centroid)

    result = await _request_osm_data_extract(
        project.id,
        aoi_featcol,
        geometry_types,
        config_data,
    )

    download_url = result.data.get("download_url")
    if not download_url:
        raise ServiceError("Failed to get download URL from data extract.")

    geojson_data = await _download_extract_geojson(download_url)
    geojson_data = _validate_downloaded_geojson(geojson_data)
    # Centroids are computed here: raw-data-api's centroid mode was unreliable.
    if centroid:
        geojson_data = await featcol_polygons_to_centroids(geojson_data)
    featcol_single_geom_type = _normalize_downloaded_extract(
        geojson_data,
        expected_output_geom,
    )

    if not featcol_single_geom_type:
        raise ServiceError("Could not process GeoJSON data.")

    await check_crs(featcol_single_geom_type)

    return featcol_single_geom_type


async def save_data_extract(
    db: AsyncConnection,
    project_id: int,
    geojson_data: dict,
) -> int:
    """Store a GeoJSON extract and return its feature count.

    Raises ValidationError for empty or invalid GeoJSON.
    """
    if not geojson_data:
        raise ValidationError("No GeoJSON data provided.")

    features = geojson_data.get("features", [])
    if not features:
        raise ValidationError("GeoJSON data contains no features.")

    await check_crs(geojson_data)

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_geojson=geojson_data,
        ),
    )
    await db.commit()

    feature_count = len(features)
    log.info(
        f"Saved data extract with {feature_count} features for project {project_id}"
    )
    return feature_count
