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
import os
import subprocess
import uuid
from asyncio import gather
from importlib.resources import files as pkg_files
from io import BytesIO
from typing import List, Optional, Union

import geoalchemy2
import geojson
import requests
import shapely.wkb as wkblib
import sozipfile.sozipfile as zipfile
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from fmtm_splitter.splitter import split_by_sql, split_by_square
from geoalchemy2.shape import to_shape
from geojson.feature import Feature, FeatureCollection
from loguru import logger as log
from osm_fieldwork.basemapper import create_basemap_file
from osm_fieldwork.json2osm import json2osm
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_fieldwork.OdkCentralAsync import OdkEntity
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.xlsforms.entities import registration_form
from osm_rawdata.postgres import PostgresClient
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union
from sqlalchemy import and_, column, func, inspect, select, table, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.central import central_crud
from app.config import encrypt_value, settings
from app.db import db_models
from app.db.postgis_utils import (
    check_crs,
    flatgeobuf_to_geojson,
    geojson_to_flatgeobuf,
    geometry_to_geojson,
    get_address_from_lat_lon_async,
    get_featcol_main_geom_type,
    parse_and_filter_geojson,
    split_geojson_by_task_areas,
    task_geojson_dict_to_entity_values,
)
from app.models.enums import HTTPStatus, ProjectRole, ProjectVisibility
from app.projects import project_deps, project_schemas
from app.s3 import add_obj_to_bucket, get_obj_from_bucket
from app.tasks import tasks_crud
from app.users import user_crud

TILESDIR = "/opt/tiles"


async def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    hashtags: Optional[List[str]] = None,
    search: Optional[str] = None,
):
    """Get all projects, or a filtered subset."""
    filters = []

    if user_id:
        filters.append(db_models.DbProject.author_id == user_id)

    if hashtags:
        filters.append(db_models.DbProject.hashtags.op("&&")(hashtags))  # type: ignore

    if search:
        filters.append(
            db_models.DbProject.project_info.has(
                db_models.DbProjectInfo.name.ilike(f"%{search}%")
            )
        )

    if len(filters) > 0:
        db_projects = (
            db.query(db_models.DbProject)
            .filter(and_(*filters))
            .order_by(db_models.DbProject.id.desc())  # type: ignore
            .offset(skip)
            .limit(limit)
            .all()
        )
        project_count = db.query(db_models.DbProject).filter(and_(*filters)).count()

    else:
        db_projects = (
            db.query(db_models.DbProject)
            .filter(
                db_models.DbProject.visibility  # type: ignore
                == ProjectVisibility.PUBLIC  # type: ignore
            )
            .order_by(db_models.DbProject.id.desc())  # type: ignore
            .offset(skip)
            .limit(limit)
            .all()
        )
        project_count = db.query(db_models.DbProject).count()

    filtered_projects = await convert_to_app_projects(db_projects)
    return project_count, filtered_projects


