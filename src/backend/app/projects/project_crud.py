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


import base64
import io
import json
import logging
import os
import uuid
from base64 import b64encode
from json import dumps, loads
from typing import List
from zipfile import ZipFile


import geoalchemy2
import geojson
import numpy as np
import segno
import shapely.wkb as wkblib
import sqlalchemy
from fastapi import HTTPException, UploadFile, File
from fastapi.logger import logger as logger
from geoalchemy2.shape import from_shape
from geojson import dump
from osm_fieldwork.make_data_extract import PostgresClient
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_fieldwork.xlsforms import xlsforms_path
from shapely import wkt, wkb
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from sqlalchemy import (
    column,
    inspect,
    select,
    table,
    func,
    and_
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from osm_fieldwork.filter_data import FilterData

from ..central import central_crud
from ..config import settings
from ..db import db_models
from ..db.postgis_utils import geometry_to_geojson, timestamp
from ..tasks import tasks_crud
from ..users import user_crud

from . import project_schemas

import requests
import time
import zipfile
from io import BytesIO


# --------------
# ---- CRUD ----
# --------------

QR_CODES_DIR = "QR_codes/"
TASK_GEOJSON_DIR = "geojson/"


def get_projects(
    db: Session, user_id: int, skip: int = 0, limit: int = 100, db_objects: bool = False,
    hashtags: List[str] = None
):
    filters = []
    if user_id:
        filters.append(db_models.DbProject.author_id == user_id) 
        
    if hashtags:
        filters.append(db_models.DbProject.hashtags.op('&&')(hashtags))
        
    if len(filters) > 0:
        db_projects = (
            db.query(db_models.DbProject)
            .filter(and_(*filters))
            .order_by(db_models.DbProject.id.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    else:
        db_projects = (
            db.query(db_models.DbProject)
            .order_by(db_models.DbProject.id.asc())
            .offset(skip).limit(limit).all()
        )
    if db_objects:
        return db_projects
    return convert_to_app_projects(db_projects)


def get_project_summaries(db: Session, user_id: int, skip: int = 0, limit: int = 100, hashtags: str = None):
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

    db_projects = get_projects(db, user_id, skip, limit, True, hashtags)
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
        logger.error(e)
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

    # Check / set credentials
    if odk_credentials:
        url = odk_credentials.odk_central_url
        user = odk_credentials.odk_central_user
        pw = odk_credentials.odk_central_password

    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    # verify data coming in
    if not project_user:
        raise HTTPException("No user passed in")
    if not project_info_1:
        raise HTTPException("No project info passed in")

    # get db user
    db_user = user_crud.get_user(db, project_user.id)
    if not db_user:
        raise HTTPException(
            status_code=400, detail=f"User {project_user.username} does not exist"
        )
    # TODO: get this from logged in user, return 403 (forbidden) if not authorized

    hashtags = list(map(lambda hashtag: hashtag if hashtag.startswith('#') else f"#{hashtag}", hashtags))\
        if hashtags else None
    # create new project
    db_project = db_models.DbProject(
        author=db_user,
        odkid=project_id,
        project_name_prefix=project_info_1.name,
        xform_title=xform_title,
        odk_central_url=url,
        odk_central_user=user,
        odk_central_password=pw,
        hashtags=hashtags
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

        """verify project exists in db"""
        db_project = get_project_by_id(db, project_id)
        if not db_project:
            logger.error(f"Project {project_id} doesn't exist!")
            return False

        """Update the boundary polyon on the database."""
        polygons = boundary["features"]
        for polygon in polygons:

            """If the polygon is a MultiPolygon, convert it to a Polygon"""
            if polygon["geometry"]["type"] == "MultiPolygon":
                polygon["geometry"]["type"] = "Polygon"
                polygon["geometry"]["coordinates"] = polygon["geometry"]["coordinates"][
                    0
                ]

            """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """

            def remove_z_dimension(coord):
                return coord.pop() if len(coord) == 3 else None

            """ Apply the lambda function to each coordinate in its geometry """
            list(map(remove_z_dimension,
                 polygon["geometry"]["coordinates"][0]))

            db_task = db_models.DbTask(
                project_id=project_id,
                outline=wkblib.dumps(shape(polygon["geometry"]), hex=True),
                project_task_index=1,
            )
            db.add(db_task)
            db.commit()

            """ Id is passed in the task_name too. """
            db_task.project_task_name = str(db_task.id)
            db.commit()

        """ Generate project outline from tasks """
        # query = f'''SELECT ST_AsText(ST_Buffer(ST_Union(outline), 0.5, 'endcap=round')) as oval_envelope
        #            FROM tasks
        #           where project_id={project_id};'''

        query = f"""SELECT ST_AsText(ST_ConvexHull(ST_Collect(outline)))
                    FROM tasks
                    WHERE project_id={project_id};"""
        result = db.execute(query)
        data = result.fetchone()

        db_project.outline = data[0]
        db_project.centroid = (wkt.loads(data[0])).centroid.wkt
        db.commit()
        db.refresh(db_project)
        logger.debug("Added project boundary!")

        return True
    except Exception as e:
        logger.error(e)
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
        features = [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": boundary,
                    }]
    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid GeoJSON type: {boundary['type']}"
        )

    """ Apply the lambda function to each coordinate in its geometry ro remove the z-dimension - if it exists"""
    for feature in features:
        list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))

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
        gx, gy = np.linspace(minx, maxx, ny), np.linspace(
            miny, miny + xdiff, ny)
    else:
        gx, gy = np.linspace(minx, minx + ydiff,
                             nx), np.linspace(miny, maxy, nx)
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
    # Filters for osm extracts
    query = {"filters": {
        "tags": {
            "all_geometry": {
                "join_or": {
                    "building": [],
                    "highway": [],
                    "waterway": []
                }
            }
        }
    }}
    
    json_boundary = json.loads(boundary)
    
    if json_boundary.get("features", None) is not None:
        query["geometry"] = json_boundary["features"][0]["geometry"]
    
    else:
        query["geometry"] = json_boundary

    base_url = "https://raw-data-api0.hotosm.org/v1"
    query_url = f"{base_url}/snapshot/"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    result = requests.post(query_url, data=json.dumps(query), headers=headers)

    if result.status_code == 200:
        task_id = result.json()['task_id']
    else:
        return False

    task_url = f"{base_url}/tasks/status/{task_id}"
    # extracts = requests.get(task_url)
    while True:
        result = requests.get(task_url, headers=headers)
        if result.json()['status'] == "PENDING":
            time.sleep(1)
        elif result.json()['status'] == "SUCCESS":
            break

    zip_url = result.json()['result']['download_url']
    zip_url
    result = requests.get(zip_url, headers=headers)
    # result.content
    fp = BytesIO(result.content)
    zfp = zipfile.ZipFile(fp, "r")
    zfp.extract("Export.geojson", "/tmp/")
    data = json.loads(zfp.read("Export.geojson"))

    for feature in data['features']:
        properties = feature['properties']
        tags = properties.pop('tags', {})
        properties.update(tags)

    return data


