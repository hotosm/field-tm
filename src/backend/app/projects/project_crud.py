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
"""Logic for FMTM project routes."""

import json
import uuid
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from traceback import format_exc
from typing import Optional, Union

import geojson
import geojson_pydantic
import requests
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Request
from loguru import logger as log
from osm_fieldwork.basemapper import create_basemap_file
from osm_login_python.core import Auth
from osm_rawdata.postgres import PostgresClient
from psycopg import Connection
from psycopg.rows import class_row

from app.auth.providers.osm import get_osm_token, send_osm_message
from app.central import central_crud, central_schemas
from app.config import settings
from app.db.enums import BackgroundTaskStatus, HTTPStatus, XLSFormType
from app.db.models import DbBackgroundTask, DbBasemap, DbProject, DbTask, DbUser
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    featcol_to_flatgeobuf,
    flatgeobuf_to_featcol,
    get_featcol_dominant_geom_type,
    parse_geojson_file_to_featcol,
    split_geojson_by_task_areas,
)
from app.projects import project_deps, project_schemas
from app.s3 import add_file_to_bucket, add_obj_to_bucket

TILESDIR = "/opt/tiles"


async def get_projects_featcol(
    db: Connection,
    bbox: Optional[str] = None,
) -> geojson.FeatureCollection:
    """Get all projects, or a filtered subset."""
    bbox_condition = ""
    bbox_params = {}

    if bbox:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
        bbox_condition = """
            AND ST_Intersects(
                p.outline, ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, 4326)
            )
        """
        bbox_params = {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}

    # FIXME add logic for percentMapped and percentValidated
    # NOTE alternative logic to build a FeatureCollection
    """
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(feature), '[]'::jsonb)
        ) AS featcol
        FROM (...
    """
    sql = f"""
            SELECT
                'FeatureCollection' as type,
                COALESCE(jsonb_agg(feature), '[]'::jsonb) AS features
            FROM (
                SELECT jsonb_build_object(
                    'type', 'Feature',
                    'id', p.id,
                    'geometry', ST_AsGeoJSON(p.outline)::jsonb,
                    'properties', jsonb_build_object(
                        'name', p.name,
                        'percentMapped', 0,
                        'percentValidated', 0,
                        'created', p.created_at,
                        'link', concat('https://', %(domain)s::text, '/project/', p.id)
                    )
                ) AS feature
                FROM projects p
                WHERE p.visibility = 'PUBLIC'
                {bbox_condition}
            ) AS features;
        """

    async with db.cursor(
        row_factory=class_row(geojson_pydantic.FeatureCollection)
    ) as cur:
        query_params = {"domain": settings.FMTM_DOMAIN}
        if bbox:
            query_params.update(bbox_params)
        await cur.execute(sql, query_params)
        featcol = await cur.fetchone()

    if not featcol:
        return HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Failed to generate project FeatureCollection",
        )

    return featcol