async def get_projects_featcol(
    db: Session,
    bbox: Optional[str] = None,
) -> geojson.FeatureCollection:
    """Get all projects, or a filtered subset."""
    bbox_condition = (
        """AND ST_Intersects(
            p.outline, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)
        )"""
        if bbox
        else ""
    )

    bbox_params = {}
    if bbox:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
        bbox_params = {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}

    query = text(
        f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(feature), '[]'::jsonb)
        ) AS featcol
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'id', p.id,
                'geometry', ST_AsGeoJSON(p.outline)::jsonb,
                'properties', jsonb_build_object(
                    'name', pi.name,
                    'percentMapped', 0,
                    'percentValidated', 0,
                    'created', p.created,
                    'link', concat('https://', :domain, '/project/', p.id)
                )
            ) AS feature
            FROM projects p
            LEFT JOIN project_info pi ON p.id = pi.project_id
            WHERE p.visibility = 'PUBLIC'
            {bbox_condition}
        ) features;
        """
    )

    result = db.execute(query, {"domain": settings.FMTM_DOMAIN, **bbox_params})
    featcol = result.scalar_one()

    return featcol


async def get_project_summaries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    hashtags: Optional[List[str]] = None,
    search: Optional[str] = None,
):
    """Get project summary details for main page."""
    project_count, db_projects = await get_projects(
        db, skip, limit, user_id, hashtags, search
    )
    return project_count, await convert_to_project_summaries(db_projects)


async def get_project(db: Session, project_id: int):
    """Get a single project."""
    db_project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )
    if not db_project:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Project with id {project_id} does not exist",
        )
    return db_project


async def get_project_by_id(db: Session, project_id: int):
    """Get a single project by id."""
    db_project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )
    return await convert_to_app_project(db_project)


async def get_project_info_by_id(db: Session, project_id: int):
    """Get the project info only by id."""
    db_project_info = (
        db.query(db_models.DbProjectInfo)
        .filter(db_models.DbProjectInfo.project_id == project_id)
        .order_by(db_models.DbProjectInfo.project_id)
        .first()
    )
    return await convert_to_app_project_info(db_project_info)


async def delete_one_project(db: Session, db_project: db_models.DbProject) -> None:
    """Delete a project by id."""
    try:
        project_id = db_project.id
        db.delete(db_project)
        db.commit()
        log.info(f"Deleted project with ID: {project_id}")
    except Exception as e:
        log.exception(e)
        raise HTTPException(e) from e


async def partial_update_project_info(
    db: Session,
    project_metadata: project_schemas.ProjectPartialUpdate,
    db_project: db_models.DbProject,
):
    """Partial project update for PATCH."""
    # Get project info
    db_project_info = await get_project_info_by_id(db, db_project.id)

    # Update project informations
    if db_project and db_project_info:
        if project_metadata.name:
            db_project.project_name_prefix = project_metadata.project_name_prefix
            db_project_info.name = project_metadata.name
        if project_metadata.description:
            db_project_info.description = project_metadata.description
        if project_metadata.short_description:
            db_project_info.short_description = project_metadata.short_description
        if project_metadata.per_task_instructions:
            db_project_info.per_task_instructions = (
                project_metadata.per_task_instructions
            )
        if project_metadata.hashtags:
            db_project.hashtags = project_metadata.hashtags

    db.commit()
    db.refresh(db_project)

    return await convert_to_app_project(db_project)


async def update_project_info(
    db: Session,
    project_metadata: project_schemas.ProjectUpdate,
    db_project: db_models.DbProject,
    db_user: db_models.DbUser,
):
    """Full project update for PUT."""
    project_info = project_metadata.project_info

    if not project_info:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="No project info passed in",
        )

    # Project meta informations
    project_info = project_metadata.project_info

    # Update author of the project
    db_project.author_id = db_user.id
    db_project.project_name_prefix = project_metadata.project_name_prefix

    # get project info
    db_project_info = await get_project_info_by_id(db, db_project.id)

    # Update projects meta informations (name, descriptions)
    if db_project and db_project_info:
        db_project_info.name = project_info.name
        db_project_info.short_description = project_info.short_description
        db_project_info.description = project_info.description

    db.commit()
    db.refresh(db_project)

    return await convert_to_app_project(db_project)


async def create_project_with_project_info(
    db: Session,
    project_metadata: project_schemas.ProjectUpload,
    odk_project_id: int,
    current_user: db_models.DbUser,
):
    """Create a new project, including all associated info."""
    if not odk_project_id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="ODK Central project id is missing",
        )

    log.debug(
        "Creating project in FMTM database with vars: "
        f"project_user: {current_user.username} | "
        f"project_name: {project_metadata.project_info.name} | "
        f"xform_category: {project_metadata.xform_category} | "
        f"hashtags: {project_metadata.hashtags} | "
        f"organisation_id: {project_metadata.organisation_id}"
    )

    # Extract project_info details, then remove key
    project_name = project_metadata.project_info.name
    project_description = project_metadata.project_info.description
    project_short_description = project_metadata.project_info.short_description
    project_instructions = project_metadata.project_info.per_task_instructions

    # create new project
    db_project = db_models.DbProject(
        author_id=current_user.id,
        odkid=odk_project_id,
        **project_metadata.model_dump(exclude=["project_info", "outline_geojson"]),
    )
    db.add(db_project)

    # add project info (project id needed to create project info)
    db_project_info = db_models.DbProjectInfo(
        project=db_project,
        name=project_name,
        short_description=project_short_description,
        description=project_description,
        per_task_instructions=project_instructions,
    )
    db.add(db_project_info)

    db.commit()
    db.refresh(db_project)

    return await convert_to_app_project(db_project)


async def create_tasks_from_geojson(
    db: Session,
    project_id: int,
    boundaries: str,
):
    """Create tasks for a project, from provided task boundaries."""
    try:
        if isinstance(boundaries, str):
            boundaries = json.loads(boundaries)

        # Update the boundary polyon on the database.
        if boundaries["type"] == "Feature":
            polygons = [boundaries]
        else:
            polygons = boundaries["features"]
        log.debug(f"Processing {len(polygons)} task geometries")
        for index, polygon in enumerate(polygons):
            # If the polygon is a MultiPolygon, convert it to a Polygon
            if polygon["geometry"]["type"] == "MultiPolygon":
                log.debug("Converting MultiPolygon to Polygon")
                polygon["geometry"]["type"] = "Polygon"
                polygon["geometry"]["coordinates"] = polygon["geometry"]["coordinates"][
                    0
                ]

            db_task = db_models.DbTask(
                project_id=project_id,
                outline=wkblib.dumps(shape(polygon["geometry"]), hex=True),
                project_task_index=index,
            )
            db.add(db_task)
            log.debug(
                "Created database task | "
                f"Project ID {project_id} | "
                f"Task index {index}"
            )

        # Commit all tasks and update project location in db
        db.commit()

        log.debug("COMPLETE: creating project boundary, based on task boundaries")

        return True
    except Exception as e:
        log.exception(e)
        raise HTTPException(e) from e


async def preview_split_by_square(boundary: str, meters: int):
    """Preview split by square for a project boundary.

    Use a lambda function to remove the "z" dimension from each
    coordinate in the feature's geometry.
    """

    def remove_z_dimension(coord):
        """Remove z dimension from geojson."""
        return coord.pop() if len(coord) == 3 else None

    """ Check if the boundary is a Feature or a FeatureCollection """
    if boundary["type"] == "Feature":
        features = [boundary]
    elif boundary["type"] == "FeatureCollection":
        features = boundary["features"]
    elif boundary["type"] == "Polygon":
        features = [
            {
                "type": "Feature",
                "properties": {},
                "geometry": boundary,
            }
        ]
    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid GeoJSON type: {boundary['type']}"
        )

    # Apply the lambda function to each coordinate in its geometry
    # to remove the z-dimension - if it exists
    multi_polygons = []
    for feature in features:
        list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))
        if feature["geometry"]["type"] == "MultiPolygon":
            multi_polygons.append(Polygon(feature["geometry"]["coordinates"][0][0]))

    # Merge multiple geometries into single polygon
    if multi_polygons:
        merged_polygon = unary_union(multi_polygons)
        if isinstance(merged_polygon, MultiPolygon):
            merged_polygon = merged_polygon.convex_hull
        merged_geojson = mapping(merged_polygon)
        features = [
            {
                "type": "Feature",
                "properties": {},
                "geometry": merged_geojson,
            }
        ]
        boundary["features"] = features

    return await run_in_threadpool(
        lambda: split_by_square(
            boundary,
            meters=meters,
        )
    )


async def generate_data_extract(
    aoi: Union[FeatureCollection, Feature, dict],
    extract_config: Optional[BytesIO] = None,
) -> str:
    """Request a new data extract in flatgeobuf format.

    Args:
        db (Session):
            Database session.
        aoi (Union[FeatureCollection, Feature, dict]):
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
        auth_token=settings.OSM_SVC_ACCOUNT_TOKEN
        if settings.OSM_SVC_ACCOUNT_TOKEN
        else None,
    )
    fgb_url = pg.execQuery(
        aoi,
        extra_params={
            "fileName": (
                f"fmtm/{settings.FMTM_DOMAIN}/data_extract"
                if settings.OSM_SVC_ACCOUNT_TOKEN
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


async def split_geojson_into_tasks(
    db: Session,
    project_geojson: Union[dict, FeatureCollection],
    no_of_buildings: int,
    extract_geojson: Optional[FeatureCollection] = None,
):
    """Splits a project into tasks.

    Args:
        db (Session): A database session.
        project_geojson (Union[dict, FeatureCollection]): A GeoJSON of the project
            boundary.
        extract_geojson (Union[dict, FeatureCollection]): A GeoJSON of the project
            boundary osm data extract (features).
        extract_geojson (FeatureCollection): A GeoJSON of the project
            boundary osm data extract (features).
            If not included, an extract is generated automatically.
        no_of_buildings (int): The number of buildings to include in each task.

    Returns:
        Any: A GeoJSON object containing the tasks for the specified project.
    """
    log.debug("STARTED task splitting using provided boundary and data extract")
    features = await run_in_threadpool(
        lambda: split_by_sql(
            project_geojson,
            db,
            num_buildings=no_of_buildings,
            osm_extract=extract_geojson,
        )
    )
    log.debug("COMPLETE task splitting")
    return features


async def update_project_boundary(
    db: Session, project_id: int, boundary: str, meters: int
):
    """Update the boundary for a project and update tasks.

    TODO this needs a big refactor or removal
    #
    """
    # verify project exists in db
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        log.error(f"Project {project_id} doesn't exist!")
        return False

    # Use a lambda function to remove the "z" dimension from each
    # coordinate in the feature's geometry
    def remove_z_dimension(coord):
        """Remove the z dimension from a geojson."""
        return coord.pop() if len(coord) == 3 else None

    """ Check if the boundary is a Feature or a FeatureCollection """
    if boundary["type"] == "Feature":
        features = [boundary]
    elif boundary["type"] == "FeatureCollection":
        features = boundary["features"]
    elif boundary["type"] == "Polygon":
        features = [
            {
                "type": "Feature",
                "properties": {},
                "geometry": boundary,
            }
        ]
    else:
        # Raise an exception
        raise HTTPException(
            status_code=400, detail=f"Invalid GeoJSON type: {boundary['type']}"
        )

    """ Apply the lambda function to each coordinate in its geometry """
    multi_polygons = []
    for feature in features:
        list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))
        if feature["geometry"]["type"] == "MultiPolygon":
            multi_polygons.append(Polygon(feature["geometry"]["coordinates"][0][0]))

    """Update the boundary polygon on the database."""
    if multi_polygons:
        outline = multi_polygons[0]
        for geom in multi_polygons[1:]:
            outline = outline.union(geom)
    else:
        outline = shape(features[0]["geometry"])

    centroid = (wkt.loads(outline.wkt)).centroid.wkt
    db_project.centroid = centroid
    geometry = wkt.loads(centroid)
    longitude, latitude = geometry.x, geometry.y
    address = await get_address_from_lat_lon_async(latitude, longitude)
    db_project.location_str = address if address is not None else ""

    db.commit()
    db.refresh(db_project)
    log.debug("Finished updating project boundary")

    log.debug("Splitting tasks")
    tasks = split_by_square(
        boundary,
        meters=meters,
    )
    for index, poly in enumerate(tasks["features"]):
        db_task = db_models.DbTask(
            project_id=project_id,
            outline=wkblib.dumps(shape(poly["geometry"]), hex=True),
            # qr_code=db_qr,
            # qr_code_id=db_qr.id,
            # project_task_index=feature["properties"]["fid"],
            project_task_index=index,
            # geometry_geojson=geojson.dumps(task_geojson),
            # feature_count=len(task_geojson["features"]),
        )
        db.add(db_task)
        db.commit()
    return True


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def read_xlsforms(
    db: Session,
    directory: str,
):
    """Read the list of XLSForms from the disk."""
    xlsforms = list()
    package_name = "osm_fieldwork"
    package_files = pkg_files(package_name)
    for xls in os.listdir(directory):
        if xls.endswith(".xls") or xls.endswith(".xlsx"):
            file_name = xls.split(".")[0]
            yaml_file_name = f"data_models/{file_name}.yaml"
            if package_files.joinpath(yaml_file_name).is_file():
                xlsforms.append(xls)
            else:
                continue

    inspect(db_models.DbXLSForm)
    forms = table(
        "xlsforms", column("title"), column("xls"), column("xml"), column("id")
    )
    # x = Table('xlsforms', MetaData())
    # x.primary_key.columns.values()

    for xlsform in xlsforms:
        infile = f"{directory}/{xlsform}"
        if os.path.getsize(infile) <= 0:
            log.warning(f"{infile} is empty!")
            continue
        xls = open(infile, "rb")
        name = xlsform.split(".")[0]
        data = xls.read()
        xls.close()
        # log.info(xlsform)
        ins = insert(forms).values(title=name, xls=data)
        sql = ins.on_conflict_do_update(
            constraint="xlsforms_title_key", set_=dict(title=name, xls=data)
        )
        db.execute(sql)
        db.commit()

    return xlsforms


async def get_odk_id_for_project(db: Session, project_id: int):
    """Get the odk project id for the fmtm project id."""
    project = table(
        "projects",
        column("odkid"),
    )

    where = f"id={project_id}"
    sql = select(project).where(text(where))
    log.info(str(sql))
    result = db.execute(sql)

    # There should only be one match
    if result.rowcount != 1:
        log.warning(str(sql))
        return False
    project_info = result.first()
    return project_info.odkid


async def get_or_set_data_extract_url(
    db: Session,
    project_id: int,
    url: Optional[str],
) -> str:
    """Get or set the data extract URL for a project.

    Args:
        db (Session): SQLAlchemy database session.
        project_id (int): The ID of the project.
        url (str): URL to the streamable flatgeobuf data extract.
            If not passed, a new extract is generated.

    Returns:
        str: URL to fgb file in S3.
    """
    db_project = await get_project_by_id(db, project_id)
    if not db_project:
        msg = f"Project ({project_id}) not found"
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg)

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

    # FIXME Identify data extract type from form type
    # FIXME use mapping e.g. building=polygon, waterways=line, etc
    extract_type = "polygon"

    await update_data_extract_url_in_db(db, db_project, url, extract_type)

    return url