async def split_into_tasks(
    db: Session, boundary: str, no_of_buildings:int
):

    project_id = uuid.uuid4()

    outline = json.loads(boundary)

    """Update the boundary polyon on the database."""
    # boundary_data = outline["features"][0]["geometry"]
    if outline.get("features", None) is not None:
        boundary_data = outline["features"][0]["geometry"]
    
    else:
        boundary_data = outline
        
    outline = shape(boundary_data)

    db_task = db_models.DbProjectAOI(
        project_id=project_id,
        geom=outline.wkt,
    )

    db.add(db_task)
    db.commit()

    data = get_osm_extracts(boundary)

    for feature in data["features"]:
        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature_shape = shape(feature['geometry'])

        wkb_element = from_shape(feature_shape, srid=4326)

        if feature['properties'].get('building') == 'yes':
            db_feature = db_models.DbBuildings(
                project_id=project_id,
                geom=wkb_element,
                tags=feature["properties"]
                # category="buildings"
            )
            db.add(db_feature)
            db.commit()

        elif 'highway' in feature['properties']:
            db_feature = db_models.DbOsmLines(
                project_id=project_id,
                geom=wkb_element,
                tags=feature["properties"]
            )

            db.add(db_feature)
            db.commit()

    # Get the sql query from split_algorithm sql file
    with open('app/db/split_algorithm.sql', 'r') as sql_file:
        query = sql_file.read()

    # Execute the query with the parameter using the `params` parameter
    result = db.execute(query, params={'num_buildings': no_of_buildings})

    # result = db.execute(query)
    data = result.fetchall()[0]
    final_geojson = data['jsonb_build_object']

    db.query(db_models.DbBuildings).delete()
    db.query(db_models.DbOsmLines).delete()
    db.query(db_models.DbProjectAOI).delete()
    db.commit()

    return final_geojson


