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
import io
import json
import os
import time
import uuid
import zipfile
from io import BytesIO
from json import dumps, loads
from typing import List
from zipfile import ZipFile

import geoalchemy2
import geojson
import numpy as np
import pkg_resources
import pyproj
import requests
import segno
import shapely.wkb as wkblib
import sqlalchemy
from fastapi import File, HTTPException, UploadFile
from geoalchemy2.shape import from_shape, to_shape
from geojson import dump
from loguru import logger as log
from osm_fieldwork.basemapper import create_basemap_file
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.filter_data import FilterData
from osm_fieldwork.json2osm import json2osm
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_fieldwork.xlsforms import xlsforms_path
from osm_rawdata.postgres import PostgresClient
from shapely import wkt
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform
from sqlalchemy import and_, column, func, inspect, select, table, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..config import settings
from ..db import database, db_models
from ..db.postgis_utils import geometry_to_geojson, timestamp
from ..tasks import tasks_crud
from ..users import user_crud
from . import project_schemas

QR_CODES_DIR = "QR_codes/"
TASK_GEOJSON_DIR = "geojson/"
TILESDIR = "/opt/tiles"


def get_projects(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db_objects: bool = False,
    hashtags: List[str] = None,
    search: str = None,
):
    filters = []
    if user_id:
        filters.append(db_models.DbProject.author_id == user_id)

    if hashtags:
        filters.append(db_models.DbProject.hashtags.op("&&")(hashtags))

    if search:
        filters.append(db_models.DbProject.project_name_prefix.ilike(f"%{search}%"))

    if len(filters) > 0:
        db_projects = (
            db.query(db_models.DbProject)
            .filter(and_(*filters))
            .order_by(db_models.DbProject.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    else:
        db_projects = (
            db.query(db_models.DbProject)
            .order_by(db_models.DbProject.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    if db_objects:
        return db_projects
    return convert_to_app_projects(db_projects)


def get_project_summaries(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    hashtags: str = None,
    search: str = None,
):
    # TODO: Just get summaries, something like:
    #     db_projects = db.query(db_models.DbProject).with_entities(
    #         db_models.DbProject.id,
    #         db_models.DbProject.priority,
    #         db_models.DbProject.total_tasks,
    #         db_models.DbProject.tasks_mapped,
    #         db_models.DbProject.tasks_validated,
    #         db_models.DbProject.tasks_bad_imagery,
    #     ).join(db_models.DbProject.project_info) \
    #         .with_entities(
    #             db_models.DbProjectInfo.name,
    #             db_models.DbProjectInfo.short_description) \
    #         .filter(
    #         db_models.DbProject.author_id == user_id).offset(skip).limit(limit).all()

    db_projects = get_projects(db, user_id, skip, limit, True, hashtags, search)
    return convert_to_project_summaries(db_projects)


def get_project_by_id_w_all_tasks(db: Session, project_id: int):
    db_project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )

    return convert_to_app_project(db_project)


def get_project(db: Session, project_id: int):
    db_project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )
    return db_project


def get_project_by_id(db: Session, project_id: int):
    db_project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .order_by(db_models.DbProject.id)
        .first()
    )
    return convert_to_app_project(db_project)


def get_project_info_by_id(db: Session, project_id: int):
    db_project_info = (
        db.query(db_models.DbProjectInfo)
        .filter(db_models.DbProjectInfo.project_id == project_id)
        .order_by(db_models.DbProjectInfo.project_id)
        .first()
    )
    return convert_to_app_project_info(db_project_info)


def delete_project_by_id(db: Session, project_id: int):
    try:
        db_project = (
            db.query(db_models.DbProject)
            .filter(db_models.DbProject.id == project_id)
            .order_by(db_models.DbProject.id)
            .first()
        )
        if db_project:
            db.delete(db_project)
            db.commit()
    except Exception as e:
        log.error(e)
        raise HTTPException(e) from e
    return f"Project {project_id} deleted"


def partial_update_project_info(
    db: Session, project_metadata: project_schemas.ProjectUpdate, project_id
):
    # Get the project from db
    db_project = get_project_by_id(db, project_id)

    # Raise an exception if project is not found.
    if not db_project:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        ) from None

    # Get project info
    db_project_info = get_project_info_by_id(db, project_id)

    # Update project informations
    if project_metadata.name:
        db_project.project_name_prefix = project_metadata.name
        db_project_info.name = project_metadata.name
    if project_metadata.description:
        db_project_info.description = project_metadata.description
    if project_metadata.short_description:
        db_project_info.short_description = project_metadata.short_description

    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)


def update_project_info(
    db: Session, project_metadata: project_schemas.BETAProjectUpload, project_id
):
    user = project_metadata.author
    project_info_1 = project_metadata.project_info

    # verify data coming in
    if not user:
        raise HTTPException("No user passed in")
    if not project_info_1:
        raise HTTPException("No project info passed in")

    # get db user
    db_user = user_crud.get_user(db, user.id)
    if not db_user:
        raise HTTPException(
            status_code=400, detail=f"User {user.username} does not exist"
        )

    # verify project exists in db
    db_project = get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    # Project meta informations
    project_info_1 = project_metadata.project_info

    # Update author of the project
    db_project.author = db_user
    db_project.project_name_prefix = project_info_1.name

    # get project info
    db_project_info = get_project_info_by_id(db, project_id)

    # Update projects meta informations (name, descriptions)
    db_project_info.name = project_info_1.name
    db_project_info.short_description = project_info_1.short_description
    db_project_info.description = project_info_1.description

    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)


def create_project_with_project_info(
    db: Session, project_metadata: project_schemas.BETAProjectUpload, project_id
):
    project_user = project_metadata.author
    project_info_1 = project_metadata.project_info
    xform_title = project_metadata.xform_title
    odk_credentials = project_metadata.odk_central
    hashtags = project_metadata.hashtags
    organisation_id = project_metadata.organisation_id
    task_split_type = project_metadata.task_split_type
    task_split_dimension = project_metadata.task_split_dimension
    task_num_buildings = project_metadata.task_num_buildings

    # verify data coming in
    if not project_user:
        raise HTTPException("No user passed in")
    if not project_info_1:
        raise HTTPException("No project info passed in")

    log.debug(
        "Creating project in FMTM database with vars: "
        f"project_user: {project_user} | "
        f"project_info_1: {project_info_1} | "
        f"xform_title: {xform_title} | "
        f"hashtags: {hashtags}| "
        f"organisation_id: {organisation_id}"
    )

    # Check / set credentials
    if odk_credentials:
        url = odk_credentials.odk_central_url
        user = odk_credentials.odk_central_user
        pw = odk_credentials.odk_central_password

    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    # get db user
    # TODO: get this from logged in user / request instead,
    # return 403 (forbidden) if not authorized
    db_user = user_crud.get_user(db, project_user.id)
    if not db_user:
        raise HTTPException(
            status_code=400, detail=f"User {project_user.username} does not exist"
        )

    hashtags = (
        list(
            map(
                lambda hashtag: hashtag if hashtag.startswith("#") else f"#{hashtag}",
                hashtags,
            )
        )
        if hashtags
        else None
    )
    # create new project
    db_project = db_models.DbProject(
        author=db_user,
        odkid=project_id,
        project_name_prefix=project_info_1.name,
        xform_title=xform_title,
        odk_central_url=url,
        odk_central_user=user,
        odk_central_password=pw,
        hashtags=hashtags,
        organisation_id=organisation_id,
        task_split_type=task_split_type,
        task_split_dimension=task_split_dimension,
        task_num_buildings=task_num_buildings,
        # country=[project_metadata.country],
        # location_str=f"{project_metadata.city}, {project_metadata.country}",
    )
    db.add(db_project)

    # add project info (project id needed to create project info)
    db_project_info = db_models.DbProjectInfo(
        project=db_project,
        name=project_info_1.name,
        short_description=project_info_1.short_description,
        description=project_info_1.description,
    )
    db.add(db_project_info)

    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)


def upload_xlsform(
    db: Session,
    xlsform: str,
    name: str,
    category: str,
):
    try:
        forms = table(
            "xlsforms",
            column("title"),
            column("xls"),
            column("xml"),
            column("id"),
            column("category"),
        )
        ins = insert(forms).values(title=name, xls=xlsform, category=category)
        sql = ins.on_conflict_do_update(
            constraint="xlsforms_title_key",
            set_=dict(title=name, xls=xlsform, category=category),
        )
        db.execute(sql)
        db.commit()
        return True
    except Exception as e:
        raise HTTPException(status=400, detail={"message": str(e)}) from e