async def update_data_extract_url_in_db(
    db: Session, project: db_models.DbProject, url: str, extract_type: str
):
    """Update the data extract params in the database for a project."""
    log.debug(f"Setting data extract URL for project ({project.id}): {url}")
    project.data_extract_url = url
    project.data_extract_type = extract_type
    db.commit()


async def upload_custom_extract_to_s3(
    db: Session,
    project_id: int,
    fgb_content: bytes,
    data_extract_type: str,
) -> str:
    """Uploads custom data extracts to S3.

    Args:
        db (Session): SQLAlchemy database session.
        project_id (int): The ID of the project.
        fgb_content (bytes): Content of read flatgeobuf file.
        data_extract_type (str): centroid/polygon/line for database.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await get_project(db, project_id)
    log.debug(f"Uploading custom data extract for project: {project}")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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

    await update_data_extract_url_in_db(db, project, s3_fgb_full_url, data_extract_type)

    return s3_fgb_full_url


async def upload_custom_fgb_extract(
    db: Session,
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
        db (Session): SQLAlchemy database session.
        project_id (int): The ID of the project.
        fgb_content (bytes): Content of read flatgeobuf file.

    Returns:
        str: URL to fgb file in S3.
    """
    featcol = await flatgeobuf_to_geojson(db, fgb_content)

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