async def generate_data_extract(
    aoi: geojson.FeatureCollection | geojson.Feature | dict,
    extract_config: Optional[BytesIO] = None,
) -> str:
    """Request a new data extract in flatgeobuf format.

    Args:
        db (Connection): The database connection.
        aoi (geojson.FeatureCollection | geojson.Feature | dict]):
            Area of interest for data extraction.
        extract_config (Optional[BytesIO], optional):
            Configuration for data extraction. Defaults to None.

    Raises:
        HTTPException:
            When necessary parameters are missing or data extraction fails.

    Returns:
        str:
            URL for the flatgeobuf data extract.
    """
    if not extract_config:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="To generate a new data extract a form_category must be specified.",
        )

    pg = PostgresClient(
        "underpass",
        extract_config,
        auth_token=settings.RAW_DATA_API_AUTH_TOKEN.get_secret_value()
        if settings.RAW_DATA_API_AUTH_TOKEN
        else None,
    )
    fgb_url = pg.execQuery(
        aoi,
        extra_params={
            "fileName": (
                f"fmtm/{settings.FMTM_DOMAIN}/data_extract"
                if settings.RAW_DATA_API_AUTH_TOKEN
                else "fmtm_extract"
            ),
            "outputType": "fgb",
            "bind_zip": False,
            "useStWithin": False,
            "fgb_wrap_geoms": True,
        },
    )

    if not fgb_url:
        msg = "Could not get download URL for data extract. Did the API change?"
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    return fgb_url


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def read_and_insert_xlsforms(db: Connection, directory: str) -> None:
    """Read the list of XLSForms from the disk and sync them with the database."""
    async with db.cursor() as cur:
        existing_db_forms = set()

        # Collect all existing XLSForm titles from the database
        select_existing_query = """
            SELECT title FROM xlsforms;
        """
        await cur.execute(select_existing_query)
        existing_db_forms = {row[0] for row in await cur.fetchall()}

        # Insert or update new XLSForms from disk
        for xls_type in XLSFormType:
            file_name = xls_type.name
            category = xls_type.value
            file_path = Path(directory) / f"{file_name}.xls"

            if not file_path.exists():
                log.warning(f"{file_path} does not exist!")
                continue

            if file_path.stat().st_size == 0:
                log.warning(f"{file_path} is empty!")
                continue

            with open(file_path, "rb") as xls:
                data = xls.read()

            try:
                insert_query = """
                    INSERT INTO xlsforms (title, xls)
                    VALUES (%(title)s, %(xls)s)
                    ON CONFLICT (title) DO UPDATE
                    SET xls = EXCLUDED.xls
                """
                await cur.execute(insert_query, {"title": category, "xls": data})
                log.info(f"XLSForm for '{category}' inserted/updated in the database")

            except Exception as e:
                log.exception(
                    f"Failed to insert or update {category} in the database. "
                    f"Error: {e}",
                    stack_info=True,
                )

        # Determine the forms that need to be deleted (those in the DB but
        # not in the current XLSFormType)
        required_forms = {xls_type.value for xls_type in XLSFormType}
        forms_to_delete = existing_db_forms - required_forms

        if forms_to_delete:
            delete_query = """
                DELETE FROM xlsforms WHERE title = ANY(%(titles)s)
            """
            await cur.execute(delete_query, {"titles": list(forms_to_delete)})
            log.info(f"Deleted XLSForms from the database: {forms_to_delete}")


async def get_or_set_data_extract_url(
    db: Connection,
    db_project: DbProject,
    url: Optional[str],
) -> str:
    """Get or set the data extract URL for a project.

    Args:
        db (Connection): The database connection.
        db_project (DbProject): The project object.
        url (str): URL to the streamable flatgeobuf data extract.
            If not passed, a new extract is generated.

    Returns:
        str: URL to fgb file in S3.
    """
    project_id = db_project.id
    # If url, get extract
    # If not url, get new extract / set in db
    if not url:
        existing_url = db_project.data_extract_url

        if not existing_url:
            msg = (
                f"No data extract exists for project ({project_id}). "
                "To generate one, call 'projects/generate-data-extract/'"
            )
            log.error(msg)
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)
        return existing_url

    # FIXME determine this using get_featcol_dominant_geom_type ?
    # FIXME would have to download extract first though
    # Perhaps we do this via generate-data-extract URL
    extract_type = "polygon"

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_url=url,
            data_extract_type=extract_type,
        ),
    )

    return url