def update_multi_polygon_project_boundary(
    db: Session,
    project_id: int,
    boundary: str,
):
    """This function receives the project_id and boundary as a parameter
    and creates a task for each polygon in the database.
    This function also creates a project outline from the multiple polygons received.
    """
    try:
        if isinstance(boundary, str):
            boundary = json.loads(boundary)

        # verify project exists in db
        db_project = get_project_by_id(db, project_id)
        if not db_project:
            log.error(f"Project {project_id} doesn't exist!")
            return False

        # Update the boundary polyon on the database.
        if boundary["type"] == "Feature":
            polygons = [boundary]
        else:
            polygons = boundary["features"]
        log.debug(f"Processing {len(polygons)} task geometries")
        for polygon in polygons:
            # If the polygon is a MultiPolygon, convert it to a Polygon
            if polygon["geometry"]["type"] == "MultiPolygon":
                log.debug("Converting MultiPolygon to Polygon")
                polygon["geometry"]["type"] = "Polygon"
                polygon["geometry"]["coordinates"] = polygon["geometry"]["coordinates"][
                    0
                ]

            # def remove_z_dimension(coord):
            #     """Helper to remove z dimension.

            #     To be used in lambda, to remove z dimension from
            #     each coordinate in the feature's geometry.
            #     """
            #     return coord.pop() if len(coord) == 3 else None

            # # Apply the lambda function to each coordinate in its geometry
            # list(map(remove_z_dimension, polygon["geometry"]["coordinates"][0]))

            db_task = db_models.DbTask(
                project_id=project_id,
                outline=wkblib.dumps(shape(polygon["geometry"]), hex=True),
                project_task_index=1,
            )
            db.add(db_task)
            db.commit()

            # Id is passed in the task_name too
            db_task.project_task_name = str(db_task.id)
            log.debug(
                "Created database task | "
                f"Project ID {project_id} | "
                f"Task ID {db_task.project_task_name}"
            )
            db.commit()

        # Generate project outline from tasks
        query = text(
            f"""SELECT ST_AsText(ST_ConvexHull(ST_Collect(outline)))
                        FROM tasks
                        WHERE project_id={project_id};"""
        )

        log.debug("Generating project outline from tasks")
        result = db.execute(query)
        data = result.fetchone()

        update_project_location_info(db_project, data[0])

        db.commit()
        db.refresh(db_project)
        log.debug("COMPLETE: creating project boundary, based on task boundaries")

        return True
    except Exception as e:
        log.error(e)
        raise HTTPException(e) from e


async def preview_tasks(boundary: str, dimension: int):
    """Preview tasks by returning a list of task objects."""
    """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """

    def remove_z_dimension(coord):
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

    """ Apply the lambda function to each coordinate in its geometry ro remove the z-dimension - if it exists"""
    multi_polygons = []
    for feature in features:
        list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))
        if feature["geometry"]["type"] == "MultiPolygon":
            multi_polygons.append(Polygon(feature["geometry"]["coordinates"][0][0]))

    """Update the boundary polyon on the database."""
    if multi_polygons:
        boundary = multi_polygons[0]
        for geom in multi_polygons[1:]:
            boundary = boundary.union(geom)
    else:
        boundary = shape(features[0]["geometry"])

    minx, miny, maxx, maxy = boundary.bounds

    # 1 degree = 111139 m
    value = dimension / 111139

    nx = int((maxx - minx) / value)
    ny = int((maxy - miny) / value)
    # gx, gy = np.linspace(minx, maxx, nx), np.linspace(miny, maxy, ny)

    xdiff = abs(maxx - minx)
    ydiff = abs(maxy - miny)
    if xdiff > ydiff:
        gx, gy = np.linspace(minx, maxx, ny), np.linspace(miny, miny + xdiff, ny)
    else:
        gx, gy = np.linspace(minx, minx + ydiff, nx), np.linspace(miny, maxy, nx)
    grid = list()

    id = 0
    for i in range(len(gx) - 1):
        for j in range(len(gy) - 1):
            poly = Polygon(
                [
                    [gx[i], gy[j]],
                    [gx[i], gy[j + 1]],
                    [gx[i + 1], gy[j + 1]],
                    [gx[i + 1], gy[j]],
                    [gx[i], gy[j]],
                ]
            )

            if boundary.intersection(poly):
                feature = geojson.Feature(
                    geometry=boundary.intersection(poly), properties={"id": str(id)}
                )
                id += 1

                geom = shape(feature["geometry"])
                # Check if the geometry is a MultiPolygon
                if geom.geom_type == "MultiPolygon":
                    # Get the constituent Polygon objects from the MultiPolygon
                    polygons = geom.geoms

                    for x in range(len(polygons)):
                        # Convert the two polygons to GeoJSON format
                        feature1 = {
                            "type": "Feature",
                            "properties": {},
                            "geometry": mapping(polygons[x]),
                        }
                        grid.append(feature1)
                else:
                    grid.append(feature)

    collection = geojson.FeatureCollection(grid)

    # If project outline cannot be divided into multiple tasks,
    #   whole boundary is made into a single task.
    if len(collection["features"]) == 0:
        boundary = mapping(boundary)
        out = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": boundary, "properties": {}}],
        }
        return out

    return collection


def get_osm_extracts(boundary: str):
    """Request an extract from raw-data-api and extract the file contents.

    - The query is posted to raw-data-api and job initiated for fetching the extract.
    - The status of the job is polled every few seconds, until 'SUCCESS' is returned.
    - The resulting zip file is downloaded, extracted, and data returned.
    """
    # Filters for osm extracts
    query = {
        "filters": {
            "tags": {
                "all_geometry": {
                    "join_or": {"building": [], "highway": [], "waterway": []}
                }
            }
        }
    }

    # Boundary to extract data for
    json_boundary = json.loads(boundary)
    if json_boundary.get("features", None) is not None:
        query["geometry"] = json_boundary
        # query["geometry"] = json_boundary["features"][0]["geometry"]
    else:
        query["geometry"] = json_boundary

    # Filename to generate
    query["fileName"] = "extract"
    # File format to generate
    query["outputType"] = "geojson"
    extract_filename = f'{query["fileName"]}.{query["outputType"]}'
    log.debug(f"Setting data extract file name to: {extract_filename}")

    log.debug(f"Query for raw data api: {query}")
    base_url = settings.UNDERPASS_API_URL
    query_url = f"{base_url}/snapshot/"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Send the request to raw data api
    result = requests.post(query_url, data=json.dumps(query), headers=headers)

    if result.status_code == 200:
        task_id = result.json()["task_id"]
    else:
        return False

    # Check status of task (PENDING, or SUCCESS)
    task_url = f"{base_url}/tasks/status/{task_id}"
    while True:
        result = requests.get(task_url, headers=headers)
        if result.json()["status"] == "PENDING":
            # Wait 2 seconds before polling again
            time.sleep(2)
        elif result.json()["status"] == "SUCCESS":
            break

    # TODO update code to generate fgb file format
    # then input the download_url directly into our database
    # (no need to download the file and extract)
    zip_url = result.json()["result"]["download_url"]
    result = requests.get(zip_url, headers=headers)
    # result.content
    fp = BytesIO(result.content)
    zfp = zipfile.ZipFile(fp, "r")
    zfp.extract(extract_filename, "/tmp/")
    data = json.loads(zfp.read(extract_filename))

    for feature in data["features"]:
        properties = feature["properties"]
        tags = properties.pop("tags", {})
        properties.update(tags)

    return data


async def split_into_tasks(
    db: Session, outline: str, no_of_buildings: int, has_data_extracts: bool
):
    """Splits a project into tasks.

    Args:
        db (Session): A database session.
        boundary (str): A GeoJSON string representing the boundary of the project to split into tasks.
        no_of_buildings (int): The number of buildings to include in each task.

    Returns:
        Any: A GeoJSON object containing the tasks for the specified project.
    """
    project_id = uuid.uuid4()
    all_results = []
    boundary_data = []
    result = []

    if outline["type"] == "FeatureCollection":
        log.debug("Project boundary GeoJSON = FeatureCollection")
        boundary_data.extend(feature["geometry"] for feature in outline["features"])
        result.extend(
            split_polygon_into_tasks(
                db, project_id, data, no_of_buildings, has_data_extracts
            )
            for data in boundary_data
        )

        for inner_list in result:
            if inner_list:
                all_results.extend(iter(inner_list))

    elif outline["type"] == "GeometryCollection":
        log.debug("Project boundary GeoJSON = GeometryCollection")
        geometries = outline["geometries"]
        boundary_data.extend(iter(geometries))
        result.extend(
            split_polygon_into_tasks(
                db, project_id, data, no_of_buildings, has_data_extracts
            )
            for data in boundary_data
        )
        for inner_list in result:
            if inner_list:
                all_results.extend(iter(inner_list))

    elif outline["type"] == "Feature":
        log.debug("Project boundary GeoJSON = Feature")
        boundary_data = outline["geometry"]
        result = split_polygon_into_tasks(
            db, project_id, boundary_data, no_of_buildings, has_data_extracts
        )
        all_results.extend(iter(result))

    elif outline["type"] == "Polygon":
        log.debug("Project boundary GeoJSON = Polygon")
        boundary_data = outline
        result = split_polygon_into_tasks(
            db, project_id, boundary_data, no_of_buildings, has_data_extracts
        )
        all_results.extend(result)

    else:
        log.error(
            "Project boundary not one of: Polygon, Feature, GeometryCollection,"
            " FeatureCollection. Task splitting failed."
        )
    return {
        "type": "FeatureCollection",
        "features": all_results,
    }