async def get_data_extract_type(featcol: FeatureCollection) -> str:
    """Determine predominant geometry type for extract."""
    geom_type = get_featcol_main_geom_type(featcol)
    if geom_type not in ["Polygon", "Polyline", "Point"]:
        msg = (
            "Extract does not contain valid geometry types, from 'Polygon' "
            ", 'Polyline' and 'Point'."
        )
        log.error(msg)
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)
    geom_name_map = {
        "Polygon": "polygon",
        "Point": "centroid",
        "Polyline": "line",
    }
    data_extract_type = geom_name_map.get(geom_type, "polygon")

    return data_extract_type


async def upload_custom_geojson_extract(
    db: Session,
    project_id: int,
    geojson_raw: Union[str, bytes],
) -> str:
    """Upload a geojson data extract.

    Args:
        db (Session): SQLAlchemy database session.
        project_id (int): The ID of the project.
        geojson_raw (str): The custom data extracts contents.

    Returns:
        str: URL to fgb file in S3.
    """
    project = await get_project(db, project_id)
    log.debug(f"Uploading custom data extract for project: {project}")

    featcol_filtered = parse_and_filter_geojson(geojson_raw)
    if not featcol_filtered:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Could not process geojson input",
        )

    await check_crs(featcol_filtered)

    data_extract_type = await get_data_extract_type(featcol_filtered)

    log.debug(
        "Generating fgb object from geojson with "
        f"{len(featcol_filtered.get('features', []))} features"
    )
    fgb_data = await geojson_to_flatgeobuf(db, featcol_filtered)

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


