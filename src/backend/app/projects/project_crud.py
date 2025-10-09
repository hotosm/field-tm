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
"""Logic for Field-TM project routes."""

import ast
import importlib
import json
import subprocess
import uuid
from importlib.resources.abc import Traversable
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from traceback import format_exc
from typing import Optional, Union

import aiohttp
import geojson
import geojson_pydantic
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from loguru import logger as log
from osm_data_client import (
    RawDataClient,
    RawDataClientConfig,
    RawDataOutputOptions,
    RawDataResult,
)
from osm_fieldwork.xlsforms.conversion import convert_yaml_to_xlsform
from osm_login_python.core import Auth
from psycopg import Connection, sql
from psycopg.rows import class_row

from app.auth.providers.osm import get_osm_token, send_osm_message
from app.central import central_crud, central_schemas
from app.config import settings
from app.db.enums import BackgroundTaskStatus, HTTPStatus, ProjectStatus, XLSFormType
from app.db.models import DbBackgroundTask, DbBasemap, DbProject, DbUser, DbUserRole
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_single_geom_type,
    featcol_to_flatgeobuf,
    flatgeobuf_to_featcol,
    parse_geojson_file_to_featcol,
    split_geojson_by_task_areas,
)
from app.organisations.organisation_deps import get_default_odk_creds
from app.projects import project_deps, project_schemas
from app.s3 import add_file_to_bucket, add_obj_to_bucket
from app.submissions import submission_crud


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
    project_id: int,
    aoi: geojson.FeatureCollection | geojson.Feature | dict,
    geom_type: str,
    config_json=None,
    centroid: bool = False,
    use_st_within: bool = True,
) -> RawDataResult:
    """Request a new data extract in flatgeobuf format.

    Args:
        project_id (int): Id (primary key) of the project.
        aoi (geojson.FeatureCollection | geojson.Feature | dict]):
            Area of interest for data extraction.
        geom_type (str): Type of geometry to extract.
        config_json (Optional[json], optional):
            Configuration for data extraction. Defaults to None.
        centroid (bool): Generate centroid of polygons.
        use_st_within (bool): Include features within the AOI.

    Raises:
        HTTPException:
            When necessary parameters are missing or data extraction fails.

    Returns:
        str:
            URL for the geojson data extract.
    """
    if not config_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="To generate a new data extract a extract_config must be specified.",
        )
    config = RawDataClientConfig(
        access_token=settings.RAW_DATA_API_AUTH_TOKEN.get_secret_value()
        if settings.RAW_DATA_API_AUTH_TOKEN
        else None
    )
    extra_params = {
        "fileName": (
            f"fmtm_{settings.FMTM_DOMAIN}_data_extract_{project_id}"
            if settings.RAW_DATA_API_AUTH_TOKEN
            else f"fmtm_extract_{project_id}"
        ),
        "outputType": "geojson",
        "geometryType": [geom_type],
        "bindZip": False,
        "centroid": centroid,
        "use_st_within": (False if geom_type == "line" else use_st_within),
        "filters": config_json,
    }

    try:
        result = await RawDataClient(config).get_osm_data(
            aoi,
            output_options=RawDataOutputOptions(download_file=False),
            **extra_params,
        )

        return result
    except Exception as e:
        log.error("Raw data API request failed")
        if "status 406" in str(e) and "Area" in str(e):
            try:
                # Extract the error dict part
                error_str = str(e).split("status 406:")[-1].strip()
                error_dict = ast.literal_eval(error_str)
                msg = error_dict["detail"][0]["msg"]
            except Exception:
                msg = """Selected area is too large.
                Please select an area smaller than 200 km²."""

            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
            ) from e

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Failed to generate data extract from the raw data API.",
        ) from e


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def read_and_insert_xlsforms(
    db: Connection, directory: Union[Traversable, Path]
) -> None:
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
        for file_type in XLSFormType:
            file_name = file_type.name
            form_type = file_type.value

            yaml_resource_path = directory.joinpath(f"{file_name}.yaml")

            if not yaml_resource_path.exists():
                log.warning(f"{yaml_resource_path} does not exist!")
                continue

            try:
                with importlib.resources.as_file(yaml_resource_path) as yaml_filepath:
                    if yaml_filepath.stat().st_size == 0:
                        log.warning(f"{yaml_filepath} is empty!")
                        continue
            except FileNotFoundError:
                log.warning(f"File not found to check size: {yaml_filepath}")
                continue

            try:
                log.info(f"Converting YAMLForm '{yaml_resource_path}' to XLSForm.")
                data = await convert_yaml_to_xlsform(yaml_resource_path)
                log.info(
                    f"Successfully converted from YAMLForm to XLSForm '{file_name}'."
                )
            except Exception as e:
                log.exception(
                    f"Failed to convert YAMLForm '{file_name} to XLSForm'.",
                    f"Error '{e}",
                    stack_info=True,
                )
                continue

            try:
                log.info(
                    f"INSERTING converted XLSForm for '{form_type}' into the database."
                )
                insert_query = """
                    INSERT INTO xlsforms (title, xls)
                    VALUES (%(title)s, %(xls)s)
                    ON CONFLICT (title) DO UPDATE
                    SET xls = EXCLUDED.xls
                """
                # NOTE: The 'xls' column name now stores .xlsx data.
                await cur.execute(insert_query, {"title": form_type, "xls": data})
                log.info(f"XLSForm for '{form_type}' inserted/updated in the database")

            except Exception as e:
                log.exception(
                    f"Failed to insert or update {form_type} in the database. "
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
    # If url passed, get extract
    # If no url passed, get new extract / set in db
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

    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            data_extract_url=url,
        ),
    )

    return url