def split_polygon_into_tasks(
    db: Session,
    project_id: uuid.UUID,
    boundary_data: str,
    no_of_buildings: int,
    has_data_extracts: bool,
):
    outline = shape(boundary_data)
    db_task = db_models.DbProjectAOI(
        project_id=project_id,
        geom=outline.wkt,
    )
    db.add(db_task)
    db.commit()

    # Get the data extract from raw-data-api
    # Input into DbBuildings and DbOsmLines
    # TODO update to use flatgeobuf file directly
    # No need to store in our database
    if not has_data_extracts:
        data = get_osm_extracts(json.dumps(boundary_data))
        if not data:
            return None
        for feature in data["features"]:
            feature_shape = shape(feature["geometry"])
            wkb_element = from_shape(feature_shape, srid=4326)
            if feature["properties"].get("building") == "yes":
                db_feature = db_models.DbBuildings(
                    project_id=project_id, geom=wkb_element, tags=feature["properties"]
                )
                db.add(db_feature)
            elif "highway" in feature["properties"]:
                db_feature = db_models.DbOsmLines(
                    project_id=project_id, geom=wkb_element, tags=feature["properties"]
                )
                db.add(db_feature)

        db.commit()
    else:
        # Remove the polygons outside of the project AOI using a parameterized query
        query = text(
            f"""
                    DELETE FROM ways_poly
                    WHERE NOT ST_Within(ST_Centroid(ways_poly.geom), (SELECT geom FROM project_aoi WHERE project_id = '{project_id}'));
                """
        )
        result = db.execute(query)
        db.commit()

    # TODO replace with fmtm_splitter algo
    with open("app/db/split_algorithm.sql", "r") as sql_file:
        query = sql_file.read()
    log.debug(f"STARTED project {project_id} task splitting")
    result = db.execute(text(query), params={"num_buildings": no_of_buildings})
    result = result.fetchall()
    db.query(db_models.DbBuildings).delete()
    db.query(db_models.DbOsmLines).delete()
    db.query(db_models.DbProjectAOI).delete()
    db.commit()
    log.debug(f"COMPLETE project {project_id} task splitting")

    features = result[0][0]["features"]
    if not features:
        log.warning(
            f"Project {project_id}: no tasks returned from splitting algorithm. "
            f"Params: 'num_buildings': {no_of_buildings}"
        )
        return []

    log.debug(f"Project {project_id} split into {len(features)} tasks")
    return features


# def update_project_boundary(
#     db: Session, project_id: int, boundary: str, dimension: int
# ):
#     # verify project exists in db
#     db_project = get_project_by_id(db, project_id)
#     if not db_project:
#         log.error(f"Project {project_id} doesn't exist!")
#         return False

#     """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """

#     def remove_z_dimension(coord):
#         return coord.pop() if len(coord) == 3 else None

#     """ Check if the boundary is a Feature or a FeatureCollection """
#     if boundary["type"] == "Feature":
#         features = [boundary]
#     elif boundary["type"] == "FeatureCollection":
#         features = boundary["features"]
#     else:
#         # Delete the created Project
#         db.delete(db_project)
#         db.commit()

#         # Raise an exception
#         raise HTTPException(
#             status_code=400, detail=f"Invalid GeoJSON type: {boundary['type']}"
#         )

#     """ Apply the lambda function to each coordinate in its geometry """
#     for feature in features:
#         list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))

#     """Update the boundary polyon on the database."""
#     outline = shape(features[0]["geometry"])

#     # If the outline is a multipolygon, use the first polygon
#     if isinstance(outline, MultiPolygon):
#         outline = outline.geoms[0]

#     db_project.outline = outline.wkt
#     db_project.centroid = outline.centroid.wkt

#     db.commit()
#     db.refresh(db_project)
#     log.debug("Added project boundary!")

#     result = create_task_grid(db, project_id=project_id, delta=dimension)

#     tasks = eval(result)
#     for poly in tasks["features"]:
#         log.debug(poly)
#         task_name = str(poly["properties"]["id"])
#         db_task = db_models.DbTask(
#             project_id=project_id,
#             project_task_name=task_name,
#             outline=wkblib.dumps(shape(poly["geometry"]), hex=True),
#             # qr_code=db_qr,
#             # qr_code_id=db_qr.id,
#             # project_task_index=feature["properties"]["fid"],
#             project_task_index=1,
#             # geometry_geojson=geojson.dumps(task_geojson),
#             # initial_feature_count=len(task_geojson["features"]),
#         )

#         db.add(db_task)
#         db.commit()

#         # FIXME: write to tasks table
#     return True


def update_project_boundary(
    db: Session, project_id: int, boundary: str, dimension: int
):
    # verify project exists in db
    db_project = get_project_by_id(db, project_id)
    if not db_project:
        log.error(f"Project {project_id} doesn't exist!")
        return False

    """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """

    def remove_z_dimension(coord):
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
        # Delete the created Project
        db.delete(db_project)
        db.commit()

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

    """Update the boundary polyon on the database."""
    if multi_polygons:
        outline = multi_polygons[0]
        for geom in multi_polygons[1:]:
            outline = outline.union(geom)
    else:
        outline = shape(features[0]["geometry"])

    update_project_location_info(db_project, outline.wkt)

    db.commit()
    db.refresh(db_project)
    log.debug("Added project boundary!")

    result = create_task_grid(db, project_id=project_id, delta=dimension)

    # Delete features from the project
    db.query(db_models.DbFeatures).filter(
        db_models.DbFeatures.project_id == project_id
    ).delete()

    # Delete all tasks of the project if there are some
    db.query(db_models.DbTask).filter(
        db_models.DbTask.project_id == project_id
    ).delete()

    tasks = eval(result)
    for poly in tasks["features"]:
        log.debug(poly)
        task_name = str(poly["properties"]["id"])
        db_task = db_models.DbTask(
            project_id=project_id,
            project_task_name=task_name,
            outline=wkblib.dumps(shape(poly["geometry"]), hex=True),
            # qr_code=db_qr,
            # qr_code_id=db_qr.id,
            # project_task_index=feature["properties"]["fid"],
            project_task_index=1,
            # geometry_geojson=geojson.dumps(task_geojson),
            # initial_feature_count=len(task_geojson["features"]),
        )
        db.add(db_task)
        db.commit()

        # FIXME: write to tasks table
    return True