async def generate_project_files(
    db: Session,
    project_id: int,
    custom_form: Optional[BytesIO],
    form_category: str,
    form_file_ext: str,
    background_task_id: Optional[uuid.UUID] = None,
):
    """Generate the files for a project.

    QR code, new XForm, and the OSM data extract.

    Parameters:
        - db: the database session
        - project_id: Project ID
        - custom_form: the xls file to upload if we have a custom form
        - form_category: the category for the custom XLS form
        - form_file_ext: weather the form is xls, xlsx or xml
        - background_task_id: the task_id of the background task running this function.
    """
    try:
        log.info(f"Starting generate_project_files for project {project_id}")

        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Project with id {project_id} does not exist",
            )

        odk_credentials = await project_deps.get_odk_credentials(db, project_id)

        if custom_form:
            log.debug("User provided custom XLSForm")
            xlsform = custom_form
        else:
            log.debug(f"Using default XLSForm for category: '{form_category}'")

            xlsform_path = f"{xlsforms_path}/{form_category}.xls"
            with open(xlsform_path, "rb") as f:
                xlsform = BytesIO(f.read())

        # Extract data extract from flatgeobuf
        log.debug("Getting data extract geojson from flatgeobuf")
        feature_collection = await get_project_features_geojson(db, project)

        # Split extract by task area
        log.debug("Splitting data extract per task area")
        task_extract_dict = await split_geojson_by_task_areas(
            db, feature_collection, project_id
        )

        if not task_extract_dict:
            log.warning(f"Project ({project_id}) failed splitting tasks")
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Failed splitting extract by tasks.",
            )

        # Get project name for XForm name
        project_name = project.project_name_prefix
        # Get ODK Project ID
        project_odk_id = project.odkid

        # Create an app user (i.e. QR Code) for the project
        log.info(
            f"Creating odkcentral app user ({project_name}) "
            f"for FMTM project ({project_id})"
        )
        appuser = OdkAppUser(
            odk_credentials.odk_central_url,
            odk_credentials.odk_central_user,
            odk_credentials.odk_central_password,
        )
        appuser_json = appuser.create(project_odk_id, project_name)

        # If app user could not be created, raise an exception.
        if not appuser_json:
            log.error(f"Couldn't create appuser {project_name} for project")
            return False
        if not (appuser_token := appuser_json.get("token")):
            log.error(f"Couldn't get token for appuser {project_name}")
            return False
        appuser_id = appuser_json.get("id")

        # First upload entity registration form
        with open(registration_form, "rb") as f:
            reg_form_bytes = BytesIO(f.read())
        # Convert XLSForm --> XForm
        registration_form_data = await central_crud.read_and_test_xform(
            reg_form_bytes, "xls", return_form_data=True
        )
        # Update fields in XML
        updated_reg_xform = await central_crud.update_entity_registration_xform(
            registration_form_data, form_category
        )
        # Upload entity registration XForm
        log.info("Uploading Entity registration XForm to ODK Central")
        central_crud.create_odk_xform(
            project_odk_id,
            updated_reg_xform,
            odk_credentials,
        )

        # TODO in the future we may possibly support multiple forms per project.
        # TODO to faciliate this we need to add the _{form_category} suffix and track.
        # TODO this in the new xforms.category field/table.
        xform_name_to_inject = project_name
        task_ids = task_extract_dict.keys()
        # Convert XLSForm --> XForm
        xform_data = await central_crud.read_and_test_xform(
            xlsform, form_file_ext, return_form_data=True
        )
        # This is where the ODK form name is set
        updated_xform = await central_crud.update_survey_xform(
            xform_data,
            xform_name_to_inject,
            form_category,
            task_ids,
        )
        # Upload survey XForm
        log.info("Uploading survey XForm to ODK Central")
        xform_name = central_crud.create_odk_xform(
            project_odk_id,
            updated_xform,
            odk_credentials,
        )

        log.info("Updating XForm role for appuser in ODK Central")
        # Update the user role for the created xform
        response = appuser.updateRole(
            projectId=project_odk_id,
            xform=xform_name,
            actorId=appuser_id,
        )
        if not response.ok:
            try:
                json_data = response.json()
                log.error(json_data)
            except json.decoder.JSONDecodeError:
                log.error(
                    "Could not parse response json during appuser update. "
                    f"status_code={response.status_code}"
                )
            finally:
                msg = f"Failed to update appuser for form: ({xform_name})"
                log.error(msg)
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg
                ) from None

        odk_url = odk_credentials.odk_central_url

        # NOTE ODK Central creation complete, update database
        log.debug(f"Setting odk token for project ({project_id}) on server: {odk_url}")
        project.odk_token = encrypt_value(
            f"{odk_url}/v1/key/{appuser_token}/projects/{project_odk_id}"
        )

        for task in project.tasks:
            # Add task feature count to task
            task.feature_count = len(task_extract_dict[task.id].get("features", []))
            log.debug(f"({task.feature_count}) features added for task ({task.id})")

        # Commit all updated database records
        db.commit()

        # Map geojson to entities dict
        entities_data_dict = await task_geojson_dict_to_entity_values(task_extract_dict)
        # Create entities
        async with OdkEntity(
            url=odk_credentials.odk_central_url,
            user=odk_credentials.odk_central_user,
            passwd=odk_credentials.odk_central_password,
        ) as odk_central:
            entities = await odk_central.createEntities(
                project_odk_id,
                form_category,
                entities_data_dict,
            )
            log.debug(f"Wrote entities for project ({project_id}): {entities}")

        if background_task_id:
            # Update background task status to COMPLETED
            await update_background_task_status_in_database(
                db, background_task_id, 4
            )  # 4 is COMPLETED

    except Exception as e:
        log.warning(str(e))

        if background_task_id:
            # Update background task status to FAILED
            await update_background_task_status_in_database(
                db, background_task_id, 2, str(e)
            )  # 2 is FAILED
        else:
            # Raise original error if not running in background
            raise e


async def get_project_geometry(db: Session, project_id: int):
    """Retrieves the geometry of a project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the project outline.
    """
    projects = table("projects", column("outline"), column("id"))
    where = f"projects.id={project_id}"
    sql = select(geoalchemy2.functions.ST_AsGeoJSON(projects.c.outline)).where(
        text(where)
    )
    result = db.execute(sql)
    # There should only be one match
    if result.rowcount != 1:
        log.warning(str(sql))
        return False
    row = eval(result.first()[0])
    return json.dumps(row)


