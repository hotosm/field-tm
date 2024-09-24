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
from asyncio import gather
from io import BytesIO
from pathlib import Path
from traceback import format_exc
from typing import List, Optional, Union

import geojson
import requests
import shapely.wkb as wkblib
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from fmtm_splitter.splitter import split_by_sql, split_by_square
from geoalchemy2.shape import to_shape
from geojson.feature import Feature, FeatureCollection
from loguru import logger as log
from osm_fieldwork.basemapper import create_basemap_file
from osm_rawdata.postgres import PostgresClient
from shapely.geometry import shape
from sqlalchemy import and_, column, func, select, table, text
from sqlalchemy.orm import Session

from app.central import central_crud
from app.config import settings
from app.db import db_models
from app.db.postgis_utils import (
    check_crs,
    featcol_keep_dominant_geom_type,
    featcol_to_flatgeobuf,
    flatgeobuf_to_featcol,
    get_featcol_dominant_geom_type,
    merge_polygons,
    parse_geojson_file_to_featcol,
    split_geojson_by_task_areas,
    wkb_geom_to_feature,
)
from app.models.enums import HTTPStatus, ProjectRole, ProjectVisibility, XLSFormType
from app.projects import project_deps, project_schemas
from app.s3 import add_obj_to_bucket, delete_all_objs_under_prefix
from app.tasks import tasks_crud

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

    # TODO refactor to use Pydantic model methods instead.
    if db_projects and len(db_projects) > 0:

        async def convert_project(project):
            return await convert_to_app_project(project)

        app_projects = await gather(
            *[convert_project(project) for project in db_projects]
        )
        filtered_projects = [project for project in app_projects if project is not None]
    else:
        filtered_projects = []

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
                    'created', p.created_at,
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
    return project_count, await convert_to_project_summaries(db, db_projects)


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

    # TODO refactor to use Pydantic model methods instead.
    if db_project_info:
        app_project_info: project_schemas.ProjectInfo = db_project_info
        return app_project_info
    else:
        return None


async def delete_fmtm_project(db: Session, project_id: int) -> None:
    """Delete a FMTM project by id."""
    try:
        sql = text("""
            DELETE FROM background_tasks WHERE project_id = :project_id;
            DELETE FROM mbtiles_path WHERE project_id = :project_id;
            DELETE FROM user_roles WHERE project_id = :project_id;
            DELETE FROM task_history WHERE project_id = :project_id;
            DELETE FROM tasks WHERE project_id = :project_id;
            DELETE FROM project_info WHERE project_id = :project_id;
            DELETE FROM projects WHERE id = :project_id;
        """)
        db.execute(sql, {"project_id": project_id})
        db.commit()
        log.info(f"Deleted project with ID: {project_id}")
    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e)) from e


async def delete_fmtm_s3_objects(db_project: db_models.DbProject) -> None:
    """Delete objects on S3 for an FMTM project."""
    project_id = db_project.id
    org_id = db_project.organisation_id
    project_s3_path = f"/{org_id}/{project_id}/"

    delete_all_objs_under_prefix(
        settings.S3_BUCKET_NAME,
        project_s3_path,
    )


async def partial_update_project_info(
    db: Session,
    project_metadata: project_schemas.ProjectPartialUpdate,
    db_project: db_models.DbProject,
):
    """Partial project update for PATCH."""
    # Get project info
    db_project_info = await get_project_info_by_id(db, db_project.id)

    # Update project information
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


async def update_project_with_project_info(
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

    for key, value in project_metadata.model_dump(
        exclude=["project_info", "outline_geojson"]
    ).items():
        setattr(db_project, key, value)

    db_project_info = await get_project_info_by_id(db, db_project.id)
    # Update project's meta information (name, descriptions)
    if db_project_info:
        for key, value in project_info.model_dump(exclude_unset=True).items():
            setattr(db_project_info, key, value)

    db.commit()
    db.refresh(db_project)
    db.refresh(db_project_info)

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
        name=project_metadata.project_info.name,
        description=project_metadata.project_info.description,
        short_description=project_metadata.project_info.short_description,
        per_task_instructions=project_metadata.project_info.per_task_instructions,
    )
    db.add(db_project_info)

    db.commit()
    db.refresh(db_project)

    # Append additional hashtag with FMTM domain and project id
    generated_project_id = db_project.id
    if db_project.hashtags:
        db_project.hashtags = db_project.hashtags + [
            f"#{settings.FMTM_DOMAIN}-{generated_project_id}"
        ]
    db.commit()

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
                project_task_index=index + 1,
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
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, detail=e) from e