def update_project_with_zip(
    db: Session,
    project_id: int,
    project_name_prefix: str,
    task_type_prefix: str,
    uploaded_zip: UploadFile,
):
    # TODO: ensure that logged in user is user who created this project, return 403 (forbidden) if not authorized

    # ensure file upload is zip
    if uploaded_zip.content_type not in [
        "application/zip",
        "application/zip-compressed",
        "application/x-zip-compressed",
    ]:
        raise HTTPException(
            status_code=415,
            detail=f"File must be a zip. Uploaded file was {uploaded_zip.content_type}",
        )

    with ZipFile(io.BytesIO(uploaded_zip.file.read()), "r") as zip:
        # verify valid zip file
        bad_file = zip.testzip()
        if bad_file:
            raise HTTPException(
                status_code=400, detail=f"Zip contained a bad file: {bad_file}"
            )

        # verify zip includes top level files & directories
        listed_files = zip.namelist()

        if QR_CODES_DIR not in listed_files:
            raise HTTPException(
                status_code=400,
                detail=f"Zip must contain directory named {QR_CODES_DIR}",
            )

        if TASK_GEOJSON_DIR not in listed_files:
            raise HTTPException(
                status_code=400,
                detail=f"Zip must contain directory named {TASK_GEOJSON_DIR}",
            )

        outline_filename = f"{project_name_prefix}.geojson"
        if outline_filename not in listed_files:
            raise HTTPException(
                status_code=400,
                detail=f'Zip must contain file named "{outline_filename}" that contains a FeatureCollection outlining the project',
            )

        task_outlines_filename = f"{project_name_prefix}_polygons.geojson"
        if task_outlines_filename not in listed_files:
            raise HTTPException(
                status_code=400,
                detail=f'Zip must contain file named "{task_outlines_filename}" that contains a FeatureCollection where each Feature outlines a task',
            )

        # verify project exists in db
        db_project = get_project_by_id(db, project_id)
        if not db_project:
            raise HTTPException(
                status_code=428, detail=f"Project with id {project_id} does not exist"
            )

        # add prefixes
        db_project.project_name_prefix = project_name_prefix
        db_project.task_type_prefix = task_type_prefix

        # generate outline from file and add to project
        outline_shape = get_outline_from_geojson_file_in_zip(
            zip, outline_filename, f"Could not generate Shape from {outline_filename}"
        )
        update_project_location_info(db_project, outline_shape.wkt)

        # get all task outlines from file
        project_tasks_feature_collection = get_json_from_zip(
            zip,
            task_outlines_filename,
            f"Could not generate FeatureCollection from {task_outlines_filename}",
        )

        # generate task for each feature
        try:
            task_count = 0
            db_project.total_tasks = len(project_tasks_feature_collection["features"])
            for feature in project_tasks_feature_collection["features"]:
                task_name = feature["properties"]["task"]

                # generate and save qr code in db
                qr_filename = (
                    f"{project_name_prefix}_{task_type_prefix}__{task_name}.png"
                )
                db_qr = get_dbqrcode_from_file(
                    zip,
                    QR_CODES_DIR + qr_filename,
                    f"QRCode for task {task_name} does not exist. File should be in {qr_filename}",
                )
                db.add(db_qr)

                # save outline
                task_outline_shape = get_shape_from_json_str(
                    feature,
                    f"Could not create task outline for {task_name} using {feature}",
                )

                # extract task geojson
                task_geojson_filename = (
                    f"{project_name_prefix}_{task_type_prefix}__{task_name}.geojson"
                )
                task_geojson = get_json_from_zip(
                    zip,
                    TASK_GEOJSON_DIR + task_geojson_filename,
                    f"Geojson for task {task_name} does not exist",
                )

                # generate qr code id first
                db.flush()
                # save task in db
                task = db_models.DbTask(
                    project_id=project_id,
                    project_task_index=feature["properties"]["fid"],
                    project_task_name=task_name,
                    qr_code=db_qr,
                    qr_code_id=db_qr.id,
                    outline=task_outline_shape.wkt,
                    # geometry_geojson=json.dumps(task_geojson),
                    initial_feature_count=len(task_geojson["features"]),
                )
                db.add(task)

                # for error messages
                task_count = task_count + 1
            db_project.last_updated = timestamp()

            db.commit()
            # should now include outline, geometry and tasks
            db.refresh(db_project)

            return db_project

        # Exception was raised by app logic and has an error message, just pass it along
        except HTTPException as e:
            raise e

        # Unexpected exception
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"{task_count} tasks were created before the following error was thrown: {e}, on feature: {feature}",
            )


# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------


def read_xlsforms(
    db: Session,
    directory: str,
):
    """Read the list of XLSForms from the disk."""
    xlsforms = list()
    package_name = "osm_fieldwork"
    for xls in os.listdir(directory):
        if xls.endswith(".xls") or xls.endswith(".xlsx"):
            file_name = xls.split(".")[0]
            yaml_file_name = f"data_models/{file_name}.yaml"
            if pkg_resources.resource_exists(package_name, yaml_file_name):
                xlsforms.append(xls)
            else:
                continue
    log.info(xls)
    inspect(db_models.DbXForm)
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


def get_odk_id_for_project(db: Session, project_id: int):
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


def upload_custom_data_extracts(
    db: Session,
    project_id: int,
    contents: str,
    category: str = "buildings",
):
    """Uploads custom data extracts to the database.

    Args:
        db (Session): The database session object.
        project_id (int): The ID of the project.
        contents (str): The custom data extracts contents.

    Returns:
        bool: True if the upload is successful.
    """
    project = get_project(db, project_id)
    log.debug(f"Uploading custom data extract for project: {project}")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_geojson = db.query(func.ST_AsGeoJSON(project.outline)).scalar()
    log.debug(f"Generated project geojson: {project_geojson}")
    json.loads(project_geojson)

    features_data = json.loads(contents)

    # # Data Cleaning
    # cleaned = FilterData()
    # models = xlsforms_path.replace("xlsforms", "data_models")
    # xlsfile = f"{category}.xls"  # FIXME: for custom form
    # file = f"{xlsforms_path}/{xlsfile}"
    # if os.path.exists(file):
    #     title, extract = cleaned.parse(file)
    # elif os.path.exists(f"{file}x"):
    #     title, extract = cleaned.parse(f"{file}x")
    # # Remove anything in the data extract not in the choices sheet.
    # cleaned_data = cleaned.cleanData(features_data)

    for feature in features_data["features"]:
        feature_shape = shape(feature["geometry"])
        if isinstance(feature_shape, MultiPolygon):
            wkb_element = from_shape(
                Polygon(feature["geometry"]["coordinates"][0][0]), srid=4326
            )
        elif isinstance(feature_shape, MultiLineString):
            wkb_element = from_shape(
                LineString(feature["geometry"]["coordinates"][0]), srid=4326
            )
        else:
            wkb_element = from_shape(feature_shape, srid=4326)

        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature["properties"]["title"] = ""
        properties = flatten_dict(feature["properties"])

        db_feature = db_models.DbFeatures(
            project_id=project_id,
            geometry=wkb_element,
            properties=properties,
            category_title=category,
        )
        db.add(db_feature)
    db.commit()

    return True


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