async def upload_custom_extract_to_s3(
    db: Connection,
    project_id: int,
    fgb_content: bytes,
    data_extract_type: str,
) -> str:
    """Uploads custom data extracts to S3.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.
        fgb_content (bytes): Content of read flatgeobuf file.
        data_extract_type (str): centroid/polygon/line for database.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    log.debug(f"Uploading custom data extract for project ({project.id})")

    fgb_obj = BytesIO(fgb_content)
    s3_fgb_path = f"{project.organisation_id}/{project_id}/custom_extract.fgb"

    log.debug(f"Uploading fgb to S3 path: /{s3_fgb_path}")
    add_obj_to_bucket(
        settings.S3_BUCKET_NAME,
        fgb_obj,
        s3_fgb_path,
        content_type="application/octet-stream",
    )

    # Add url and type to database
    s3_fgb_full_url = (
        f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}/{s3_fgb_path}"
    )

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_url=s3_fgb_full_url,
            data_extract_type=data_extract_type,
        ),
    )

    return s3_fgb_full_url


async def upload_custom_fgb_extract(
    db: Connection,
    project_id: int,
    fgb_content: bytes,
) -> str:
    """Upload a flatgeobuf data extract.

    FIXME how can we validate this has the required fields for geojson conversion?
    Requires:
        "id"
        "osm_id"
        "tags"
        "version"
        "changeset"
        "timestamp"

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.
        fgb_content (bytes): Content of read flatgeobuf file.

    Returns:
        str: URL to fgb file in S3.
    """
    featcol = await flatgeobuf_to_featcol(db, fgb_content)

    if not featcol:
        msg = f"Failed extracting geojson from flatgeobuf for project ({project_id})"
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)

    data_extract_type = await get_data_extract_type(featcol)

    return await upload_custom_extract_to_s3(
        db,
        project_id,
        fgb_content,
        data_extract_type,
    )


async def get_data_extract_type(featcol: geojson.FeatureCollection) -> str:
    """Determine predominant geometry type for extract."""
    geom_type = get_featcol_dominant_geom_type(featcol)
    if geom_type not in ["Polygon", "LineString", "Point"]:
        msg = (
            "Extract does not contain valid geometry types, from 'Polygon' "
            ", 'LineString' and 'Point'."
        )
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)
    geom_name_map = {
        "Polygon": "polygon",
        "Point": "centroid",
        "LineString": "line",
    }
    data_extract_type = geom_name_map.get(geom_type, "polygon")

    return data_extract_type


async def upload_custom_geojson_extract(
    db: Connection,
    project_id: int,
    geojson_raw: Union[str, bytes],
) -> str:
    """Upload a geojson data extract.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.
        geojson_raw (str): The custom data extracts contents.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    log.debug(f"Uploading custom data extract for project ({project.id})")

    featcol = parse_geojson_file_to_featcol(geojson_raw)
    featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

    if not featcol_single_geom_type:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Could not process geojson input",
        )

    await check_crs(featcol_single_geom_type)

    data_extract_type = await get_data_extract_type(featcol_single_geom_type)

    log.debug(
        "Generating fgb object from geojson with "
        f"{len(featcol_single_geom_type.get('features', []))} features"
    )
    fgb_data = await featcol_to_flatgeobuf(db, featcol_single_geom_type)

    if not fgb_data:
        msg = f"Failed converting geojson to flatgeobuf for project ({project_id})"
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)

    return await upload_custom_extract_to_s3(
        db, project_id, fgb_data, data_extract_type
    )