async def upload_data_extract_to_s3(
    db: Connection,
    project_id: int,
    fgb_content: bytes,
) -> str:
    """Uploads custom data extracts to S3.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.
        fgb_content (bytes): Content of read flatgeobuf file.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    log.debug(f"Uploading custom data extract for project ({project.id})")

    fgb_obj = BytesIO(fgb_content)
    s3_fgb_path = f"{project.organisation_id}/{project_id}/data_extract.fgb"

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
        ),
    )

    return s3_fgb_full_url


async def upload_geojson_data_extract(
    db: Connection,
    project_id: int,
    geojson_raw: Union[str, bytes],
) -> str:
    """Upload a geojson data extract.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.
        geojson_raw (str): The data extracts contents.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await project_deps.get_project_by_id(db, project_id)
    log.debug(f"Uploading data extract for project ({project.id})")

    featcol = parse_geojson_file_to_featcol(geojson_raw)
    featcol_single_geom_type = featcol_keep_single_geom_type(featcol)

    if not featcol_single_geom_type:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Could not process geojson input",
        )

    await check_crs(featcol_single_geom_type)

    log.debug(
        "Generating fgb object from geojson with "
        f"{len(featcol_single_geom_type.get('features', []))} features"
    )
    fgb_data = await featcol_to_flatgeobuf(db, featcol_single_geom_type)

    if not fgb_data:
        msg = f"Failed converting geojson to flatgeobuf for project ({project_id})"
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)

    return await upload_data_extract_to_s3(
        db,
        project_id,
        fgb_data,
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
    task_extract_dict: Optional[dict[int, geojson.FeatureCollection]] = None,
    entity_properties: Optional[list[str]] = None,
) -> str:
    """Populate the project in ODK Central with XForm, Appuser, Permissions."""
    entities_list = []
    if task_extract_dict:
        entities_list = await central_crud.task_geojson_dict_to_entity_values(
            task_extract_dict
        )

    log.debug("Creating project ODK dataset named 'features'")
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
        project_id(int): id of the Field-TM project.
        background_task_id (uuid): the task_id of the background task.
        db (Connection): The database connection, newly generated.

    Returns:
        bool: True if success.
    """
    try:
        project = await project_deps.get_project_by_id(db, project_id)
        geom_type = project.primary_geom_type
        log.info(f"Starting generate_project_files for project {project_id}")

        # Extract data extract from flatgeobuf
        log.debug("Getting data extract geojson from flatgeobuf")
        feature_collection = await get_project_features_geojson(db, project)

        first_feature = next(
            iter(feature_collection.get("features", [])), {}
        )  # Get first feature or {}

        if first_feature and "properties" in first_feature:  # Check if properties exist
            # FIXME perhaps this should be done in the SQL code?
            entity_properties = list(first_feature["properties"].keys())
            for field in ["submission_ids", "created_by"]:
                if field not in entity_properties:
                    entity_properties.append(field)

            log.debug("Splitting data extract per task area")
            # TODO in future this splitting could be removed if the task_id is
            # no longer used in the XLSForm for the map filter
            task_extract_dict = await split_geojson_by_task_areas(
                db, feature_collection, project_id, geom_type
            )
        else:
            # NOTE the entity properties are generated by the form `save_to` field
            # NOTE automatically anyway
            entity_properties = []
            task_extract_dict = {}

        # Get ODK Project details
        project_odk_id = project.odkid
        project_xlsform = project.xlsform_content
        project_odk_form_id = project.odk_form_id
        project_odk_creds = project.odk_credentials

        if not project_odk_creds:
            # get default credentials
            project_odk_creds = await get_default_odk_creds()

        odk_token = await generate_odk_central_project_content(
            project_odk_id,
            project_odk_form_id,
            project_odk_creds,
            BytesIO(project_xlsform),
            task_extract_dict,
            entity_properties,
        )
        # Run separate thread in event loop to avoid blocking with sync code
        # Copy the parsed form XML into the FieldTM db for easy easy
        form_xml = await run_in_threadpool(
            central_crud.get_project_form_xml,
            project_odk_creds,
            project_odk_id,
            project_odk_form_id,
        )

        log.debug(
            f"Setting encrypted odk token for Field-TM project ({project_id}) "
            f"ODK project {project_odk_id}: {type(odk_token)} ({odk_token[:15]}...)"
        )
        await DbProject.update(
            db,
            project_id,
            project_schemas.ProjectUpdate(
                odk_token=odk_token,
                odk_form_xml=form_xml,
            ),
        )
        task_feature_counts = [
            (
                task.id,
                len(
                    task_extract_dict.get(task.project_task_index, {}).get(
                        "features", []
                    )
                ),
            )
            for task in project.tasks
        ]

        # Use parameterized batch update
        update_data = [
            (task_id, feature_count) for task_id, feature_count in task_feature_counts
        ]

        async with db.cursor() as cur:
            await cur.executemany(
                sql.SQL("UPDATE public.tasks SET feature_count = %s WHERE id = %s"),
                [(fc, tid) for tid, fc in update_data],
            )
        return True
    except Exception as e:
        log.debug(str(format_exc()))
        log.exception(
            f"Error generating project files for project {project_id}: {e}",
            stack_info=True,
        )
        return False


async def get_task_geometry(db: Connection, project_id: int):
    """Retrieves the geometry of tasks associated with a project.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """
    query = """
        SELECT project_task_index,
        ST_AsGeoJSON(tasks.outline)::jsonb AS outline
        FROM tasks
        WHERE project_id = %(project_id)s
    """
    async with db.cursor(row_factory=class_row(dict)) as cur:
        await cur.execute(query, {"project_id": project_id})
        db_tasks = await cur.fetchall()

    if not db_tasks:
        raise ValueError(f"No tasks found for project ID {project_id}.")

    features = [
        {
            "type": "Feature",
            "geometry": task["outline"],
            "properties": {"task_id": task["project_task_index"]},
        }
        for task in db_tasks
        if task["outline"]  # Exclude tasks with no geometry
    ]

    feature_collection = {"type": "FeatureCollection", "features": features}
    return json.dumps(feature_collection)


async def get_project_features_geojson(
    db: Connection,
    db_project: DbProject,
    task_id: Optional[int] = None,
) -> geojson.FeatureCollection:
    """Get a geojson of all features for a task."""
    project_id = db_project.id
    geom_type = db_project.primary_geom_type

    data_extract_url = db_project.data_extract_url

    if not data_extract_url:
        # raise HTTPException(
        #     status_code=HTTPStatus.NOT_FOUND,
        #     detail=f"No data extract exists for project ({project_id})",
        # )
        # Return an empty featcol for projects with no existing features
        return {"type": "FeatureCollection", "features": []}

    # If local debug URL, replace with Docker service name
    data_extract_url = data_extract_url.replace(
        settings.S3_DOWNLOAD_ROOT,
        settings.S3_ENDPOINT,
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(data_extract_url) as response:
            if not response.ok:
                msg = f"Download failed for data extract, project ({project_id})"
                log.error(msg)
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail=msg,
                )

            log.debug("Converting FlatGeobuf to GeoJSON")
            data_extract_geojson = await flatgeobuf_to_featcol(
                db, await response.read()
            )

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
            db, data_extract_geojson, project_id, geom_type
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
    mbtiles_file = ""
    final_tile_file = ""

    # TODO update this for user input or automatic
    # maxzoom can be determined from OAM: https://tiles.openaerialmap.org/663
    # c76196049ef00013b8494/0/663c76196049ef00013b8495
    # TODO should inverted_y be user configurable?

    # NOTE mbtile max supported zoom level is 22 (in GDAL at least)
    if tms:
        zooms = "12-22"
    # While typically satellite imagery TMS only goes to zoom 19
    else:
        zooms = "12-19"

    mbtiles_file = Path(f"/tmp/{project_id}_{source}tiles.mbtiles")

    # Set URL based on source (previously in osm-fieldwork)
    if source == "esri":
        # ESRI uses inverted zyx convention
        # the ordering is extracted automatically from the URL, else use
        # -inverted-y param
        tms_url = "http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png"
        tile_format = "png"
    elif source == "bing":
        # FIXME this probably doesn't work
        tms_url = "http://ecn.t0.tiles.virtualearth.net/tiles/h{z}/{x}/{y}.jpg?g=129&mkt=en&stl=H"
        tile_format = "jpg"
    elif source == "google":
        tms_url = "https://mt0.google.com/vt?lyrs=s&x={x}&y={y}&z={z}"
        tile_format = "jpg"
    elif source == "custom" and tms:
        tms_url = tms
        if not (tile_format := Path(tms_url).suffix.lstrip(".")):
            # Default to png if suffix not included in URL
            tile_format = "png"
    else:
        raise ValueError("Must select a source from: esri,bing,google,custom")

    # Invert zxy --> zyx for OAM provider
    # inverted_y = True if tms and "openaerialmap" in tms else False
    # NOTE the xy ordering is determined from the URL placeholders, by tilepack!
    inverted_y = False

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

        tilepack_cmd = [
            # "prlimit", f"--as={500 * 1000}", "--",
            "tilepack",
            "-dsn",
            f"{str(mbtiles_file)}",
            "-url-template",
            f"{tms_url}",
            # tilepack requires format: south,west,north,east
            "-bounds",
            f"{min_lat},{min_lon},{max_lat},{max_lon}",
            "-zooms",
            f"{zooms}",
            "-output-mode",
            "mbtiles",  # options: mbtiles or disk
            "-mbtiles-format",
            f"{tile_format}",
            "-tileset-name",
            f"fmtm_{project_id}_{source}tiles",
        ]
        # Add '-inverted-y' only if needed
        if inverted_y:
            tilepack_cmd.append("-inverted-y")
        log.debug(
            "Creating basemap mbtiles using tilepack with command: "
            f"{' '.join(tilepack_cmd)}"
        )
        subprocess.run(tilepack_cmd, check=True)
        log.info(
            f"MBTile basemap created for project ID {project_id}: {str(mbtiles_file)}"
        )
        # write to another var so we upload either mbtiles OR pmtiles override below
        final_tile_file = str(mbtiles_file)

        if output_format == "pmtiles":
            pmtiles_file = mbtiles_file.with_suffix(".pmtiles")
            pmtile_command = [
                # "prlimit", f"--as={500 * 1000}", "--",
                "pmtiles",
                "convert",
                f"{str(mbtiles_file)}",
                f"{str(pmtiles_file)}",
            ]
            log.debug(
                "Converting mbtiles --> pmtiles file with command: "
                f"{' '.join(pmtile_command)}"
            )
            subprocess.run(pmtile_command, check=True)
            log.info(
                f"PMTile basemap created for project ID {project_id}: "
                f"{str(pmtiles_file)}"
            )
            final_tile_file = str(pmtiles_file)

        # Generate S3 urls
        # We parse as BasemapOut to calculated computed fields (format, mimetype)
        basemap_out = project_schemas.BasemapOut(
            **new_basemap.model_dump(exclude=["url"]),
            url=final_tile_file,
        )
        basemap_s3_path = (
            f"{org_id}/{project_id}/basemaps/{basemap_out.id}.{basemap_out.format}"
        )
        log.debug(f"Uploading basemap to S3 path: {basemap_s3_path}")
        add_file_to_bucket(
            settings.S3_BUCKET_NAME,
            basemap_s3_path,
            final_tile_file,
            content_type=basemap_out.mimetype,
        )
        basemap_external_s3_url = (
            f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}/{basemap_s3_path}"
        )
        log.info(f"Upload of basemap to S3 complete: {basemap_external_s3_url}")

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
    finally:
        Path(mbtiles_file).unlink(missing_ok=True)
        Path(final_tile_file).unlink(missing_ok=True)
        log.debug("Cleaning up tile archives on disk")


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
    total_pages = (total + results_per_page - 1) // results_per_page
    has_next = (page * results_per_page) < total  # noqa: N806
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
    current_user: Optional[str] = None,
    org_id: Optional[int] = None,
    user_sub: Optional[str] = None,
    hashtags: Optional[str] = None,
    search: Optional[str] = None,
    minimal: bool = False,
    status: Optional[ProjectStatus] = None,
) -> dict:
    """Helper function to fetch paginated projects with optional filters."""
    if hashtags:
        hashtags = hashtags.split(",")

    # Get subset of projects
    projects = await DbProject.all(
        db,
        current_user=current_user,
        org_id=org_id,
        user_sub=user_sub,
        hashtags=hashtags,
        search=search,
        minimal=minimal,
        status=status,
    )
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    paginated_projects = projects[start_index:end_index]

    pagination = await get_pagination(
        page, len(paginated_projects), results_per_page, len(projects)
    )

    return {"results": paginated_projects, "pagination": pagination}


async def get_project_users_plus_contributions(db: Connection, project_id: int):
    """Get the users and their number of submissions for a project.

    Args:
        db (Connection): The database connection.
        project_id (int): The ID of the project.

    Returns:
        List[Dict[str, Union[str, int]]]: A list of dictionaries containing
            the username and the number of submissions made by each user
            for the specified project.
    """
    try:
        project = await DbProject.one(db, project_id, minimal=False)

        # Fetch all submissions for the project
        data = await submission_crud.get_submission_by_project(project, {})
        submissions = data.get("value", [])

        # Count submissions per user
        submission_counts = {}
        for sub in submissions:
            username = sub.get("username")
            if "|" in username:
                user = await DbUser.one(db, user_subidentifier=username)
                username = user.username if user else username
            if username:
                submission_counts[username] = submission_counts.get(username, 0) + 1

        # Format as list of dicts, sorted by count desc
        result = [
            {"user": user, "submissions": count}
            for user, count in sorted(
                submission_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]
        return result
    except Exception as e:
        log.error(f"Error in get_project_users_plus_contributions: {e}")
        return []


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
        osm_sub=new_manager.sub,
        title=f"You have been assigned to project {project.name} as a manager",
        body=message_content,
    )
    log.info(f"Message sent to new project manager ({new_manager.username}).")


async def unassign_user_from_project(db, project_id, user_sub):
    """Unassigns a user from a project by removing their role.

    Args:
        db: Database session or connection.
        project_id: ID of the project.
        user_sub: Unique user identifier.

    Returns:
        bool: True if the user was successfully unassigned.

    Raises:
        HTTPException (404): If the user is not associated with the project.
    """
    try:
        user_role = await DbUserRole.get(db, project_id, user_sub)
        if not user_role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User {user_sub} is not associated with project {project_id}.",
            )
        return await DbUserRole.delete(db, project_id, user_sub)
    except Exception as e:
        log.exception(f"Failed to unassign user {user_sub} from project {project_id}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to unassign user {user_sub} from project {project_id}",
        ) from e