def generate_task_files(
    db: Session,
    project_id: int,
    task_id: int,
    xlsform: str,
    form_type: str,
    odk_credentials: project_schemas.ODKCentral,
):
    project_log = log.bind(task="create_project", project_id=project_id)

    project_log.info(f"Generating files for task {task_id}")
    project = get_project(db, project_id)
    odk_id = project.odkid
    project_name = project.project_name_prefix
    category = project.xform_title
    name = f"{project_name}_{category}_{task_id}"

    # Create an app user for the task
    project_log.info(f"Creating odkcentral app user for task {task_id}")
    appuser = central_crud.create_appuser(odk_id, name, odk_credentials)

    # If app user could not be created, raise an exception.
    if not appuser:
        project_log.error("Couldn't create appuser for project")
        return False

    # prefix should be sent instead of name
    project_log.info(f"Creating qr code for task {task_id}")
    create_qr = create_qrcode(
        db,
        odk_id,
        appuser.json()["token"],
        project_name,
        odk_credentials.odk_central_url,
    )

    task = tasks_crud.get_task(db, task_id)
    task.qr_code_id = create_qr["qr_code_id"]
    db.commit()
    db.refresh(task)

    # This file will store xml contents of an xls form.
    xform = f"/tmp/{name}.xml"
    extracts = f"/tmp/{name}.geojson"  # This file will store osm extracts

    # xform_id_format
    xform_id = f"{name}".split("_")[2]

    # Get the features for this task.
    # Postgis query to filter task inside this task outline and of this project
    # Update those features and set task_id
    query = text(
        f"""UPDATE features
                SET task_id={task_id}
                WHERE id IN (
                    SELECT id
                    FROM features
                    WHERE project_id={project_id}
                    AND ST_IsValid(geometry)
                    AND ST_IsValid('{task.outline}'::Geometry)
                    AND ST_Contains('{task.outline}'::Geometry, ST_Centroid(geometry))
                )"""
    )

    result = db.execute(query)

    # Get the geojson of those features for this task.
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
                WHERE project_id={project_id} and task_id={task_id}
                ) features;"""
    )

    result = db.execute(query)

    features = result.fetchone()[0]

    upload_media = False if features["features"] is None else True

    # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
    with open(extracts, "w") as jsonfile:
        jsonfile.truncate(0)  # clear the contents of the file
        dump(features, jsonfile)

    project_log.info(
        f"Generating xform for task: {task_id} "
        f"using xform: {xform} | form_type: {form_type}"
    )
    outfile = central_crud.generate_updated_xform(xlsform, xform, form_type)

    # Create an odk xform
    project_log.info(f"Uploading media in {task_id}")
    result = central_crud.create_odk_xform(
        odk_id, task_id, outfile, odk_credentials, False, upload_media
    )
    # result = central_crud.create_odk_xform(odk_id, task_id, outfile, odk_credentials)

    project_log.info(f"Updating role for app user in task {task_id}")
    # Update the user role for the created xform.
    try:
        # Pass odk credentials
        if odk_credentials:
            url = odk_credentials.odk_central_url
            user = odk_credentials.odk_central_user
            pw = odk_credentials.odk_central_password

        else:
            log.debug("ODKCentral connection variables not set in function")
            log.debug("Attempting extraction from environment variables")
            url = settings.ODK_CENTRAL_URL
            user = settings.ODK_CENTRAL_USER
            pw = settings.ODK_CENTRAL_PASSWD

        odk_app = OdkAppUser(url, user, pw)

        odk_app.updateRole(
            projectId=odk_id, xform=xform_id, actorId=appuser.json()["id"]
        )
    except Exception as e:
        log.warning(str(e))

    project.extract_completed_count += 1
    db.commit()
    db.refresh(project)

    return True


def generate_task_files_wrapper(project_id, task, xlsform, form_type, odk_credentials):
    for db in database.get_db():
        generate_task_files(db, project_id, task, xlsform, form_type, odk_credentials)


def generate_appuser_files(
    db: Session,
    project_id: int,
    extract_polygon: bool,
    upload: str,
    extracts_contents: str,
    category: str,
    form_type: str,
    background_task_id: uuid.UUID,
):
    """Generate the files for each appuser.
    QR code, new XForm, and the OSM data extract.

    Parameters:
        - db: the database session
        - project_id: Project ID
        - extract_polygon: boolean to determine if we should extract the polygon
        - upload: the xls file to upload if we have a custom form
        - category: the category of the project
        - form_type: weather the form is xls, xlsx or xml
        - background_task_id: the task_id of the background task running this function.
    """
    try:
        project_log = log.bind(task="create_project", project_id=project_id)

        project_log.info(f"Starting generate_appuser_files for project {project_id}")

        # Get the project table contents.
        project = table(
            "projects",
            column("project_name_prefix"),
            column("xform_title"),
            column("id"),
            column("odk_central_url"),
            column("odk_central_user"),
            column("odk_central_password"),
            column("outline"),
        )

        where = f"id={project_id}"
        sql = select(
            project.c.project_name_prefix,
            project.c.xform_title,
            project.c.id,
            project.c.odk_central_url,
            project.c.odk_central_user,
            project.c.odk_central_password,
            geoalchemy2.functions.ST_AsGeoJSON(project.c.outline).label("outline"),
        ).where(text(where))
        result = db.execute(sql)

        # There should only be one match
        if result.rowcount != 1:
            log.warning(str(sql))
            if result.rowcount < 1:
                raise HTTPException(status_code=400, detail="Project not found")
            else:
                raise HTTPException(status_code=400, detail="Multiple projects found")

        one = result.first()

        if one:
            # Get odk credentials from project.
            odk_credentials = {
                "odk_central_url": one.odk_central_url,
                "odk_central_user": one.odk_central_user,
                "odk_central_password": one.odk_central_password,
            }

            odk_credentials = project_schemas.ODKCentral(**odk_credentials)

            xform_title = one.xform_title if one.xform_title else None

            category = xform_title
            if upload:
                xlsform = f"/tmp/{category}.{form_type}"
                contents = upload
                with open(xlsform, "wb") as f:
                    f.write(contents)
            else:
                xlsform = f"{xlsforms_path}/{xform_title}.xls"

            # Data Extracts
            if extracts_contents is not None:
                project_log.info("Uploading data extracts")
                upload_custom_data_extracts(db, project_id, extracts_contents)

            else:
                project = (
                    db.query(db_models.DbProject)
                    .filter(db_models.DbProject.id == project_id)
                    .first()
                )
                config_file_contents = project.form_config_file

                project_log.info("Extracting Data from OSM")

                config_path = "/tmp/config.yaml"
                if config_file_contents:
                    with open(config_path, "w", encoding="utf-8") as config_file_handle:
                        config_file_handle.write(config_file_contents.decode("utf-8"))
                else:
                    config_path = f"{data_models_path}/{category}.yaml"

                # # OSM Extracts for whole project
                pg = PostgresClient("underpass", config_path)
                outline = json.loads(one.outline)
                boundary = {"type": "Feature", "properties": {}, "geometry": outline}
                data_extract = pg.execQuery(boundary)
                filter = FilterData(xlsform)

                updated_data_extract = {"type": "FeatureCollection", "features": []}
                filtered_data_extract = (
                    filter.cleanData(data_extract)
                    if data_extract
                    else updated_data_extract
                )

                # Collect feature mappings for bulk insert
                feature_mappings = []

                for feature in filtered_data_extract["features"]:
                    # If the osm extracts contents do not have a title, provide an empty text for that.
                    feature["properties"]["title"] = ""

                    feature_shape = shape(feature["geometry"])

                    # If the centroid of the Polygon is not inside the outline, skip the feature.
                    if extract_polygon and (
                        not shape(outline).contains(shape(feature_shape.centroid))
                    ):
                        continue

                    wkb_element = from_shape(feature_shape, srid=4326)
                    feature_mapping = {
                        "project_id": project_id,
                        "category_title": category,
                        "geometry": wkb_element,
                        "properties": feature["properties"],
                    }
                    updated_data_extract["features"].append(feature)
                    feature_mappings.append(feature_mapping)
                # Bulk insert the osm extracts into the db.
                db.bulk_insert_mappings(db_models.DbFeatures, feature_mappings)

            # Generating QR Code, XForm and uploading OSM Extracts to the form.
            # Creating app users and updating the role of that user.
            tasks_list = tasks_crud.get_task_lists(db, project_id)

            # info = get_cpu_info()
            # cores = info["count"]
            # with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
            #     futures = {executor.submit(generate_task_files_wrapper, project_id, task, xlsform, form_type, odk_credentials): task for task in tasks_list}

            #     for future in concurrent.futures.as_completed(futures):
            #         log.debug(f"Waiting for thread to complete..")

            for task in tasks_list:
                try:
                    generate_task_files(
                        db,
                        project_id,
                        task,
                        xlsform,
                        form_type,
                        odk_credentials,
                    )
                except Exception as e:
                    log.warning(str(e))
                    continue
        # # Update background task status to COMPLETED
        update_background_task_status_in_database(
            db, background_task_id, 4
        )  # 4 is COMPLETED

    except Exception as e:
        log.warning(str(e))

        # Update background task status to FAILED
        update_background_task_status_in_database(
            db, background_task_id, 2, str(e)
        )  # 2 is FAILED


def create_qrcode(
    db: Session,
    odk_id: int,
    token: str,
    project_name: str,
    odk_central_url: str = None,
):
    # Make QR code for an app_user.
    log.debug(f"Generating base64 encoded QR settings for token: {token}")
    qrcode_data = central_crud.create_qrcode(
        odk_id, token, project_name, odk_central_url
    )

    log.debug("Generating QR code from base64 settings")
    qrcode = segno.make(qrcode_data, micro=False)

    log.debug("Saving to buffer and decoding")
    buffer = io.BytesIO()
    qrcode.save(buffer, kind="png", scale=5)
    qrcode_binary = buffer.getvalue()

    log.debug(f"Writing QR code to database for token {token}")
    qrdb = db_models.DbQrCode(image=qrcode_binary)
    db.add(qrdb)
    db.commit()
    codes = table("qr_code", column("id"))
    sql = select(sqlalchemy.func.count(codes.c.id))
    result = db.execute(sql)
    rows = result.fetchone()[0]
    return {"data": qrcode, "id": rows + 1, "qr_code_id": qrdb.id}


def get_project_geometry(db: Session, project_id: int):
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


def get_task_geometry(db: Session, project_id: int):
    """Retrieves the geometry of tasks associated with a project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """
    db_tasks = tasks_crud.get_tasks(db, project_id, None)
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


async def get_project_features_geojson(db: Session, project_id: int):
    db_features = (
        db.query(db_models.DbFeatures)
        .filter(db_models.DbFeatures.project_id == project_id)
        .all()
    )

    """Get a geojson of all features for a task."""
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
                ) features;
            """
    )

    result = db.execute(query)
    features = result.fetchone()[0]

    # Create mapping feat_id:task_id
    task_feature_mapping = {feat.id: feat.task_id for feat in db_features}

    for feature in features["features"]:
        if (feat_id := feature["id"]) in task_feature_mapping:
            feature["properties"]["task_id"] = task_feature_mapping[feat_id]

    return features