def flatten_dict(d, parent_key="", sep="_"):
    """Recursively flattens a nested dictionary into a single-level dictionary.

    Args:
        d (dict): The input dictionary.
        parent_key (str): The parent key (used for recursion).
        sep (str): The separator character to use in flattened keys.

    Returns:
        dict: The flattened dictionary.
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


async def generate_odk_central_project_content(
    project_odk_id: int,
    project_odk_form_id: str,
    odk_credentials: central_schemas.ODKCentralDecrypted,
    xlsform: BytesIO,
    task_extract_dict: dict[int, geojson.FeatureCollection],
    entity_properties: list[str],
) -> str:
    """Populate the project in ODK Central with XForm, Appuser, Permissions."""
    # The ODK Dataset (Entity List) must exist prior to main XLSForm
    entities_list = await central_crud.task_geojson_dict_to_entity_values(
        task_extract_dict
    )

    log.debug("Creating main ODK Entity list for project: features")
    await central_crud.create_entity_list(
        odk_credentials,
        project_odk_id,
        properties=entity_properties,
        dataset_name="features",
        entities_list=entities_list,
    )

    # Do final check of XLSForm validity + return parsed XForm
    xform = await central_crud.read_and_test_xform(xlsform)

    # Upload survey XForm
    log.info("Uploading survey XForm to ODK Central")
    central_crud.create_odk_xform(
        project_odk_id,
        xform,
        odk_credentials,
    )

    return await central_crud.get_appuser_token(
        project_odk_form_id,
        project_odk_id,
        odk_credentials,
    )


async def generate_project_files(
    db: Connection,
    project_id: int,
) -> bool:
    """Generate the files for a project.

    QR code (appuser), ODK XForm, ODK Entities from OSM data extract.

    Args:
        project_id(int): id of the FMTM project.
        background_task_id (uuid): the task_id of the background task.
        db (Connection): The database connection, newly generated.

    Returns:
        bool: True if success.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    log.info(f"Starting generate_project_files for project {project_id}")

    # Extract data extract from flatgeobuf
    log.debug("Getting data extract geojson from flatgeobuf")
    feature_collection = await get_project_features_geojson(db, project)

    # Get properties to create datasets
    entity_properties = list(
        feature_collection.get("features")[0].get("properties").keys()
    )
    entity_properties.append("submission_ids")

    # Split extract by task area
    log.debug("Splitting data extract per task area")
    # TODO in future this splitting could be removed if the task_id is
    # no longer used in the XLSForm for the map filter
    task_extract_dict = await split_geojson_by_task_areas(
        db, feature_collection, project_id
    )

    # Get ODK Project details
    project_odk_id = project.odkid
    project_xlsform = project.xlsform_content
    project_odk_form_id = project.odk_form_id
    project_odk_creds = project.odk_credentials

    odk_token = await generate_odk_central_project_content(
        project_odk_id,
        project_odk_form_id,
        project_odk_creds,
        BytesIO(project_xlsform),
        task_extract_dict,
        entity_properties,
    )
    log.debug(
        f"Setting encrypted odk token for FMTM project ({project_id}) "
        f"ODK project {project_odk_id}: {type(odk_token)} ({odk_token[:15]}...)"
    )
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            odk_token=odk_token,
        ),
    )

    task_feature_counts = [
        (
            task.id,
            len(task_extract_dict.get(task.project_task_index, {}).get("features", [])),
        )
        for task in project.tasks
    ]
    sql = """
        WITH task_update(id, feature_count) AS (
            VALUES {}
        )
        UPDATE
            public.tasks t
        SET
            feature_count = tu.feature_count
        FROM
            task_update tu
        WHERE
            t.id = tu.id;
    """
    value_placeholders = ", ".join(
        f"({task_id}, {feature_count})"
        for task_id, feature_count in task_feature_counts
    )
    formatted_sql = sql.format(value_placeholders)
    async with db.cursor() as cur:
        await cur.execute(formatted_sql)

    return True


async def get_task_geometry(db: Connection, project_id: int):
    """Retrieves the geometry of tasks associated with a project.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """
    db_tasks = await DbTask.all(db, project_id)
    features = []
    for task in db_tasks:
        properties = {
            "task_id": task.id,
        }
        feature = {
            "type": "Feature",
            "geometry": task.outline,
            "properties": properties,
        }
        features.append(feature)

    feature_collection = {"type": "FeatureCollection", "features": features}
    return json.dumps(feature_collection)


async def get_project_features_geojson(
    db: Connection,
    db_project: DbProject,
    task_id: Optional[int] = None,
) -> geojson.FeatureCollection:
    """Get a geojson of all features for a task."""
    project_id = db_project.id

    data_extract_url = db_project.data_extract_url

    if not data_extract_url:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No data extract exists for project ({project_id})",
        )

    # If local debug URL, replace with Docker service name
    data_extract_url = data_extract_url.replace(
        settings.S3_DOWNLOAD_ROOT,
        settings.S3_ENDPOINT,
    )

    with requests.get(data_extract_url) as response:
        if not response.ok:
            msg = f"Download failed for data extract, project ({project_id})"
            log.error(msg)
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=msg,
            )
        log.debug("Converting download flatgeobuf to geojson")
        data_extract_geojson = await flatgeobuf_to_featcol(db, response.content)

    if not data_extract_geojson:
        msg = f"Failed to convert flatgeobuf --> geojson for project ({project_id})"
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    # Split by task areas if task_id provided
    if task_id:
        split_extract_dict = await split_geojson_by_task_areas(
            db, data_extract_geojson, project_id
        )
        return split_extract_dict[task_id]

    return data_extract_geojson