# def update_project_boundary(
#     db: Session, project_id: int, boundary: str, dimension: int
# ):
#     # verify project exists in db
#     db_project = get_project_by_id(db, project_id)
#     if not db_project:
#         logger.error(f"Project {project_id} doesn't exist!")
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
#     logger.debug("Added project boundary!")

#     result = create_task_grid(db, project_id=project_id, delta=dimension)

#     tasks = eval(result)
#     for poly in tasks["features"]:
#         logger.debug(poly)
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
        logger.error(f"Project {project_id} doesn't exist!")
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
        features = [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": boundary,
                    }]
    else:
        # Delete the created Project
        db.delete(db_project)
        db.commit()

        # Raise an exception
        raise HTTPException(
            status_code=400, detail=f"Invalid GeoJSON type: {boundary['type']}"
        )

    """ Apply the lambda function to each coordinate in its geometry """
    for feature in features:
        list(map(remove_z_dimension, feature["geometry"]["coordinates"][0]))

    """Update the boundary polyon on the database."""
    outline = shape(features[0]["geometry"])

    # If the outline is a multipolygon, use the first polygon
    if isinstance(outline, MultiPolygon):
        outline = outline.geoms[0]

    db_project.outline = outline.wkt
    db_project.centroid = outline.centroid.wkt

    db.commit()
    db.refresh(db_project)
    logger.debug("Added project boundary!")

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
        logger.debug(poly)
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
        db_project.outline = outline_shape.wkt
        db_project.centroid = outline_shape.centroid.wkt

        # get all task outlines from file
        project_tasks_feature_collection = get_json_from_zip(
            zip,
            task_outlines_filename,
            f"Could not generate FeatureCollection from {task_outlines_filename}",
        )

        # generate task for each feature
        try:
            task_count = 0
            db_project.total_tasks = len(
                project_tasks_feature_collection["features"])
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
    for xls in os.listdir(directory):
        if xls.endswith(".xls") or xls.endswith(".xlsx"):
            xlsforms.append(xls)
    logger.info(xls)
    inspect(db_models.DbXForm)
    forms = table(
        "xlsforms", column("title"), column("xls"), column("xml"), column("id")
    )
    # x = Table('xlsforms', MetaData())
    # x.primary_key.columns.values()

    for xlsform in xlsforms:
        infile = f"{directory}/{xlsform}"
        if os.path.getsize(infile) <= 0:
            logger.warning(f"{infile} is empty!")
            continue
        xls = open(infile, "rb")
        name = xlsform.split(".")[0]
        data = xls.read()
        xls.close()
        # logger.info(xlsform)
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
    logger.info(str(sql))
    result = db.execute(sql)

    # There should only be one match
    if result.rowcount != 1:
        logger.warning(str(sql))
        return False
    project_info = result.first()
    return project_info.odkid


def upload_custom_data_extracts(db: Session,
                                project_id: int,
                                contents: str,
                                category: str = 'buildings',
                                ):
    """
    Uploads custom data extracts to the database.

    Args:
        db (Session): The database session object.
        project_id (int): The ID of the project.
        contents (str): The custom data extracts contents.

    Returns:
        bool: True if the upload is successful.
    """

    project = get_project(db, project_id)

    if not project:
        raise HTTPException(
            status_code=404, detail="Project not found")

    project_geojson = json.loads(
        db.query(func.ST_AsGeoJSON(project.outline)).scalar())

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

        feature_shape = shape(feature['geometry'])

        if not (shape(project_geojson).contains(feature_shape)):
            continue

        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature["properties"]["title"] = ""

        feature_shape = shape(feature['geometry'])

        wkb_element = from_shape(feature_shape, srid=4326)
        feature_mapping = {
            'project_id': project_id,
            'geometry': wkb_element,
            'properties': feature["properties"],
        }
        featuree = db_models.DbFeatures(**feature_mapping)
        db.add(featuree)
        db.commit()

    return True