def create_task_grid(db: Session, project_id: int, delta: int):
    try:
        # Query DB for project AOI
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
        data = result.fetchall()
        boundary = shape(loads(data[0][0]))
        minx, miny, maxx, maxy = boundary.bounds

        # 1 degree = 111139 m
        value = delta / 111139

        nx = int((maxx - minx) / value)
        ny = int((maxy - miny) / value)
        # gx, gy = np.linspace(minx, maxx, nx), np.linspace(miny, maxy, ny)

        xdiff = maxx - minx
        ydiff = maxy - miny
        if xdiff > ydiff:
            gx, gy = np.linspace(minx, maxx, ny), np.linspace(miny, miny + xdiff, ny)
        else:
            gx, gy = np.linspace(minx, minx + ydiff, nx), np.linspace(miny, maxy, nx)

        grid = list()

        id = 0
        for i in range(len(gx) - 1):
            for j in range(len(gy) - 1):
                poly = Polygon(
                    [
                        [gx[i], gy[j]],
                        [gx[i], gy[j + 1]],
                        [gx[i + 1], gy[j + 1]],
                        [gx[i + 1], gy[j]],
                        [gx[i], gy[j]],
                    ]
                )

                if boundary.intersection(poly):
                    feature = geojson.Feature(
                        geometry=boundary.intersection(poly), properties={"id": str(id)}
                    )

                    geom = shape(feature["geometry"])
                    # Check if the geometry is a MultiPolygon
                    if geom.geom_type == "MultiPolygon":
                        # Get the constituent Polygon objects from the MultiPolygon
                        polygons = geom.geoms

                        for x in range(len(polygons)):
                            id += 1
                            # Convert the two polygons to GeoJSON format
                            feature1 = {
                                "type": "Feature",
                                "properties": {"id": str(id)},
                                "geometry": mapping(polygons[x]),
                            }
                            grid.append(feature1)
                    else:
                        id += 1
                        grid.append(feature)

        collection = geojson.FeatureCollection(grid)
        # jsonout = open("tmp.geojson", 'w')
        # out = dump(collection, jsonout)
        out = dumps(collection)

        # If project outline cannot be divided into multiple tasks,
        #   whole boundary is made into a single task.
        result = json.loads(out)
        if len(result["features"]) == 0:
            geom = loads(data[0][0])
            out = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": geom,
                        "properties": {"id": project_id},
                    }
                ],
            }
            out = json.dumps(out)

        return out
    except Exception as e:
        log.error(e)


def get_json_from_zip(zip, filename: str, error_detail: str):
    try:
        with zip.open(filename) as file:
            data = file.read()
            return json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{error_detail} ----- Error: {e}")


def get_outline_from_geojson_file_in_zip(
    zip, filename: str, error_detail: str, feature_index: int = 0
):
    try:
        with zip.open(filename) as file:
            data = file.read()
            json_dump = json.loads(data)
            check_crs(json_dump)  # Validatiing Coordinate Reference System
            feature_collection = geojson.FeatureCollection(json_dump)
            feature = feature_collection["features"][feature_index]
            geom = feature["geometry"]
            shape_from_geom = shape(geom)
            return shape_from_geom
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ----",
        ) from e


def get_shape_from_json_str(feature: str, error_detail: str):
    try:
        geom = feature["geometry"]
        return shape(geom)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ---- Json: {feature}",
        ) from e


def get_dbqrcode_from_file(zip, qr_filename: str, error_detail: str):
    try:
        with zip.open(qr_filename) as qr_file:
            binary_qrcode = qr_file.read()
            if binary_qrcode:
                return db_models.DbQrCode(
                    filename=qr_filename,
                    image=binary_qrcode,
                )
            else:
                raise HTTPException(
                    status_code=400, detail=f"{qr_filename} is an empty file"
                ) from None
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=400, detail=f"{error_detail} ----- Error: {e}"
        ) from e


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


def convert_to_app_project(db_project: db_models.DbProject):
    if db_project:
        log.debug("Converting db project to app project")
        app_project: project_schemas.Project = db_project

        if db_project.outline:
            log.debug("Converting project outline to geojson")
            app_project.outline_geojson = geometry_to_geojson(
                db_project.outline, {"id": db_project.id}, db_project.id
            )

        app_project.project_tasks = tasks_crud.convert_to_app_tasks(db_project.tasks)

        return app_project
    else:
        log.debug("convert_to_app_project called, but no project provided")
        return None


def convert_to_app_project_info(db_project_info: db_models.DbProjectInfo):
    if db_project_info:
        app_project_info: project_schemas.ProjectInfo = db_project_info
        return app_project_info
    else:
        return None


def convert_to_app_projects(db_projects: List[db_models.DbProject]):
    if db_projects and len(db_projects) > 0:
        app_projects = []
        for project in db_projects:
            if project:
                app_projects.append(convert_to_app_project(project))
        app_projects_without_nones = [i for i in app_projects if i is not None]
        return app_projects_without_nones
    else:
        return []


def convert_to_project_summary(db_project: db_models.DbProject):
    if db_project:
        summary: project_schemas.ProjectSummary = db_project

        if db_project.project_info and len(db_project.project_info) > 0:
            default_project_info = next(
                (x for x in db_project.project_info),
                None,
            )
            # default_project_info = project_schemas.ProjectInfo
            summary.location_str = db_project.location_str
            summary.title = default_project_info.name
            summary.description = default_project_info.short_description

        summary.num_contributors = (
            db_project.tasks_mapped + db_project.tasks_validated
        )  # TODO: get real number of contributors
        summary.organisation_logo = (
            db_project.organisation.logo if db_project.organisation else None
        )

        return summary
    else:
        return None


def convert_to_project_summaries(db_projects: List[db_models.DbProject]):
    if db_projects and len(db_projects) > 0:
        project_summaries = []
        for project in db_projects:
            if project:
                project_summaries.append(convert_to_project_summary(project))
        app_projects_without_nones = [i for i in project_summaries if i is not None]
        return app_projects_without_nones
    else:
        return []


def convert_to_project_feature(db_project_feature: db_models.DbFeatures):
    if db_project_feature:
        app_project_feature: project_schemas.Feature = db_project_feature

        if db_project_feature.geometry:
            app_project_feature.geometry = geometry_to_geojson(
                db_project_feature.geometry,
                db_project_feature.properties,
                db_project_feature.id,
            )

        return app_project_feature
    else:
        return None


def convert_to_project_features(db_project_features: List[db_models.DbFeatures]):
    if db_project_features and len(db_project_features) > 0:
        app_project_features = []
        for project_feature in db_project_features:
            if project_feature:
                app_project_features.append(convert_to_project_feature(project_feature))
        return app_project_features
    else:
        return []


def get_project_features(db: Session, project_id: int, task_id: int = None):
    if task_id:
        features = (
            db.query(db_models.DbFeatures)
            .filter(db_models.DbFeatures.project_id == project_id)
            .filter(db_models.DbFeatures.task_id == task_id)
            .all()
        )
    else:
        features = (
            db.query(db_models.DbFeatures)
            .filter(db_models.DbFeatures.project_id == project_id)
            .all()
        )
    return convert_to_project_features(features)


async def get_extract_completion_count(project_id: int, db: Session):
    project = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )
    return project.extract_completed_count


async def get_background_task_status(task_id: uuid.UUID, db: Session):
    """Get the status of a background task."""
    task = (
        db.query(db_models.BackgroundTasks)
        .filter(db_models.BackgroundTasks.id == str(task_id))
        .first()
    )
    return task.status, task.message


async def insert_background_task_into_database(
    db: Session, task_id: uuid.UUID, name: str = None, project_id=None
):
    """Inserts a new task into the database
    Params:
        db: database session
        task_id: uuid of the task
        name: name of the task.
    """
    task = db_models.BackgroundTasks(
        id=str(task_id), name=name, status=1, project_id=project_id
    )  # 1 = running

    db.add(task)
    db.commit()
    db.refresh(task)

    return True