# NOTE defined as non-async to run in separate thread
def generate_project_basemap(
    db: Connection,
    project_id: int,
    org_id: int,
    background_task_id: uuid.UUID,
    source: str,
    output_format: str = "mbtiles",
    tms: Optional[str] = None,
):
    """Get the tiles for a project.

    FIXME waiting on hotosm/basemap-api project to replace this

    Args:
        db (Connection): The database connection.
        project_id (int): ID of project to create tiles for.
        org_id (int): Organisation ID that the project falls within.
        background_task_id (uuid.UUID): UUID of background task to track.
        source (str): Tile source ("esri", "bing", "google", "custom" (tms)).
        output_format (str, optional): Default "mbtiles".
            Other options: "pmtiles", "sqlite3".
        tms (str, optional): Default None. Custom TMS provider URL.
    """
    new_basemap = None

    # TODO update this for user input or automatic
    # maxzoom can be determined from OAM: https://tiles.openaerialmap.org/663
    # c76196049ef00013b8494/0/663c76196049ef00013b8495
    # TODO xy should also be user configurable
    # NOTE mbtile max supported zoom level is 22 (in GDAL at least)
    zooms = "12-22" if tms else "12-19"
    tiles_dir = f"{TILESDIR}/{project_id}"
    outfile = f"{tiles_dir}/{project_id}_{source}tiles.{output_format}"

    # NOTE here we put the connection in autocommit mode to ensure we get
    # background task db entries if there is an exception.
    # The default behaviour is to rollback on exception.
    autocommit_update_sync = async_to_sync(db.set_autocommit)
    autocommit_update_sync(True)

    try:
        sync_basemap_create = async_to_sync(DbBasemap.create)
        new_basemap = sync_basemap_create(
            db,
            project_schemas.BasemapIn(
                project_id=project_id,
                background_task_id=background_task_id,
                status=BackgroundTaskStatus.PENDING,
                tile_source=source,
            ),
        )

        min_lon, min_lat, max_lon, max_lat = new_basemap.bbox

        # Overwrite source with OAM provider
        if tms and "openaerialmap" in tms:
            # NOTE the 'xy' param is set automatically by source=oam
            source = "oam"

        log.debug(
            "Creating basemap with params: "
            f"boundary={min_lon},{min_lat},{max_lon},{max_lat} | "
            f"outfile={outfile} | "
            f"zooms={zooms} | "
            f"outdir={tiles_dir} | "
            f"source={source} | "
            f"tms={tms}"
        )

        create_basemap_file(
            boundary=f"{min_lon},{min_lat},{max_lon},{max_lat}",
            outfile=outfile,
            zooms=zooms,
            outdir=tiles_dir,
            source=source,
            tms=tms,
        )
        log.info(f"Basemap created for project ID {project_id}: {outfile}")

        # Generate S3 urls
        # We parse as BasemapOut to calculated computed fields (format, mimetype)
        basemap_out = project_schemas.BasemapOut(
            **new_basemap.model_dump(exclude=["url"]),
            url=outfile,
        )
        basemap_s3_path = (
            f"{org_id}/{project_id}/basemaps/{basemap_out.id}.{basemap_out.format}"
        )
        log.debug(f"Uploading basemap to S3 path: {basemap_s3_path}")
        add_file_to_bucket(
            settings.S3_BUCKET_NAME,
            basemap_s3_path,
            outfile,
            content_type=basemap_out.mimetype,
        )
        basemap_external_s3_url = (
            f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}/{basemap_s3_path}"
        )
        log.info(f"Upload of basemap to S3 complete: {basemap_external_s3_url}")
        # Delete file on disk
        Path(outfile).unlink(missing_ok=True)

        update_basemap_sync = async_to_sync(DbBasemap.update)
        update_basemap_sync(
            db,
            basemap_out.id,
            project_schemas.BasemapUpdate(
                url=basemap_external_s3_url,
                status=BackgroundTaskStatus.SUCCESS,
            ),
        )

        update_bg_task_sync = async_to_sync(DbBackgroundTask.update)
        update_bg_task_sync(
            db,
            background_task_id,
            project_schemas.BackgroundTaskUpdate(status=BackgroundTaskStatus.SUCCESS),
        )

        log.info(f"Tiles generation process completed for project id {project_id}")

    except Exception as e:
        log.debug(str(format_exc()))
        log.exception(f"Error: {e}", stack_info=True)
        log.error(f"Tiles generation process failed for project id {project_id}")

        if new_basemap:
            update_basemap_sync = async_to_sync(DbBasemap.update)
            update_basemap_sync(
                db,
                new_basemap.id,
                project_schemas.BasemapUpdate(status=BackgroundTaskStatus.FAILED),
            )

        update_bg_task_sync = async_to_sync(DbBackgroundTask.update)
        update_bg_task_sync(
            db,
            background_task_id,
            project_schemas.BackgroundTaskUpdate(
                status=BackgroundTaskStatus.FAILED,
                message=str(e),
            ),
        )


