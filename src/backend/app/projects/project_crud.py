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
from fastapi import HTTPException, UploadFile
from fastapi.logger import logger as logger
from geoalchemy2.shape import from_shape
from geojson import dump
from osm_fieldwork.make_data_extract import PostgresClient
from osm_fieldwork.OdkCentral import OdkAppUser
from osm_fieldwork.xlsforms import xlsforms_path
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from sqlalchemy import (
    column,
    inspect,
    select,
    table,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from ..central import central_crud
from ..config import settings
from ..db import db_models
from ..db.postgis_utils import geometry_to_geojson, timestamp
from ..tasks import tasks_crud
from ..users import user_crud

# from ..osm_fieldwork.make_data_extract import PostgresClient, OverpassClient
from . import project_schemas

# --------------
# ---- CRUD ----
# --------------

QR_CODES_DIR = "QR_codes/"
TASK_GEOJSON_DIR = "geojson/"


def get_projects(
    db: Session, user_id: int, skip: int = 0, limit: int = 100, db_objects: bool = False
):
    if user_id:
        db_projects = (
            db.query(db_models.DbProject)
            .filter(db_models.DbProject.author_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:

        db_projects = db.query(db_models.DbProject).offset(skip).limit(limit).all()
    if db_objects:
        return db_projects
    return convert_to_app_projects(db_projects)


def get_project_summaries(db: Session, user_id: int, skip: int = 0, limit: int = 100):
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

    db_projects = get_projects(db, user_id, skip, limit, True)
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

    # create new project
    db_project = db_models.DbProject(
        author=db_user,
        odkid=project_id,
        project_name_prefix=project_info_1.name,
        xform_title=xform_title,
        odk_central_url=url,
        odk_central_user=user,
        odk_central_password=pw,
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
            list(map(remove_z_dimension, polygon["geometry"]["coordinates"][0]))

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


async def split_into_tasks(
    db: Session, project_id: int, boundary: str   
    ):

    # verify project exists in db
    db_project = get_project(db, project_id)
    if not db_project:
        logger.error(f"Project {project_id} doesn't exist!")
        return False

    outline = json.loads(boundary)

    """Update the boundary polyon on the database."""
    boundary_data = outline["features"][0]["geometry"]
    outline = shape(boundary_data)

    # Update the project outline and centroid in project table.
    db_project.outline = outline.wkt
    db_project.centroid = outline.centroid.wkt
    db.commit()
    db.refresh(db_project)


    # Filters for osm extracts
    query={"filters":{
            "tags": {
                "all_geometry": {
                    "join_or": {
                        "building":[],
                        "highway": [],
                        "waterway":[]     
                        }
                    }
                }
            },
            "geometryType": [
                "polygon",
                "line",
                "line"
            ],
            "centroid": "false"
        }
    query["geometry"] = json.loads(boundary)["features"][0]["geometry"]

    base_url = "https://raw-data-api0.hotosm.org/v1"
    query_url = f"{base_url}/snapshot/"
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    import requests
    import time
    import zipfile
    from io import BytesIO

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
    data = eval(zfp.read("Export.geojson"))

    for feature in data["features"]:
        
        # If the osm extracts contents do not have a title, provide an empty text for that.
        feature_shape = shape(feature['geometry'])

        wkb_element = from_shape(feature_shape, srid=4326)

        if feature['properties']['tags'].get('building') == 'yes':
            db_feature = db_models.DbFeatures(
                project_id=project_id,
                geometry=wkb_element,
                properties=feature["properties"]
                # category="buildings"
            )
            db.add(db_feature)
            db.commit()

        else:
            db_feature = db_models.DbOsmLines(
                project_id=project_id,
                geometry=wkb_element,
                properties=feature["properties"]
            )

            db.add(db_feature)
            db.commit()


    query = f"""    
        WITH boundary AS (
        SELECT ST_Boundary(outline) AS geom
        FROM "projects" WHERE id={project_id}
        ),
        splitlines AS (
        SELECT ST_Intersection(a.outline, l.geometry) AS geom
        FROM "projects" a, "osm_lines" l
        WHERE a.id={project_id} and l.project_id={project_id}
        AND ST_Intersects(a.outline, l.geometry)
        ),
        merged AS (
        SELECT ST_LineMerge(ST_Union(splitlines.geom)) AS geom
        FROM splitlines
        ),
        comb AS (
        SELECT ST_Union(boundary.geom, merged.geom) AS geom
        FROM boundary, merged
        ),
        splitpolysnoindex AS (
        SELECT (ST_Dump(ST_Polygonize(comb.geom))).geom as geom
        FROM comb
        )
        -- Add row numbers to function as temporary unique IDs for our new polygons
        SELECT row_number () over () as polyid, * 
        from splitpolysnoindex

        """


    # query = f"""
    # WITH boundary AS (
    # SELECT ST_Boundary(outline) AS geom
    # FROM "projects" WHERE id={project_id}
    # ),
    # splitlines AS (
    # SELECT ST_Intersection(a.outline, l.geometry) AS geom
    # FROM "projects" a, "osm_lines" l
    # where a.id={project_id} and l.project_id={project_id}
    # and ST_Intersects(a.outline, l.geometry)
    # -- AND (tags->>'highway' = 'primary' OR tags->>'waterway' = 'river')
    # ),
    # merged AS (
    # SELECT ST_LineMerge(ST_Union(splitlines.geom)) AS geom
    # FROM splitlines
    # ),
    # comb AS (
    # SELECT ST_Union(boundary.geom, merged.geom) AS geom
    # FROM boundary, merged
    # ),
    # polygons AS (
    # SELECT (ST_Dump(ST_Polygonize(comb.geom))).geom AS geom
    # FROM comb
    # ),
    # buildings AS (
    # SELECT *
    # FROM "features"
    # where project_id={project_id}
    # -- and tags->>'building' IS NOT NULL
    # ),
    # polbuild AS(
    # SELECT buildings.geometry
    # FROM buildings
    # JOIN polygons ON st_contains(polygons.geom, buildings.geometry)
    # WHERE polygons.geom IN (
    #     SELECT polygons.geom
    #     FROM polygons
    #     ORDER BY polygons.geom 
    #     OFFSET 66 LIMIT 1
    # )),
    # points as(
    # SELECT  st_centroid(geometry) AS geom
    # FROM polbuild
    # ),
    # clusters AS (
    # SELECT ST_ClusterKMeans(geometry, 15) OVER () AS cid, geometry
    # FROM polbuild
    # ),
    # polycluster AS(
    # select polbuild.geometry,cid from polbuild join clusters on st_contains( polbuild.geometry, clusters.geometry) group by cid, polbuild.geometry),

    # polyboundary AS (
    # SELECT ST_ConvexHull(ST_Collect(polycluster.geometry)) AS geom
    # FROM polycluster group by cid
    # )
    # SELECT polyboundary.geom
    # FROM polyboundary;
    # """

    return data

    # result = db.execute(query)
    # geom_data = result.fetchall()

    # for geom in geom_data:
    #     # Add tasks in the database
    #     db_task = db_models.DbTask(
    #         project_id=project_id,
    #         outline=geom[1]
    #     )

    #     db.add(db_task)
    #     db.commit()

    #     """ Id is passed in the task_name too. """
    #     db_task.project_task_name = str(db_task.id)
    #     db.commit()

    # return data


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


def generate_appuser_files(
    db: Session,
    project_id: int,
    extract_polygon: bool,
    upload: str,
    category: str,
    background_task_id: uuid.UUID,
):
    """Generate the files for each appuser.

    QR code, new XForm, and the OSM data extract.
    """
    try:
        ## Logging ##
        # create file handler
        handler = logging.FileHandler(f"{project_id}_generate.log")
        handler.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # add handler to logger
        logger.addHandler(handler)
        logger.info(f"Starting generate_appuser_files for project {project_id}")

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
        )
        where = f"id={project_id}"
        sql = select(project).where(text(where))
        result = db.execute(sql)

        # There should only be one match
        if result.rowcount != 1:
            logger.warning(str(sql))
            if result.rowcount < 1:
                raise HTTPException(status_code=400, detail="Project not found")
            else:
                raise HTTPException(status_code=400, detail="Multiple projects found")

        one = result.first()
        if one:
            prefix = one.project_name_prefix

            task = table("tasks", column("outline"), column("id"))
            where = f"project_id={project_id}"
            sql = select(
                task.c.id,
                geoalchemy2.functions.ST_AsGeoJSON(task.c.outline).label("outline"),
            ).where(text(where))
            result = db.execute(sql)

            # Get odk project id, and odk credentials from project.
            odk_id = one.odkid
            odk_credentials = {
                "odk_central_url": one.odk_central_url,
                "odk_central_user": one.odk_central_user,
                "odk_central_password": one.odk_central_password,
            }

            xform_title = one.xform_title if one.xform_title else None

            if upload:
                xlsform = "/tmp/custom_form.xls"
                contents = upload
                with open(xlsform, "wb") as f:
                    f.write(contents)
            else:
                xlsform = f"{xlsforms_path}/{xform_title}.xls"

            category = xform_title
            for poly in result.fetchall():
                name = f"{prefix}_{category}_{poly.id}"

                # Create an app user for the task
                appuser = central_crud.create_appuser(odk_id, name, odk_credentials)

                # If app user could not be created, raise an exception.
                if not appuser:
                    logger.error(f"Couldn't create appuser for project {project_id}")
                    raise HTTPException(
                        status_code=400, detail="Could not create appuser"
                    )

                # prefix should be sent instead of name
                create_qr = create_qrcode(
                    db, odk_id, appuser.json()["token"], prefix, odk_credentials
                )

                xform = f"/tmp/{prefix}_{xform_title}_{poly.id}.xml"  # This file will store xml contents of an xls form.
                outfile = f"/tmp/{prefix}_{xform_title}_{poly.id}.geojson"  # This file will store osm extracts

                # xform_id_format
                xform_id = f"{prefix}_{xform_title}_{poly.id}".split("_")[2]

                outline = eval(poly.outline)

                # Generating an osm extract from the underpass database.
                pg = PostgresClient("https://raw-data-api0.hotosm.org/v1", "underpass")
                outline = eval(poly.outline)

                outline_geojson = pg.getFeatures(
                    boundary=outline,
                    filespec=outfile,
                    polygon=extract_polygon,
                    # xlsfile =  f'{category}.xls' if not upload else xlsform,
                    xlsfile=f"{category}.xls",
                    category=category,
                )

                updated_outline_geojson = {"type": "FeatureCollection", "features": []}

                # If the osm extracts contents does not have title, provide an empty text for that.
                for feature in outline_geojson["features"]:
                    feature["properties"]["title"] = ""

                    # Insert the osm extracts into the database.
                    feature_shape = shape(feature["geometry"])

                    # If the centroid of the Polygon is not inside the outline, skip the feature.
                    if not shape(outline).contains(shape(feature_shape.centroid)):
                        continue

                    wkb_element = from_shape(feature_shape, srid=4326)
                    feature_obj = db_models.DbFeatures(
                        project_id=project_id,
                        task_id=poly.id,
                        category_title=category,
                        geometry=wkb_element,
                        properties=feature["properties"],
                    )
                    updated_outline_geojson["features"].append(feature)
                    db.add(feature_obj)
                    db.commit()

                # Update outfile containing osm extracts with the new geojson contents containing title in the properties.
                with open(outfile, "w") as jsonfile:
                    jsonfile.truncate(0)  # clear the contents of the file
                    dump(updated_outline_geojson, jsonfile)

                outfile = central_crud.generate_updated_xform(
                    db, poly.id, xlsform, xform
                )

                # Update tasks table qith qr_Code id
                task = tasks_crud.get_task(db, poly.id)
                task.qr_code_id = create_qr["qr_code_id"]
                db.commit()
                db.refresh(task)

                # Create an odk xform
                result = central_crud.create_odk_xform(
                    odk_id, poly.id, outfile, odk_credentials
                )

                # Update the user role for the created xform.
                try:
                    # Pass odk credentials
                    if odk_credentials:
                        url = odk_credentials["odk_central_url"]
                        user = odk_credentials["odk_central_user"]
                        pw = odk_credentials["odk_central_password"]

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
                        projectId=one[3], xform=xform_id, actorId=appuser.json()["id"]
                    )
                except Exception as e:
                    logger.warning(str(e))

                # Add the count of completed task in project table extract_completed_count column.
                project = get_project_by_id(db, project_id)
                project.extract_completed_count += 1
                db.commit()
                db.refresh(project)

        # Update background task status to COMPLETED
        update_background_task_status_in_database(
            db, background_task_id, 4
        )  # 4 is COMPLETED

    except Exception as e:
        logger.warning(str(e))

        # Update background task status to FAILED
        update_background_task_status_in_database(
            db, background_task_id, 2
        )  # 2 is FAILED


def create_qrcode(
    db: Session,
    project_id: int,
    token: str,
    project_name: str,
    odk_credentials: dict = None,
):
    # Make QR code for an app_user.
    qrcode = central_crud.create_qrcode(
        project_id, token, project_name, odk_credentials
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


def download_geometry(
    db: Session,
    project_id: int,
    download_type: bool,
):
    """Download the project or task boundaries from the database."""
    data = list()
    if not download_type:
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
        row["id"] = project_id
        data.append(row)
    else:
        task = table("tasks", column("outline"), column("project_id"), column("id"))
        where = f"project_id={project_id}"
        sql = select(
            task.c.id,
            geoalchemy2.functions.ST_AsGeoJSON(task.c.outline).label("outline"),
        ).where(text(where))
        result = db.execute(sql)
        for item in result.fetchall():
            poly = eval(item.outline)
            poly["id"] = item.id
            data.append(poly)
    collection = geojson.FeatureCollection(data)
    out = dumps(collection)

    return {"filespec": out}


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
        logger.error(e)


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
            app_project.outline_geojson = geometry_to_geojson(db_project.outline)

        app_project.project_tasks = tasks_crud.convert_to_app_tasks(db_project.tasks)

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
        app_projects_without_nones = [i for i in project_summaries if i is not None]
        return app_projects_without_nones
    else:
        return []


def convert_to_project_feature(db_project_feature: db_models.DbFeatures):
    if db_project_feature:
        app_project_feature: project_schemas.Feature = db_project_feature

        if db_project_feature.geometry:
            app_project_feature.geometry = geometry_to_geojson(
                db_project_feature.geometry
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
    return task.status


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
    db: Session, task_id: uuid.UUID, status: int
):
    """Updates the status of a task in the database
    Params:
        db: database session
        task_id: uuid of the task
        status: status of the task.
    """
    db.query(db_models.BackgroundTasks).filter(
        db_models.BackgroundTasks.id == str(task_id)
    ).update({db_models.BackgroundTasks.status: status})
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