def update_background_task_status_in_database(
    db: Session, task_id: uuid.UUID, status: int, message: str = None
):
    """Updates the status of a task in the database
    Params:
        db: database session
        task_id: uuid of the task
        status: status of the task.
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


def add_features_into_database(
    db: Session,
    features: dict,
    background_task_id: uuid.UUID,
    feature_type: str,
):
    """Inserts a new task into the database
    Params:
          db: database session
          project_id: id of the project
          features: features to be added.
    """
    try:
        success = 0
        failure = 0
        project_id = uuid.uuid4()
        if feature_type == "buildings":
            for feature in features["features"]:
                try:
                    feature_geometry = feature["geometry"]
                    feature_shape = shape(feature_geometry)

                    wkb_element = from_shape(feature_shape, srid=4326)
                    building_obj = db_models.DbBuildings(
                        project_id=project_id,
                        geom=wkb_element,
                        tags=feature["properties"],
                    )
                    db.add(building_obj)
                    db.commit()

                    success += 1
                except Exception:
                    failure += 1
                    continue

            update_background_task_status_in_database(
                db, background_task_id, 4
            )  # 4 is COMPLETED

        elif feature_type == "lines":
            for feature in features["features"]:
                try:
                    feature_geometry = feature["geometry"]
                    feature_shape = shape(feature_geometry)
                    feature["properties"]["highway"] = "yes"

                    wkb_element = from_shape(feature_shape, srid=4326)
                    db_feature = db_models.DbOsmLines(
                        project_id=project_id,
                        geom=wkb_element,
                        tags=feature["properties"],
                    )

                    db.add(db_feature)
                    db.commit()

                    success += 1
                except Exception:
                    failure += 1
                    continue

            update_background_task_status_in_database(
                db, background_task_id, 4
            )  # 4 is COMPLETED

        return True
    except Exception as e:
        log.warning(str(e))

        # Update background task status to FAILED
        update_background_task_status_in_database(
            db, background_task_id, 2, str(e)
        )  # 2 is FAILED


async def update_project_form(
    db: Session, project_id: int, form_type: str, form: UploadFile = File(None)
):
    project = get_project(db, project_id)
    category = project.xform_title
    project_title = project.project_name_prefix
    odk_id = project.odkid

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project.odk_central_url,
        odk_central_user=project.odk_central_user,
        odk_central_password=project.odk_central_password,
    )

    if form:
        xlsform = f"/tmp/custom_form.{form_type}"
        contents = await form.read()
        with open(xlsform, "wb") as f:
            f.write(contents)
    else:
        xlsform = f"{xlsforms_path}/{category}.xls"

    db.query(db_models.DbFeatures).filter(
        db_models.DbFeatures.project_id == project_id
    ).delete()
    db.commit()

    # OSM Extracts for whole project
    pg = PostgresClient("underpass")
    outfile = (
        f"/tmp/{project_title}_{category}.geojson"  # This file will store osm extracts
    )

    extract_polygon = True if project.data_extract_type == "polygon" else False

    project = table("projects", column("outline"))

    # where = f"id={project_id}
    sql = select(
        geoalchemy2.functions.ST_AsGeoJSON(project.c.outline).label("outline"),
    ).where(text(f"id={project_id}"))
    result = db.execute(sql)
    project_outline = result.first()

    final_outline = json.loads(project_outline.outline)

    outline_geojson = pg.getFeatures(
        boundary=final_outline,
        filespec=outfile,
        polygon=extract_polygon,
        xlsfile=f"{category}.xls",
        category=category,
    )

    updated_outline_geojson = {"type": "FeatureCollection", "features": []}

    # Collect feature mappings for bulk insert
    feature_mappings = []

    for feature in outline_geojson["features"]:
        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature["properties"]["title"] = ""

        feature_shape = shape(feature["geometry"])

        # # If the centroid of the Polygon is not inside the outline, skip the feature.
        # if extract_polygon and (not shape(outline).contains(shape(feature_shape.centroid))):
        #     continue

        wkb_element = from_shape(feature_shape, srid=4326)
        feature_mapping = {
            "project_id": project_id,
            "category_title": category,
            "geometry": wkb_element,
            "properties": feature["properties"],
        }
        updated_outline_geojson["features"].append(feature)
        feature_mappings.append(feature_mapping)

        # Insert features into db
        db_feature = db_models.DbFeatures(
            project_id=project_id,
            category_title=category,
            geometry=wkb_element,
            properties=feature["properties"],
        )
        db.add(db_feature)
        db.commit()

    tasks_list = tasks_crud.get_task_lists(db, project_id)

    for task in tasks_list:
        task_obj = tasks_crud.get_task(db, task)

        # Get the features for this task.
        # Postgis query to filter task inside this task outline and of this project
        # Update those features and set task_id
        query = text(
            f"""UPDATE features
                    SET task_id={task}
                    WHERE id in (

                    SELECT id
                    FROM features
                    WHERE project_id={project_id} and ST_Intersects(geometry, '{task_obj.outline}'::Geometry)

                    )"""
        )

        result = db.execute(query)

        # Get the geojson of those features for this task.
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
                    WHERE project_id={project_id} and task_id={task}
                    ) features;"""
        )

        result = db.execute(query)
        features = result.fetchone()[0]

        xform = f"/tmp/{project_title}_{category}_{task}.xml"  # This file will store xml contents of an xls form.
        extracts = f"/tmp/{project_title}_{category}_{task}.geojson"  # This file will store osm extracts

        # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
        with open(extracts, "w") as jsonfile:
            jsonfile.truncate(0)  # clear the contents of the file
            dump(features, jsonfile)

        outfile = central_crud.generate_updated_xform(xlsform, xform, form_type)

        # Create an odk xform
        result = central_crud.create_odk_xform(
            odk_id, task, xform, odk_credentials, True, True, False
        )

    return True