async def get_task_geometry(db: Session, project_id: int):
    """Retrieves the geometry of tasks associated with a project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """
    db_tasks = await tasks_crud.get_tasks(db, project_id, None)
    features = []
    for task in db_tasks:
        geom = to_shape(task.outline)
        # Convert the shapely geometry object to GeoJSON
        geometry = geom.__geo_interface__
        properties = {
            "task_id": task.id,
        }
        feature = {"type": "Feature", "geometry": geometry, "properties": properties}
        features.append(feature)

    feature_collection = {"type": "FeatureCollection", "features": features}
    return json.dumps(feature_collection)


async def get_project_features_geojson(
    db: Session,
    project: Union[db_models.DbProject, int],
    task_id: Optional[int] = None,
) -> FeatureCollection:
    """Get a geojson of all features for a task."""
    if isinstance(project, int):
        db_project = await get_project(db, project)
    else:
        db_project = project
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
        data_extract_geojson = await flatgeobuf_to_geojson(db, response.content)

    if not data_extract_geojson:
        msg = "Failed to convert flatgeobuf --> geojson for " f"project ({project_id})"
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
        if not split_extract_dict:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=(f"Failed to extract geojson for task ({task_id})"),
            )
        return split_extract_dict[task_id]

    return data_extract_geojson


async def get_json_from_zip(zip, filename: str, error_detail: str):
    """Extract json file from zip."""
    try:
        with zip.open(filename) as file:
            data = file.read()
            return json.loads(data)
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=400, detail=f"{error_detail} ----- Error: {e}"
        ) from e


async def get_outline_from_geojson_file_in_zip(
    zip, filename: str, error_detail: str, feature_index: int = 0
):
    """Parse geojson outline within a zip."""
    try:
        with zip.open(filename) as file:
            data = file.read()
            json_dump = json.loads(data)
            await check_crs(json_dump)  # Validatiing Coordinate Reference System
            feature_collection = FeatureCollection(json_dump)
            feature = feature_collection["features"][feature_index]
            geom = feature["geometry"]
            shape_from_geom = shape(geom)
            return shape_from_geom
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ----",
        ) from e


async def get_shape_from_json_str(feature: str, error_detail: str):
    """Parse geojson outline within a zip to shapely geom."""
    try:
        geom = feature["geometry"]
        return shape(geom)
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ---- Json: {feature}",
        ) from e


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


async def convert_to_app_project(db_project: db_models.DbProject):
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if not db_project:
        log.debug("convert_to_app_project called, but no project provided")
        return None

    app_project = db_project

    if db_project.outline:
        app_project.outline_geojson = geometry_to_geojson(
            db_project.outline, {"id": db_project.id}, db_project.id
        )

    app_project.tasks = db_project.tasks

    return app_project


async def convert_to_app_project_info(db_project_info: db_models.DbProjectInfo):
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_project_info:
        app_project_info: project_schemas.ProjectInfo = db_project_info
        return app_project_info
    else:
        return None


async def convert_to_app_projects(
    db_projects: List[db_models.DbProject],
) -> List[project_schemas.ProjectOut]:
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_projects and len(db_projects) > 0:

        async def convert_project(project):
            return await convert_to_app_project(project)

        app_projects = await gather(
            *[convert_project(project) for project in db_projects]
        )
        return [project for project in app_projects if project is not None]
    else:
        return []


async def convert_to_project_summary(db_project: db_models.DbProject):
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_project:
        summary: project_schemas.ProjectSummary = db_project

        if db_project.project_info:
            summary.location_str = db_project.location_str
            summary.title = db_project.project_info.name
            summary.description = db_project.project_info.short_description

        summary.num_contributors = (
            db_project.tasks_mapped + db_project.tasks_validated
        )  # TODO: get real number of contributors
        summary.organisation_logo = (
            db_project.organisation.logo if db_project.organisation else None
        )

        return summary
    else:
        return None


async def convert_to_project_summaries(
    db_projects: List[db_models.DbProject],
) -> List[project_schemas.ProjectSummary]:
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_projects and len(db_projects) > 0:

        async def convert_summary(project):
            return await convert_to_project_summary(project)

        project_summaries = await gather(
            *[convert_summary(project) for project in db_projects]
        )
        return [summary for summary in project_summaries if summary is not None]
    else:
        return []