def generate_task_files(
        db: Session,
        project_id: int,
        task_id: int,
        xlsform: str,
        form_type: str,
        odk_credentials: project_schemas.ODKCentral
):

    project = get_project(db, project_id)
    odk_id = project.odkid
    project_name = project.project_name_prefix
    category = project.xform_title
    name = f"{project_name}_{category}_{task_id}"

    # Create an app user for the task
    appuser = central_crud.create_appuser(odk_id, name, odk_credentials)

    # If app user could not be created, raise an exception.
    if not appuser:
        logger.error(f"Couldn't create appuser for project {project_id}")
        return False

    # prefix should be sent instead of name
    create_qr = create_qrcode(
        db, odk_id, appuser.json(
        )["token"], project_name, odk_credentials.odk_central_url
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
    query = f'''UPDATE features
                SET task_id={task_id}
                WHERE id in (
                
                SELECT id
                FROM features
                WHERE project_id={project_id} and ST_Intersects(geometry, '{task.outline}'::Geometry)

                )'''

    result = db.execute(query)

    # Get the geojson of those features for this task.
    query = f'''SELECT jsonb_build_object(
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
                ) features;'''

    result = db.execute(query)
    features = result.fetchone()[0]

    # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
    with open(extracts, "w") as jsonfile:
        jsonfile.truncate(0)  # clear the contents of the file
        dump(features, jsonfile)

    outfile = central_crud.generate_updated_xform(
        xlsform, xform, form_type)

    # Create an odk xform
    result = central_crud.create_odk_xform(
        odk_id, task_id, outfile, odk_credentials
    )

    # Update the user role for the created xform.
    try:
        # Pass odk credentials
        if odk_credentials:
            url = odk_credentials.odk_central_url
            user = odk_credentials.odk_central_user
            pw = odk_credentials.odk_central_password

        else:
            logger.debug(
                "ODKCentral connection variables not set in function"
            )
            logger.debug("Attempting extraction from environment variables")
            url = settings.ODK_CENTRAL_URL
            user = settings.ODK_CENTRAL_USER
            pw = settings.ODK_CENTRAL_PASSWD

        odk_app = OdkAppUser(url, user, pw)

        odk_app.updateRole(
            projectId=odk_id, xform=xform_id, actorId=appuser.json()["id"]
        )
    except Exception as e:
        logger.warning(str(e))

    project.extract_completed_count += 1
    db.commit()
    db.refresh(project)

    return True


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
        ## Logging ##
        # create file handler
        handler = logging.FileHandler(f"/tmp/{project_id}_generate.log")
        handler.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # add handler to logger
        logger.addHandler(handler)
        logger.info(
            f"Starting generate_appuser_files for project {project_id}")

        # Get the project table contents.
        project = table(
            "projects",
            column("project_name_prefix"),
            column("xform_title"),
            column("id"),
            column("odk_central_url"),
            column("odk_central_user"),
            column("odk_central_password"),
            column("outline")
        )

        where = f"id={project_id}"
        sql = select(
            project.c.project_name_prefix,
            project.c.xform_title,
            project.c.id,
            project.c.odk_central_url,
            project.c.odk_central_user,
            project.c.odk_central_password,

            geoalchemy2.functions.ST_AsGeoJSON(
                project.c.outline).label("outline"),
        ).where(text(where))
        result = db.execute(sql)

        # There should only be one match
        if result.rowcount != 1:
            logger.warning(str(sql))
            if result.rowcount < 1:
                raise HTTPException(
                    status_code=400, detail="Project not found")
            else:
                raise HTTPException(
                    status_code=400, detail="Multiple projects found")

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

            if upload:
                xlsform = f"/tmp/custom_form.{form_type}"
                contents = upload
                with open(xlsform, "wb") as f:
                    f.write(contents)
            else:
                xlsform = f"{xlsforms_path}/{xform_title}.xls"

            category = xform_title

            # Data Extracts
            if extracts_contents is not None:
                upload_custom_data_extracts(db, project_id, extracts_contents)

            else:

                # OSM Extracts for whole project
                pg = PostgresClient(
                    'https://raw-data-api0.hotosm.org/v1', "underpass")
                # This file will store osm extracts
                outfile = f"/tmp/{prefix}_{xform_title}.geojson"

                outline = json.loads(one.outline)
                outline_geojson = pg.getFeatures(boundary=outline,
                                                 filespec=outfile,
                                                 polygon=extract_polygon,
                                                 xlsfile=f'{category}.xls',
                                                 category=category
                                                 )

                updated_outline_geojson = {
                    "type": "FeatureCollection",
                    "features": []}

                # Collect feature mappings for bulk insert
                feature_mappings = []

                for feature in outline_geojson["features"]:

                    # If the osm extracts contents do not have a title, provide an empty text for that.
                    feature["properties"]["title"] = ""

                    feature_shape = shape(feature['geometry'])

                    # If the centroid of the Polygon is not inside the outline, skip the feature.
                    if extract_polygon and (not shape(outline).contains(shape(feature_shape.centroid))):
                        continue

                    wkb_element = from_shape(feature_shape, srid=4326)
                    feature_mapping = {
                        'project_id': project_id,
                        'category_title': category,
                        'geometry': wkb_element,
                        'properties': feature["properties"],
                    }
                    updated_outline_geojson['features'].append(feature)
                    feature_mappings.append(feature_mapping)

                # Bulk insert the osm extracts into the db.
                db.bulk_insert_mappings(db_models.DbFeatures, feature_mappings)

            # Generating QR Code, XForm and uploading OSM Extracts to the form.
            # Creating app users and updating the role of that user.
            tasks_list = tasks_crud.get_task_lists(db, project_id)

            for task in tasks_list:
                generate_task_files(db, project_id, task,
                                    xlsform, form_type, odk_credentials)

        # Update background task status to COMPLETED
        update_background_task_status_in_database(
            db, background_task_id, 4
        )  # 4 is COMPLETED

    except Exception as e:
        logger.warning(str(e))

        # Update background task status to FAILED
        update_background_task_status_in_database(
            db, background_task_id, 2, str(e)
        )  # 2 is FAILED


def create_qrcode(
    db: Session,
    project_id: int,
    token: str,
    project_name: str,
    odk_central_url: str = None,
):
    # Make QR code for an app_user.
    qrcode = central_crud.create_qrcode(
        project_id, token, project_name, odk_central_url
    )
    qrcode = segno.make(qrcode, micro=False)
    image_name = f"{project_name}.png"
    with open(image_name, "rb") as f:
        base64_data = b64encode(f.read()).decode()
    qr_code_text = base64.b64decode(base64_data)
    qrdb = db_models.DbQrCode(image=qr_code_text, filename=image_name)
    db.add(qrdb)
    db.commit()
    codes = table("qr_code", column("id"))
    sql = select(sqlalchemy.func.count(codes.c.id))
    result = db.execute(sql)
    rows = result.fetchone()[0]
    return {"data": qrcode, "id": rows + 1, "qr_code_id": qrdb.id}


def get_project_geometry(db: Session,
                         project_id: int):
    """
    Retrieves the geometry of a project.

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
        logger.warning(str(sql))
        return False
    row = eval(result.first()[0])
    return json.dumps(row)


def get_task_geometry(db: Session,
                      project_id: int):
    """
    Retrieves the geometry of tasks associated with a project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.

    Returns:
        str: A geojson of the task boundaries
    """

    tasks = table("tasks", column("outline"),
                  column("project_id"), column("id"))
    where = f"project_id={project_id}"
    sql = select(geoalchemy2.functions.ST_AsGeoJSON(tasks.c.outline)).where(
        text(where)
    )
    result = db.execute(sql)

    features = []
    for row in result:
        geometry = json.loads(row[0])
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {}
        }
        features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    return json.dumps(feature_collection)


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
            logger.warning(str(sql))
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
            gx, gy = np.linspace(minx, maxx, ny), np.linspace(
                miny, miny + xdiff, ny)
        else:
            gx, gy = np.linspace(minx, minx + ydiff,
                                 nx), np.linspace(miny, maxy, nx)

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
        logger.error(e)


def get_json_from_zip(zip, filename: str, error_detail: str):
    try:
        with zip.open(filename) as file:
            data = file.read()
            return json.loads(data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"{error_detail} ----- Error: {e}")


def get_outline_from_geojson_file_in_zip(
    zip, filename: str, error_detail: str, feature_index: int = 0
):
    try:
        with zip.open(filename) as file:
            data = file.read()
            json_dump = json.loads(data)
            feature_collection = geojson.FeatureCollection(json_dump)
            feature = feature_collection["features"][feature_index]
            geom = feature["geometry"]
            shape_from_geom = shape(geom)
            return shape_from_geom
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ----",
        ) from e


def get_shape_from_json_str(feature: str, error_detail: str):
    try:
        geom = feature["geometry"]
        return shape(geom)
    except Exception as e:
        logger.error(e)
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
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=f"{error_detail} ----- Error: {e}"
        ) from e


# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these


def convert_to_app_project(db_project: db_models.DbProject):
    if db_project:
        app_project: project_schemas.Project = db_project

        if db_project.outline:
            app_project.outline_geojson = geometry_to_geojson(
                db_project.outline, {"id": db_project.id}, db_project.id)

        app_project.project_tasks = tasks_crud.convert_to_app_tasks(
            db_project.tasks)

        return app_project
    else:
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
            summary.title = default_project_info.name
            summary.description = default_project_info.short_description

        summary.num_contributors = (
            db_project.tasks_mapped + db_project.tasks_validated
        )  # TODO: get real number of contributors

        return summary
    else:
        return None


def convert_to_project_summaries(db_projects: List[db_models.DbProject]):
    if db_projects and len(db_projects) > 0:
        project_summaries = []
        for project in db_projects:
            if project:
                project_summaries.append(convert_to_project_summary(project))
        app_projects_without_nones = [
            i for i in project_summaries if i is not None]
        return app_projects_without_nones
    else:
        return []


def convert_to_project_feature(db_project_feature: db_models.DbFeatures):
    if db_project_feature:
        app_project_feature: project_schemas.Feature = db_project_feature

        if db_project_feature.geometry:
            app_project_feature.geometry = geometry_to_geojson(
                db_project_feature.geometry, {
                    id: db_project_feature.id}, db_project_feature.id
            )

        return app_project_feature
    else:
        return None


def convert_to_project_features(db_project_features: List[db_models.DbFeatures]):
    if db_project_features and len(db_project_features) > 0:
        app_project_features = []
        for project_feature in db_project_features:
            if project_feature:
                app_project_features.append(
                    convert_to_project_feature(project_feature))
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
    db: Session, task_id: uuid.UUID, name: str = None
):
    """Inserts a new task into the database
    Params:
        db: database session
        task_id: uuid of the task
        name: name of the task.
    """
    task = db_models.BackgroundTasks(
        id=str(task_id), name=name, status=1
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
    ).update({
        db_models.BackgroundTasks.status: status,
        db_models.BackgroundTasks.message: message
    })
    db.commit()

    return True


def add_features_into_database(
    db: Session, project_id: int, features: dict, background_task_id: uuid.UUID
):
    """Inserts a new task into the database
    Params:
          db: database session
          project_id: id of the project
          features: features to be added.
    """
    success = 0
    failure = 0
    for feature in features["features"]:
        try:
            feature_geometry = feature["geometry"]
            feature_shape = shape(feature_geometry)

            wkb_element = from_shape(feature_shape, srid=4326)
            feature_obj = db_models.DbFeatures(
                project_id=project_id,
                category_title="buildings",
                geometry=wkb_element,
                task_id=1,
                properties=feature["properties"],
            )
            db.add(feature_obj)
            db.commit()
            success += 1
        except Exception:
            failure += 1
            continue

    update_background_task_status_in_database(
        db, background_task_id, 4
    )  # 4 is COMPLETED

    return True


async def update_project_form(
        db: Session,
        project_id: int,
        form_type: str,
        form: UploadFile = File(None)
        ):

    project = get_project(db, project_id)
    category = project.xform_title
    project_title = project.project_name_prefix
    odk_id = project.odkid

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url = project.odk_central_url,
        odk_central_user = project.odk_central_user,
        odk_central_password = project.odk_central_password,
        )


    if form:
        xlsform = f"/tmp/custom_form.{form_type}"
        contents = await form.read()
        with open(xlsform, "wb") as f:
            f.write(contents)
    else:
        xlsform = f"{xlsforms_path}/{category}.xls"

    db.query(db_models.DbFeatures).filter(db_models.DbFeatures.project_id == project_id).delete()
    db.commit()

    # OSM Extracts for whole project
    pg = PostgresClient('https://raw-data-api0.hotosm.org/v1', "underpass")
    outfile = f"/tmp/{project_title}_{category}.geojson"  # This file will store osm extracts

    extract_polygon = True if project.data_extract_type == 'polygon' else False

    project = table(
        "projects", 
        column("outline")
    )

    # where = f"id={project_id}
    sql = select(
                geoalchemy2.functions.ST_AsGeoJSON(project.c.outline).label("outline"),
                ).where(text(f"id={project_id}"))
    result = db.execute(sql)
    project_outline = result.first()

    final_outline = json.loads(project_outline.outline)

    outline_geojson = pg.getFeatures(boundary = final_outline, 
                                        filespec = outfile,
                                        polygon = extract_polygon,
                                        xlsfile = f'{category}.xls',
                                        category = category
                                        )


    updated_outline_geojson = {
        "type": "FeatureCollection",
        "features": []}

    # Collect feature mappings for bulk insert
    feature_mappings = []

    for feature in outline_geojson["features"]:

        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature["properties"]["title"] = ""

        feature_shape = shape(feature['geometry'])

        # # If the centroid of the Polygon is not inside the outline, skip the feature.
        # if extract_polygon and (not shape(outline).contains(shape(feature_shape.centroid))):
        #     continue

        wkb_element = from_shape(feature_shape, srid=4326)
        feature_mapping = {
            'project_id': project_id,
            'category_title': category,
            'geometry': wkb_element,
            'properties': feature["properties"],
        }
        updated_outline_geojson['features'].append(feature)
        feature_mappings.append(feature_mapping)

        # Insert features into db
        db_feature = db_models.DbFeatures(
            project_id=project_id,
            category_title = category,
            geometry=wkb_element,
            properties=feature["properties"]
        )
        db.add(db_feature)
        db.commit()

    tasks_list = tasks_crud.get_task_lists(db, project_id)

    for task in tasks_list:

        task_obj = tasks_crud.get_task(db, task)

        # Get the features for this task.
        # Postgis query to filter task inside this task outline and of this project
        # Update those features and set task_id
        query = f'''UPDATE features
                    SET task_id={task}
                    WHERE id in (
                    
                    SELECT id
                    FROM features
                    WHERE project_id={project_id} and ST_Intersects(geometry, '{task_obj.outline}'::Geometry)

                    )'''

        result = db.execute(query)

        # Get the geojson of those features for this task.
        query = f'''SELECT jsonb_build_object(
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
                    ) features;'''


        result = db.execute(query)
        features = result.fetchone()[0]

        xform = f"/tmp/{project_title}_{category}_{task}.xml"  # This file will store xml contents of an xls form.
        extracts = f"/tmp/{project_title}_{category}_{task}.geojson"  # This file will store osm extracts

        # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
        with open(extracts, "w") as jsonfile:
            jsonfile.truncate(0)  # clear the contents of the file
            dump(features, jsonfile)


        outfile = central_crud.generate_updated_xform(
            xlsform, xform, form_type)

        # Create an odk xform
        result = central_crud.create_odk_xform(
            odk_id,
            task, 
            xform, 
            odk_credentials, 
            True, 
            True, 
            False
        )

    return True


async def update_odk_credentials(project_instance: project_schemas.BETAProjectUpload, 
                          odk_central_cred: project_schemas.ODKCentral,
                          odkid: int, db: Session):
    project_instance.odkid = odkid
    project_instance.odk_central_url = odk_central_cred.odk_central_url
    project_instance.odk_central_user = odk_central_cred.odk_central_user
    project_instance.odk_central_password = odk_central_cred.odk_central_password
    
    db.commit()
    db.refresh(project_instance)


async def get_extracted_data_from_db(db:Session, project_id:int, outfile:str):

    """Get the geojson of those features for this project"""

    query = f'''SELECT jsonb_build_object(
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
                ) features;'''

    result = db.execute(query)
    features = result.fetchone()[0]

    # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
    with open(outfile, "w") as jsonfile:
        jsonfile.truncate(0)
        dump(features, jsonfile)