async def update_odk_credentials(
    project_instance: project_schemas.BETAProjectUpload,
    odk_central_cred: project_schemas.ODKCentral,
    odkid: int,
    db: Session,
):
    project_instance.odkid = odkid
    project_instance.odk_central_url = odk_central_cred.odk_central_url
    project_instance.odk_central_user = odk_central_cred.odk_central_user
    project_instance.odk_central_password = odk_central_cred.odk_central_password

    db.commit()
    db.refresh(project_instance)


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

    # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
    with open(outfile, "w") as jsonfile:
        jsonfile.truncate(0)
        dump(features, jsonfile)


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
        project_id (int): ID of project to create tiles for.
        background_task_id (uuid.UUID): UUID of background task to track.
        source (str): Tile source ("esri", "bing", "topo", "google", "oam").
        output_format (str, optional): Default "mbtiles".
            Other options: "pmtiles", "sqlite3".
        tms (str, optional): Default None. Custom TMS provider URL.
    """
    zooms = "12-19"
    tiles_path_id = uuid.uuid4()
    tiles_dir = f"{TILESDIR}/{tiles_path_id}"
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
        update_background_task_status_in_database(
            db, background_task_id, 4
        )  # 4 is COMPLETED

        log.info(f"Tiles generation process completed for project id {project_id}")

    except Exception as e:
        log.error(f"Tiles generation process failed for project id {project_id}")
        log.error(str(e))

        tile_path_instance.status = 2
        db.commit()

        # Update background task status to FAILED
        update_background_task_status_in_database(
            db, background_task_id, 2, str(e)
        )  # 2 is FAILED


async def get_mbtiles_list(db: Session, project_id: int):
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
        raise HTTPException(status_code=400, detail=str(e))


async def convert_geojson_to_osm(geojson_file: str):
    """Convert a GeoJSON file to OSM format."""
    return json2osm(geojson_file)


def generate_appuser_files_for_janakpur(
    db: Session,
    project_id: int,
    form: str,
    building_extracts_contents: str,
    road_extracts_contents: str,
    category: str,
    form_type: str,
    background_task_id: uuid.UUID,
):
    project_log = log.bind(task="create_project", project_id=project_id)

    project_log.info(f"Starting generate_appuser_files for project {project_id}")

    # Get the project table contents.
    project = table(
        "projects",
        column("project_name_prefix"),
        column("xform_title"),
        column("id"),
        column("odkid"),
        column("odk_central_url"),
        column("odk_central_user"),
        column("odk_central_password"),
        column("outline"),
    )

    where = f"id={project_id}"
    sql = select(
        project.c.project_name_prefix,
        project.c.xform_title,
        project.c.id,
        project.c.odkid,
        project.c.odk_central_url,
        project.c.odk_central_user,
        project.c.odk_central_password,
        geoalchemy2.functions.ST_AsGeoJSON(project.c.outline).label("outline"),
    ).where(text(where))
    result = db.execute(sql)

    # There should only be one match
    if result.rowcount != 1:
        log.warning(str(sql))
        if result.rowcount < 1:
            raise HTTPException(status_code=400, detail="Project not found")
        else:
            raise HTTPException(status_code=400, detail="Multiple projects found")

    one = result.first()

    if one:
        prefix = one.project_name_prefix

        # Get odk credentials from project.
        odk_credentials = {
            "odk_central_url": one.odk_central_url,
            "odk_central_user": one.odk_central_user,
            "odk_central_password": one.odk_central_password,
        }

        odk_credentials = project_schemas.ODKCentral(**odk_credentials)

        xform_title = one.xform_title if one.xform_title else None

        if form:
            xlsform = f"/tmp/custom_form.{form_type}"
            contents = form
            with open(xlsform, "wb") as f:
                f.write(contents)
        else:
            xlsform = f"{xlsforms_path}/{xform_title}.xls"

        category = xform_title

        # FIXME: Need to figure out this step.
        # Data Extracts
        if building_extracts_contents is not None:
            project_log.info("Uploading data extracts")
            upload_custom_data_extracts(db, project_id, building_extracts_contents)

        if road_extracts_contents is not None:
            project_log.info("Uploading roads data")
            upload_custom_data_extracts(
                db, project_id, road_extracts_contents, "highways"
            )

        # Generating QR Code, XForm and uploading OSM Extracts to the form.
        # Creating app users and updating the role of that usegenerate_updated_xformr.
        tasks_list = tasks_crud.get_task_lists(db, project_id)

        project_name = prefix
        odk_id = one.odkid
        project_obj = get_project(db, project_id)

        for task_id in tasks_list:
            # Generate taskFiles
            name = f"{project_name}_{category}_{task_id}"

            appuser = central_crud.create_appuser(odk_id, name, odk_credentials)

            # If app user could not be created, raise an exception.
            if not appuser:
                project_log.error("Couldn't create appuser for project")
                return False

            # prefix should be sent instead of name
            project_log.info(f"Creating qr code for task_id {task_id}")
            create_qr = create_qrcode(
                db,
                odk_id,
                appuser.json()["token"],
                project_name,
                odk_credentials.odk_central_url,
            )

            task = tasks_crud.get_task(db, task_id)
            task.qr_code_id = create_qr["qr_code_id"]
            db.commit()
            db.refresh(task)

            # This file will store xml contents of an xls form.
            xform = f"/tmp/{name}.xml"

            buildings_extracts = (
                f"/tmp/buildings_{name}.geojson"  # This file will store osm extracts
            )
            roads_extracts = (
                f"/tmp/roads_{name}.geojson"  # This file will store osm extracts
            )

            # xform_id_format
            xform_id = f"{name}".split("_")[2]

            # Get the features for this task.
            # Postgis query to filter task inside this task outline and of this project
            # Update those features and set task_id
            query = text(
                f"""UPDATE features
                        SET task_id={task_id}
                        WHERE id IN (
                            SELECT id
                            FROM features
                            WHERE project_id={project_id}
                            AND ST_IsValid(geometry)
                            AND ST_IsValid('{task.outline}'::Geometry)
                            AND ST_Contains('{task.outline}'::Geometry, ST_Centroid(geometry))
                        )"""
            )
            result = db.execute(query)

            # Get the geojson of those features for this task.
            buildings_query = text(
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
                        WHERE project_id={project_id} and task_id={task_id} and category_title='buildings'
                        ) features;"""
            )
            result = db.execute(buildings_query)
            features = result.fetchone()[0]

            highway_query = text(
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
                        WHERE project_id={project_id} and category_title='highways'
                        ) features;"""
            )
            highway_result = db.execute(highway_query)
            highway_features = highway_result.fetchone()[0]

            # upload_media = False if features["features"] is None else True
            upload_media = True

            # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
            with open(buildings_extracts, "w") as jsonfile:
                jsonfile.truncate(0)  # clear the contents of the file
                dump(features, jsonfile)

            # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
            with open(roads_extracts, "w") as jsonfile:
                jsonfile.truncate(0)  # clear the contents of the file
                dump(highway_features, jsonfile)

            project_log.info(f"Generating xform for task {task_id}")
            outfile = central_crud.generate_updated_xform_for_janakpur(
                xlsform, xform, form_type
            )

            # Create an odk xform
            project_log.info(f"Uploading media in {task_id}")
            result = central_crud.create_odk_xform_for_janakpur(
                odk_id, task, outfile, odk_credentials, False, upload_media
            )

            project_log.info(f"Updating role for app user in task {task_id}")
            # Update the user role for the created xform.
            try:
                # Pass odk credentials
                if odk_credentials:
                    url = odk_credentials.odk_central_url
                    user = odk_credentials.odk_central_user
                    pw = odk_credentials.odk_central_password

                else:
                    log.debug("ODKCentral connection variables not set in function")
                    log.debug("Attempting extraction from environment variables")
                    url = settings.ODK_CENTRAL_URL
                    user = settings.ODK_CENTRAL_USER
                    pw = settings.ODK_CENTRAL_PASSWD

                odk_app = OdkAppUser(url, user, pw)

                odk_app.updateRole(
                    projectId=odk_id, xform=xform_id, actorId=appuser.json()["id"]
                )

            except Exception as e:
                log.warning(str(e))

            project_obj.extract_completed_count += 1
            db.commit()
            db.refresh(project_obj)

        # Update background task status to COMPLETED
        update_background_task_status_in_database(
            db, background_task_id, 4
        )  # 4 is COMPLETED


def get_address_from_lat_lon(latitude, longitude):
    """Get address using Nominatim, using lat,lon."""
    base_url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "format": "json",
        "lat": latitude,
        "lon": longitude,
        "zoom": 18,
    }
    headers = {"Accept-Language": "en"}  # Set the language to English

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()
    address = data["address"]["country"]

    if response.status_code == 200:
        if "city" in data["address"]:
            city = data["address"]["city"]
            address = f"{city}" + "," + address
        return address
    else:
        return "Address not found."


def update_project_location_info(
    db_project: sqlalchemy.orm.declarative_base, project_boundary: str
):
    """Update project boundary, centroid, address.

    Args:
        db_project(sqlalchemy.orm.declarative_base): The project database record.
        project_boundary(str): WKT string geometry.
    """
    db_project.outline = project_boundary
    centroid = (wkt.loads(project_boundary)).centroid.wkt
    db_project.centroid = centroid
    geometry = wkt.loads(centroid)
    longitude, latitude = geometry.x, geometry.y
    address = get_address_from_lat_lon(latitude, longitude)
    db_project.location_str = address if address is not None else ""


def convert_geojson_to_epsg4326(input_geojson):
    source_crs = pyproj.CRS(
        input_geojson.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")
    )
    transformer = pyproj.Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)

    # Convert the coordinates to EPSG:4326
    transformed_features = []
    for feature in input_geojson.get("features", []):
        geom = shape(feature.get("geometry", {}))
        transformed_geom = transform(transformer.transform, geom)
        transformed_feature = {
            "type": "Feature",
            "geometry": transformed_geom.__geo_interface__,
            "properties": feature.get("properties", {}),
        }
        transformed_features.append(transformed_feature)

    # Create a new GeoJSON with EPSG:4326
    output_geojson = {"type": "FeatureCollection", "features": transformed_features}

    return output_geojson


def check_crs(input_geojson: dict):
    log.debug("validating coordinate reference system")

    def is_valid_crs(crs_name):
        valid_crs_list = [
            "urn:ogc:def:crs:OGC:1.3:CRS84",
            "urn:ogc:def:crs:EPSG::4326",
            "WGS 84",
        ]
        return crs_name in valid_crs_list

    def is_valid_coordinate(coord):
        return -180 <= coord[0] <= 180 and -90 <= coord[1] <= 90

    error_message = "ERROR: Unsupported coordinate system, it is recommended to use a GeoJSON file in WGS84(EPSG 4326) standard."
    if "crs" in input_geojson:
        crs = input_geojson["crs"]["properties"]["name"]
        if not is_valid_crs(crs):
            log.error(error_message)
            raise HTTPException(status_code=400, detail=error_message)
        return

    if input_geojson["type"] == "FeatureCollection":
        coordinates = input_geojson["features"][0]["geometry"]["coordinates"]
    elif input_geojson["type"] == "Feature":
        coordinates = input_geojson["geometry"]["coordinates"]
    geometry_type = (
        input_geojson["features"][0]["geometry"]["type"]
        if input_geojson["type"] == "FeatureCollection"
        else input_geojson["geometry"]["type"]
    )

    if geometry_type == "MultiPolygon":
        first_coordinate = coordinates[0][0][
            0
        ]  # Get the first coordinate from the first point
    else:
        first_coordinate = coordinates[0][0]

    if not is_valid_coordinate(first_coordinate):
        log.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)


def get_tasks_count(db: Session, project_id: int):
    db_task = (
        db.query(db_models.DbProject)
        .filter(db_models.DbProject.id == project_id)
        .first()
    )
    task_count = len(db_task.tasks)
    return task_count