async def get_background_task_status(task_id: uuid.UUID, db: Session):
    """Get the status of a background task."""
    task = (
        db.query(db_models.BackgroundTasks)
        .filter(db_models.BackgroundTasks.id == str(task_id))
        .first()
    )
    if not task:
        log.warning(f"No background task with found with UUID: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    return task.status, task.message


async def insert_background_task_into_database(
    db: Session, name: str = None, project_id: str = None
) -> uuid.uuid4:
    """Inserts a new task into the database.

    Args:
        db (Session): database session
        name (str): name of the task.
        project_id (str): associated project id

    Returns:
        task_id (uuid.uuid4): The background task uuid for tracking.
    """
    task_id = uuid.uuid4()

    task = db_models.BackgroundTasks(
        id=str(task_id), name=name, status=1, project_id=project_id
    )  # 1 = running

    db.add(task)
    db.commit()
    db.refresh(task)

    return task_id


async def update_background_task_status_in_database(
    db: Session, task_id: uuid.UUID, status: int, message: str = None
) -> None:
    """Updates the status of a task in the database.

    Args:
        db (Session): database session.
        task_id (uuid.UUID): uuid of the task.
        status (int): status of the task.
        message (str): optional message to add to the db task.

    Returns:
        None
    """
    db.query(db_models.BackgroundTasks).filter(
        db_models.BackgroundTasks.id == str(task_id)
    ).update(
        {
            db_models.BackgroundTasks.status: status,
            db_models.BackgroundTasks.message: message,
        }
    )
    db.commit()

    return True


# TODO remove me
# async def update_project_form(
#     db: Session, project_id: int, form_type: str, form: UploadFile = File(None)
# ):
#     """Upload a new custom XLSForm for a project."""
#     project = await get_project(db, project_id)
#     category = project.xform_title
#     odk_id = project.odkid

#     # ODK Credentials
#     odk_credentials = await project_deps.get_odk_credentials(db, project_id)

#     if form:
#         xlsform = f"/tmp/custom_form.{form_type}"
#         contents = await form.read()
#         with open(xlsform, "wb") as f:
#             f.write(contents)
#     else:
#         xlsform = f"{xlsforms_path}/{category}.xls"

#     # TODO fix this to use correct data extract generation
#     pg = PostgresClient("underpass")
#     outfile = f"/tmp/{category}.geojson"  # This file will store osm extracts

#     # FIXME test this works
#     # FIXME PostgresClient.getFeatures does not exist...
#     # FIXME getFeatures is part of the DataExtract osm-fieldwork class
#     extract_polygon = True if project.data_extract_type == "polygon" else False

#     project = table("projects", column("outline"))

#     # where = f"id={project_id}
#     sql = select(
#         geoalchemy2.functions.ST_AsGeoJSON(project.c.outline).label("outline"),
#     ).where(text(f"id={project_id}"))
#     result = db.execute(sql)
#     project_outline = result.first()

#     final_outline = json.loads(project_outline.outline)

#     feature_geojson = pg.getFeatures(
#         boundary=final_outline,
#         filespec=outfile,
#         polygon=extract_polygon,
#         xlsfile=f"{category}.xls",
#         category=category,
#     )
#     # TODO upload data extract to S3 bucket

#     tasks_list = await tasks_crud.get_task_id_list(db, project_id)

#     for task_id in tasks_list:
#         # This file will store xml contents of an xls form.
#         xform_path = Path(f"/tmp/{category}_{task_id}.xml")

#         outfile = central_crud.update_survey_xform(
#             xlsform, xform_path, form_type, category
#         )

#         # Create an odk xform
#         # TODO include data extract geojson correctly
#         result = central_crud.create_odk_xform(
#             odk_id,
#             xform_path,
#             category,
#             feature_geojson,
#             odk_credentials,
#         )

#     return True


async def get_extracted_data_from_db(db: Session, project_id: int, outfile: str):
    """Get the geojson of those features for this project."""
    query = text(
        f"""SELECT jsonb_build_object(
                'type', 'FeatureCollection',
                'features', jsonb_agg(feature)
                )
                FROM (
                SELECT jsonb_build_object(
                    'type', 'Feature',
                    'id', id,
                    'geometry', ST_AsGeoJSON(geometry)::jsonb,
                    'properties', properties
                ) AS feature
                FROM features
                WHERE project_id={project_id}
                ) features;"""
    )

    result = db.execute(query)
    features = result.fetchone()[0]

    # Update outfile containing osm extracts with the new geojson contents
    # containing title in the properties.
    with open(outfile, "w") as jsonfile:
        jsonfile.truncate(0)
        geojson.dump(features, jsonfile)


# NOTE defined as non-async to run in separate thread
def get_project_tiles(
    db: Session,
    project_id: int,
    background_task_id: uuid.UUID,
    source: str,
    output_format: str = "mbtiles",
    tms: str = None,
):
    """Get the tiles for a project.

    Args:
        db (Session): SQLAlchemy db session.
        project_id (int): ID of project to create tiles for.
        background_task_id (uuid.UUID): UUID of background task to track.
        source (str): Tile source ("esri", "bing", "topo", "google", "oam").
        output_format (str, optional): Default "mbtiles".
            Other options: "pmtiles", "sqlite3".
        tms (str, optional): Default None. Custom TMS provider URL.
    """
    zooms = "12-19"
    tiles_dir = f"{TILESDIR}/{project_id}"
    outfile = f"{tiles_dir}/{project_id}_{source}tiles.{output_format}"

    tile_path_instance = db_models.DbTilesPath(
        project_id=project_id,
        background_task_id=str(background_task_id),
        status=1,
        tile_source=source,
        path=outfile,
    )

    try:
        db.add(tile_path_instance)
        db.commit()

        # Project Outline
        log.debug(f"Getting bbox for project: {project_id}")
        query = text(
            f"""SELECT ST_XMin(ST_Envelope(outline)) AS min_lon,
                        ST_YMin(ST_Envelope(outline)) AS min_lat,
                        ST_XMax(ST_Envelope(outline)) AS max_lon,
                        ST_YMax(ST_Envelope(outline)) AS max_lat
                FROM projects
                WHERE id = {project_id};"""
        )

        result = db.execute(query)
        project_bbox = result.fetchone()
        log.debug(f"Extracted project bbox: {project_bbox}")

        if project_bbox:
            min_lon, min_lat, max_lon, max_lat = project_bbox
        else:
            log.error(f"Failed to get bbox from project: {project_id}")

        log.debug(
            "Creating basemap with params: "
            f"boundary={min_lon},{min_lat},{max_lon},{max_lat} | "
            f"outfile={outfile} | "
            f"zooms={zooms} | "
            f"outdir={tiles_dir} | "
            f"source={source} | "
            f"xy={False} | "
            f"tms={tms}"
        )

        # TODO replace this temp workaround with osm-fieldwork code
        # TODO to generate pmtiles directly instead of with go-pmtiles
        if output_format == "pmtiles":
            create_basemap_file(
                boundary=f"{min_lon},{min_lat},{max_lon},{max_lat}",
                outfile=outfile.replace("pmtiles", "mbtiles"),
                zooms=zooms,
                outdir=tiles_dir,
                source=source,
                xy=False,
                tms=tms,
            )
            subprocess.call(
                "pmtiles convert " f"{outfile.replace('pmtiles', 'mbtiles')} {outfile}",
                shell=True,
            )
        else:
            create_basemap_file(
                boundary=f"{min_lon},{min_lat},{max_lon},{max_lat}",
                outfile=outfile,
                zooms=zooms,
                outdir=tiles_dir,
                source=source,
                xy=False,
                tms=tms,
            )

        log.info(f"Basemap created for project ID {project_id}: {outfile}")

        tile_path_instance.status = 4
        db.commit()

        # Update background task status to COMPLETED
        update_bg_task_sync = async_to_sync(update_background_task_status_in_database)
        update_bg_task_sync(db, background_task_id, 4)  # 4 is COMPLETED

        log.info(f"Tiles generation process completed for project id {project_id}")

    except Exception as e:
        log.exception(str(e))
        log.error(f"Tiles generation process failed for project id {project_id}")

        tile_path_instance.status = 2
        db.commit()

        # Update background task status to FAILED
        update_bg_task_sync = async_to_sync(update_background_task_status_in_database)
        update_bg_task_sync(db, background_task_id, 2, str(e))  # 2 is FAILED


async def get_mbtiles_list(db: Session, project_id: int):
    """List mbtiles in database for a project."""
    try:
        tiles_list = (
            db.query(
                db_models.DbTilesPath.id,
                db_models.DbTilesPath.project_id,
                db_models.DbTilesPath.status,
                db_models.DbTilesPath.tile_source,
            )
            .filter(db_models.DbTilesPath.project_id == str(project_id))
            .all()
        )

        processed_tiles_list = [
            {
                "id": x.id,
                "project_id": x.project_id,
                "status": x.status.name,
                "tile_source": x.tile_source,
            }
            for x in tiles_list
        ]

        return processed_tiles_list

    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=400, detail=str(e)) from e