async def preview_split_by_square(
    boundary: FeatureCollection,
    meters: int,
    extract_geojson: Optional[FeatureCollection] = None,
):
    """Preview split by square for a project boundary.

    Use a lambda function to remove the "z" dimension from each
    coordinate in the feature's geometry.
    """
    boundary = merge_polygons(boundary)

    return await run_in_threadpool(
        lambda: split_by_square(
            boundary,
            osm_extract=extract_geojson,
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
        auth_token=settings.RAW_DATA_API_AUTH_TOKEN
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


async def split_geojson_into_tasks(
    db: Session,
    project_geojson: FeatureCollection,
    no_of_buildings: int,
    extract_geojson: Optional[FeatureCollection] = None,
):
    """Splits a project into tasks.

    Args:
        db (Session): A database session.
        project_geojson (FeatureCollection): A FeatureCollection containing a
            single project boundary geometry.
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


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


async def read_and_insert_xlsforms(db, directory) -> None:
    """Read the list of XLSForms from the disk and insert to DB."""
    # Insert new XLSForms to DB and update existing ones
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
            insert_query = text(
                """
                INSERT INTO xlsforms (title, xls)
                VALUES (:title, :xls)
                ON CONFLICT (title) DO UPDATE SET
                title = EXCLUDED.title, xls = EXCLUDED.xls
            """
            )
            db.execute(insert_query, {"title": category, "xls": data})
            db.commit()
            log.info(f"XLSForm for '{category}' present in the database")

        except Exception as e:
            log.error(
                f"Failed to insert or update {category} in the database. Error: {e}"
            )

    existing_db_forms = {
        title for (title,) in db.query(db_models.DbXLSForm.title).all()
    }
    required_forms = {xls_type.value for xls_type in XLSFormType}
    # Delete XLSForms from DB that are not found on disk
    for title in existing_db_forms - required_forms:
        delete_query = text(
            """
            DELETE FROM xlsforms WHERE title = :title
        """
        )
        db.execute(delete_query, {"title": title})
        db.commit()
        log.info(
            f"Deleted {title} from the database as it was not present in XLSFormType."
        )


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


async def get_data_extract_type(featcol: FeatureCollection) -> str:
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

    featcol = parse_geojson_file_to_featcol(geojson_raw)
    featcol_single_geom_type = featcol_keep_dominant_geom_type(featcol)

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
    odk_credentials: project_schemas.ODKCentralDecrypted,
    xlsform: BytesIO,
    task_extract_dict: dict[int, geojson.FeatureCollection],
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
    db: Session,
    project_id: int,
    background_task_id: Optional[uuid.UUID] = None,
) -> None:
    """Generate the files for a project.

    QR code (appuser), ODK XForm, ODK Entities from OSM data extract.

    Args:
        db (Session): the database session.
        project_id(int): id of the FMTM project.
        background_task_id (uuid): the task_id of the background task.
    """
    try:
        project = await project_deps.get_project_by_id(db, project_id)
        log.info(f"Starting generate_project_files for project {project_id}")
        odk_credentials = await project_deps.get_odk_credentials(db, project_id)

        # Extract data extract from flatgeobuf
        log.debug("Getting data extract geojson from flatgeobuf")
        feature_collection = await get_project_features_geojson(db, project)

        # Split extract by task area
        log.debug("Splitting data extract per task area")
        # TODO in future this splitting could be removed as the task_id is
        # no longer used in the XLSForm
        task_extract_dict = await split_geojson_by_task_areas(
            db, feature_collection, project_id
        )

        if not task_extract_dict:
            log.warning(f"Project ({project_id}) failed splitting tasks")
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Failed splitting extract by tasks.",
            )

        # Get ODK Project details
        project_odk_id = project.odkid
        project_xlsform = project.xlsform_content
        project_odk_form_id = project.odk_form_id

        encrypted_odk_token = await generate_odk_central_project_content(
            project_odk_id,
            project_odk_form_id,
            odk_credentials,
            BytesIO(project_xlsform),
            task_extract_dict,
        )
        log.debug(
            f"Setting encrypted odk token for FMTM project ({project_id}) "
            f"ODK project {project_odk_id}: {encrypted_odk_token}"
        )
        query = text("""
            UPDATE public.projects
            SET
                odk_token = :encrypted_odk_token
            WHERE id = :project_id;
        """)
        db.execute(
            query,
            {
                "project_id": project_id,
                "encrypted_odk_token": encrypted_odk_token,
            },
        )

        # Add the feature counts for each task
        # FIXME this logic could probably be better
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
        db.execute(text(formatted_sql))

        if background_task_id:
            # Update background task status to COMPLETED
            await update_background_task_status_in_database(
                db, background_task_id, 4
            )  # 4 is COMPLETED

    except Exception as e:
        log.debug(str(format_exc()))
        log.warning(str(e))

        if background_task_id:
            # Update background task status to FAILED
            await update_background_task_status_in_database(
                db, background_task_id, 2, str(e)
            )  # 2 is FAILED
        else:
            # Raise original error if not running in background
            raise e


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
    db_project: db_models.DbProject,
    task_id: Optional[int] = None,
) -> FeatureCollection:
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
        app_project.outline_geojson = wkb_geom_to_feature(
            db_project.outline, {"id": db_project.id}, db_project.id
        )

    app_project.tasks = db_project.tasks

    return app_project


async def convert_to_project_summary(db: Session, db_project: db_models.DbProject):
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_project:
        summary: project_schemas.ProjectSummary = db_project

        if db_project.project_info:
            summary.title = db_project.project_info.name
            summary.description = db_project.project_info.short_description
        summary.num_contributors = (
            db.query(db_models.DbTaskHistory.user_id)
            .filter(
                db_models.DbTaskHistory.project_id == db_project.id,
                db_models.DbTaskHistory.user_id is not None,
            )
            .distinct()
            .count()
        )
        summary.organisation_logo = (
            db_project.organisation.logo if db_project.organisation else None
        )

        return summary
    else:
        return None


async def convert_to_project_summaries(
    db: Session,
    db_projects: List[db_models.DbProject],
) -> List[project_schemas.ProjectSummary]:
    """Legacy function to convert db models --> Pydantic.

    TODO refactor to use Pydantic model methods instead.
    """
    if db_projects and len(db_projects) > 0:

        async def convert_summary(db, project):
            return await convert_to_project_summary(db, project)

        project_summaries = await gather(
            *[convert_summary(db, project) for project in db_projects]
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
    db: Session, name: Optional[str] = None, project_id: Optional[int] = None
) -> uuid.UUID:
    """Inserts a new task into the database.

    Args:
        db (Session): database session
        name (int): name of the task.
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
    tms: Optional[str] = None,
):
    """Get the tiles for a project.

    Args:
        db (Session): SQLAlchemy db session.
        project_id (int): ID of project to create tiles for.
        background_task_id (uuid.UUID): UUID of background task to track.
        source (str): Tile source ("esri", "bing", "google", "custom" (tms)).
        output_format (str, optional): Default "mbtiles".
            Other options: "pmtiles", "sqlite3".
        tms (str, optional): Default None. Custom TMS provider URL.
    """
    # TODO update this for user input or automatic
    # maxzoom can be determined from OAM: https://tiles.openaerialmap.org/663
    # c76196049ef00013b8494/0/663c76196049ef00013b8495
    # TODO xy should also be user configurable
    # NOTE mbtile max supported zoom level is 22 (in GDAL at least)
    zooms = "12-22" if tms else "12-19"
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
            msg = f"Failed to get bbox from project: {project_id}"
            log.error(msg)
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=msg)

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

        tile_path_instance.status = 4
        db.commit()

        # Update background task status to COMPLETED
        update_bg_task_sync = async_to_sync(update_background_task_status_in_database)
        update_bg_task_sync(db, background_task_id, 4)  # 4 is COMPLETED

        log.info(f"Tiles generation process completed for project id {project_id}")

    except Exception as e:
        log.debug(str(format_exc()))
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
                db_models.DbTilesPath.path,
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
                "source": x.tile_source,
                "format": Path(x.path).suffix[1:],
            }
            for x in tiles_list
        ]

        return processed_tiles_list

    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=400, detail=str(e)) from e


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


async def get_dashboard_detail(
    project: db_models.DbProject, db_organisation: db_models.DbOrganisation, db: Session
):
    """Get project details for project dashboard."""
    odk_central = await project_deps.get_odk_credentials(db, project.id)
    xform = central_crud.get_odk_form(odk_central)

    submission_meta_data = xform.getFullDetails(project.odkid, project.odk_form_id)
    project.total_submission = submission_meta_data.get("submissions", 0)
    project.last_active = submission_meta_data.get("lastSubmission")

    contributors = (
        db.query(db_models.DbTaskHistory.user_id)
        .filter(
            db_models.DbTaskHistory.project_id == project.id,
            db_models.DbTaskHistory.user_id is not None,
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
    query = text("""
        SELECT u.username, COUNT(th.user_id) as contributions
        FROM users u
        JOIN task_history th ON u.id = th.user_id
        WHERE th.project_id = :project_id
        GROUP BY u.username
        ORDER BY contributions DESC
    """)
    result = db.execute(query, {"project_id": project_id}).fetchall()

    return [
        {"user": row.username, "contributions": row.contributions} for row in result
    ]


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


async def add_project_manager(
    db: Session, user: db_models.DbUser, project: db_models.DbProject
):
    """Adds a user as an manager to the specified project.

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