# async def convert_geojson_to_osm(geojson_file: str):
#     """Convert a GeoJSON file to OSM format."""
#     jsonin = JsonDump()
#     geojson_path = Path(geojson_file)
#     data = jsonin.parse(geojson_path)

#     osmoutfile = f"{geojson_path.stem}.osm"
#     jsonin.createOSM(osmoutfile)

#     for entry in data:
#         feature = jsonin.createEntry(entry)

#     # TODO add json2osm back in
#     # https://github.com/hotosm/osm-fieldwork/blob/1a94afff65c4653190d735
#     # f104c0644dcfb71e64/osm_fieldwork/json2osm.py#L363

#     return json2osm(geojson_file)


async def get_pagination(page: int, count: int, results_per_page: int, total: int):
    """Pagination result for splash page."""
    total_pages = (count + results_per_page - 1) // results_per_page
    has_next = (page * results_per_page) < count  # noqa: N806
    has_prev = page > 1  # noqa: N806

    pagination = project_schemas.PaginationInfo(
        has_next=has_next,
        has_prev=has_prev,
        next_num=page + 1 if has_next else None,
        page=page,
        pages=total_pages,
        prev_num=page - 1 if has_prev else None,
        per_page=results_per_page,
        total=total,
    )

    return pagination


async def get_paginated_projects(
    db: Connection,
    page: int,
    results_per_page: int,
    user_id: Optional[int] = None,
    hashtags: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """Helper function to fetch paginated projects with optional filters."""
    if hashtags:
        hashtags = hashtags.split(",")

    # Calculate pagination offsets
    skip = (page - 1) * results_per_page
    limit = results_per_page

    # Get subset of projects
    projects = await DbProject.all(
        db, skip=skip, limit=limit, user_id=user_id, hashtags=hashtags, search=search
    )

    # Count total number of projects for pagination
    async with db.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM projects")
        total_project_count = await cur.fetchone()
        total_project_count = total_project_count[0]

    pagination = await get_pagination(
        page, len(projects), results_per_page, total_project_count
    )

    return {"results": projects, "pagination": pagination}


async def get_project_users_plus_contributions(db: Connection, project_id: int):
    """Get the users and their contributions for a project.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.

    Returns:
        List[Dict[str, Union[str, int]]]: A list of dictionaries containing
            the username and the number of contributions made by each user
            for the specified project.
    """
    query = """
        SELECT
            u.username as user,
            COUNT(th.user_id) as contributions
        FROM
            users u
        JOIN
            task_events th ON u.id = th.user_id
        WHERE
            th.project_id = %(project_id)s
        GROUP BY u.username
        ORDER BY contributions DESC
    """
    async with db.cursor(
        row_factory=class_row(project_schemas.ProjectUserContributions)
    ) as cur:
        await cur.execute(query, {"project_id": project_id})
        return await cur.fetchall()


async def send_project_manager_message(
    request: Request,
    project: DbProject,
    new_manager: DbUser,
    osm_auth: Auth,
):
    """Send message to the new project manager after assigned."""
    log.info(f"Sending message to new project manager ({new_manager.username}).")

    osm_token = get_osm_token(request, osm_auth)
    project_url = f"{settings.FMTM_DOMAIN}/project/{project.id}"
    if not project_url.startswith("http"):
        project_url = f"https://{project_url}"

    message_content = dedent(f"""
        You have been assigned to the project **{project.name}** as a
        manager. You can now manage the project and its tasks.

        [Click here to view the project]({project_url})

        Thank you for being a part of our platform!
    """)

    send_osm_message(
        osm_token=osm_token,
        osm_id=new_manager.id,
        title=f"You have been assigned to project {project.name} as a manager",
        body=message_content,
    )
    log.info(f"Message sent to new project manager ({new_manager.username}).")