async def convert_geojson_to_osm(geojson_file: str):
    """Convert a GeoJSON file to OSM format."""
    return json2osm(geojson_file)


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


async def get_dashboard_detail(
    project: db_models.DbProject, db_organisation: db_models.DbOrganisation, db: Session
):
    """Get project details for project dashboard."""
    s3_project_path = f"/{project.organisation_id}/{project.id}"
    s3_submission_path = f"/{s3_project_path}/submission.zip"
    s3_submission_meta_path = f"/{s3_project_path}/submissions.meta.json"

    try:
        submission = get_obj_from_bucket(settings.S3_BUCKET_NAME, s3_submission_path)
        with zipfile.ZipFile(submission, "r") as zip_ref:
            with zip_ref.open("submissions.json") as file_in_zip:
                content = file_in_zip.read()
        content = json.loads(content)
        project.total_submission = len(content)
        submission_meta = get_obj_from_bucket(
            settings.S3_BUCKET_NAME, s3_submission_meta_path
        )
        project.last_active = (json.loads(submission_meta.getvalue()))[
            "last_submission"
        ]
    except ValueError:
        project.total_submission = 0
        pass

    contributors = (
        db.query(db_models.DbTaskHistory.user_id)
        .filter(
            db_models.DbTaskHistory.project_id == project.id,
            db_models.DbTaskHistory.user_id.isnot(None),
        )
        .distinct()
        .count()
    )

    project.total_tasks = await tasks_crud.get_task_count_in_project(db, project.id)
    project.organisation_name, project.organisation_logo = (
        db_organisation.name,
        db_organisation.logo,
    )
    project.total_contributors = contributors

    return project


async def get_project_users(db: Session, project_id: int):
    """Get the users and their contributions for a project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.

    Returns:
        List[Dict[str, Union[str, int]]]: A list of dictionaries containing
            the username and the number of contributions made by each user
            for the specified project.
    """
    contributors = (
        db.query(db_models.DbTaskHistory)
        .filter(db_models.DbTaskHistory.project_id == project_id)
        .all()
    )
    unique_user_ids = {
        user.user_id for user in contributors if user.user_id is not None
    }
    response = []

    for user_id in unique_user_ids:
        contributions = count_user_contributions(db, user_id, project_id)
        db_user = await user_crud.get_user(db, user_id)
        response.append({"user": db_user.username, "contributions": contributions})

    response = sorted(response, key=lambda x: x["contributions"], reverse=True)
    return response


def count_user_contributions(db: Session, user_id: int, project_id: int) -> int:
    """Count contributions for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.
        project_id (int): The ID of the project.

    Returns:
        int: The number of contributions made by the user for the specified
            project.
    """
    contributions_count = (
        db.query(func.count(db_models.DbTaskHistory.user_id))
        .filter(
            db_models.DbTaskHistory.user_id == user_id,
            db_models.DbTaskHistory.project_id == project_id,
        )
        .scalar()
    )

    return contributions_count


async def add_project_admin(
    db: Session, user: db_models.DbUser, project: db_models.DbProject
):
    """Adds a user as an admin to the specified organisation.

    Args:
        db (Session): The database session.
        user (int): The ID of the user to be added as an admin.
        project (DbOrganisation): The Project model instance.

    Returns:
        Response: The HTTP response with status code 200.
    """
    new_user_role = db_models.DbUserRoles(
        user_id=user.id,
        project_id=project.id,
        role=ProjectRole.PROJECT_MANAGER,
    )

    # add data to the managers field in organisation model
    project.roles.append(new_user_role)
    db.commit()

    return Response(status_code=HTTPStatus.OK)
