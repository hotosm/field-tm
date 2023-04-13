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
from json import dumps, loads
from typing import List
from zipfile import ZipFile
import base64
import segno
from base64 import b64encode

import geoalchemy2
import geojson
import numpy as np
import shapely.wkb as wkblib
import sqlalchemy
from fastapi import HTTPException, UploadFile
from fastapi.logger import logger as logger
from osm_fieldwork.xlsforms import xlsforms_path
from shapely.geometry import Polygon, shape
from osm_fieldwork.OdkCentral import OdkAppUser
from shapely import wkt
from sqlalchemy import (
    column,
    insert,
    inspect,
    select,
    table,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from geojson import dump

from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.make_data_extract import PostgresClient, OverpassClient

from ..db.postgis_utils import geometry_to_geojson, timestamp
from ..central import central_crud
from ..db import db_models
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
        raise HTTPException(e)
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
        )

    # Get project info
    db_project_info = get_project_info_by_id(db, project_id)

    # Update project informations 
    if project_metadata.name:
        db_project.project_name_prefix = project_metadata.name
        db_project_info.name = project_metadata.name
    if project_metadata.description:
        db_project_info.description=project_metadata.description
    if project_metadata.short_description:
        db_project_info.short_description=project_metadata.short_description

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
    db_project_info.short_description=project_info_1.short_description
    db_project_info.description=project_info_1.description

    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)


def create_project_with_project_info(
    db: Session, project_metadata: project_schemas.BETAProjectUpload, project_id
):
    user = project_metadata.author
    project_info_1 = project_metadata.project_info
    xform_title = project_metadata.xform_title
    odk_credentials = project_metadata.odk_central
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
    # TODO: get this from logged in user, return 403 (forbidden) if not authorized

    # create new project
    db_project = db_models.DbProject(
        author=db_user,
        odkid=project_id,
        project_name_prefix=project_info_1.name,
        xform_title= xform_title,
        odk_central_url = odk_credentials.odk_central_url,
        odk_central_user = odk_credentials.odk_central_user,
        odk_central_password = odk_credentials.odk_central_password,

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
    project_id: int,
    xlsform: str,
    name: str,
):
    try:
        forms = table(
            "xlsforms", column("title"), column("xls"), column("xml"), column("id")
        )
        ins = insert(forms).values(title=name, xls=xlsform)
        sql = ins.on_conflict_do_update(
            constraint="xlsforms_title_key", set_=dict(title=name, xls=xlsform)
        )
        db.execute(sql)
        db.commit()
        return True
    except Exception as e:
        raise HTTPException(status=400, detail={'message':str(e)})


def update_multi_polygon_project_boundary(
    db: Session,
    project_id: int,
    boundary: str,        
):
    """
        This function receives the project_id and boundary as a parameter
        and creates a task for each polygon in the database. 
        This function also creates a project outline from the multiple polygons received.
    """

    try:
        """ verify project exists in db """
        db_project = get_project_by_id(db, project_id)
        if not db_project:
            logger.error(f"Project {project_id} doesn't exist!")
            return False

        """Update the boundary polyon on the database."""
        polygons = boundary["features"]
        for polygon in polygons:

            """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """
            remove_z_dimension = lambda coord: coord.pop() if len(coord) == 3 else None

            """ Apply the lambda function to each coordinate in its geometry """
            list(map(remove_z_dimension, polygon['geometry']['coordinates'][0]))

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

        query = f'''SELECT ST_AsText(ST_ConvexHull(ST_Collect(outline)))
                    FROM tasks
                    WHERE project_id={project_id};'''
        result = db.execute(query)
        data = result.fetchone()

        db_project.outline = data[0]
        db_project.centroid = (wkt.loads(data[0])).centroid.wkt
        db.commit()
        db.refresh(db_project)
        logger.debug("Added project boundary!")

        return True
    except Exception as e:
        raise HTTPException(e)


def update_project_boundary(
    db: Session,
    project_id: int,
    boundary: str,
    dimension : int
):
    """Use a lambda function to remove the "z" dimension from each coordinate in the feature's geometry """
    remove_z_dimension = lambda coord: coord.pop() if len(coord) == 3 else None

    """ Apply the lambda function to each coordinate in its geometry """
    for feature in boundary['features']:
        list(map(remove_z_dimension, feature['geometry']['coordinates'][0]))

    """Update the boundary polyon on the database."""
    outline = shape(boundary["features"][0]["geometry"])

    # verify project exists in db
    db_project = get_project_by_id(db, project_id)
    if not db_project:
        logger.error(f"Project {project_id} doesn't exist!")
        return False

    db_project.outline = outline.wkt
    db_project.centroid = outline.centroid.wkt

    db.commit()
    db.refresh(db_project)
    logger.debug("Added project boundary!")

    result = create_task_grid(db, project_id=project_id, delta=dimension)

    tasks = eval(result)
    for poly in tasks["features"]:
        logger.debug(poly)
        task_name = str(poly['properties']['id'])
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



def get_odk_id_for_project(
        db: Session,
        project_id:int
        ):
    
    """
    Get the odk project id for the fmtm project id
    """
    
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
    # dbname: str,
    category: str,
    project_id: int,
):
    """Generate the files for each appuser, the qrcode, the new XForm,
    and the OSM data extract.
    """
    project = table(
        "projects", column("project_name_prefix"), 
        column("xform_title"), 
        column("id"), 
        column("odkid"),
        column("odk_central_url"),
        column("odk_central_user"),
        column("odk_central_password"),
    )
    where = f"id={project_id}"
    sql = select(project).where(text(where))
    logger.info(str(sql))
    result = db.execute(sql)
    # There should only be one match
    if result.rowcount != 1:
        logger.warning(str(sql))
        return False
    one = result.first()
    if one:
        prefix = one.project_name_prefix
        if not one.xform_title:
            xform_title = category
        else:
            xform_title = one.xform_title
        task = table("tasks", column("outline"), column("id"))
        where = f"project_id={project_id}"
        sql = select(
            task.c.id,
            geoalchemy2.functions.ST_AsGeoJSON(task.c.outline).label("outline"),
        ).where(text(where))
        result = db.execute(sql)

        # Get odk project id, and odk credentials from project. 
        odk_id = one.odkid
        odk_credentials={
            'odk_central_url' : one.odk_central_url,
            'odk_central_user' : one.odk_central_user,
            'odk_central_password' : one.odk_central_password
        }
        for poly in result.fetchall():
            # poly = result.first()
            name = f"{prefix}_{category}_{poly.id}"
            # appuser = central_crud.create_appuser(project_id, name)
            appuser = central_crud.create_appuser(odk_id, name, odk_credentials)

            if not appuser:
                logger.error(f"Couldn't create appuser for project {project_id}")
                return None

            #prefix should be sent instead of name
            create_qr = create_qrcode(db, odk_id, appuser.json()["token"], prefix, odk_credentials)

            # create_qr = create_qrcode(db, project_id, appuser.json()["token"], f"/tmp/{name}")
            xlsform = f"{xlsforms_path}/{xform_title}.xls"
            xform = f"/tmp/{prefix}_{xform_title}_{poly.id}.xml"
            outfile = f"/tmp/{prefix}_{xform_title}_{poly.id}.geojson"
            # pg = PostgresClient('localhost', dbname, outfile)

            #xform_id_format
            xform_id = f'{prefix}_{xform_title}_{poly.id}'.split('_')[2]

            outline = eval(poly.outline)

            pg = PostgresClient('https://raw-data-api0.hotosm.org/v1', "underpass")
            outline = eval(poly.outline)
            outline_geojson = pg.getFeatures(outline, outfile, xform_title)
            for feature in outline_geojson["features"]:
                feature["properties"]["title"] = ""

            with open(outfile, "w") as jsonfile:
                jsonfile.truncate(0)  # clear the contents of the file
                dump(outline_geojson, jsonfile)
            

            outfile = central_crud.generate_updated_xform(db, poly.id, xlsform, xform)


            """Update tasks table qith qr_Code id"""
            task = tasks_crud.get_task(db, poly.id)
            task.qr_code_id = create_qr['qr_code_id']
            db.commit()
            db.refresh(task)

            # import epdb; epdb.st()
            result = central_crud.create_odk_xform(odk_id, poly.id, outfile, odk_credentials)
            try:
                # Pass odk credentials
                if odk_credentials:
                    url = odk_credentials['odk_central_url']
                    user = odk_credentials['odk_central_user']
                    pw = odk_credentials['odk_central_password']
                    odk_app = OdkAppUser(url, user, pw)
                else:
                    odk_app = central_crud.appuser

                odk_app.updateRole(projectId=one[3], 
                                xmlFormId=xform_id, 
                                actorId=appuser.json()["id"])
            except Exception as e:
                print('Error ', str(e))


def create_qrcode(
    db: Session,
    project_id: int,
    token: str,
    project_name: str,
    odk_credentials: dict = None
):
    #Make QR code for an app_user.
    qrcode = central_crud.create_QRCode(project_id, token, project_name, odk_credentials)
    qrcode = segno.make(qrcode, micro=False)
    image_name = f"{project_name}.png"
    with open(image_name, "rb") as f:
        base64_data = b64encode(f.read()).decode()
    qr_code_text = base64.b64decode(base64_data)
    qrdb = db_models.DbQrCode(
        image=qr_code_text,
        filename = image_name
    )
    db.add(qrdb)
    db.commit()
    codes = table("qr_code", column("id"))
    sql = select(sqlalchemy.func.count(codes.c.id))
    result = db.execute(sql)
    rows = result.fetchone()[0]
    return {"data": qrcode, "id": rows + 1,"qr_code_id":qrdb.id}


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


def create_task_grid(db: Session, project_id: int, delta:int):
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
        value = delta/111139

        nx = int((maxx - minx) / value)
        ny = int((maxy - miny) / value)
        gx, gy = np.linspace(minx, maxx, nx), np.linspace(miny, maxy, ny)
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
                # FIXME: this should clip the features that intersect with the
                # boundary.
                if boundary.contains(poly):
                    feature = geojson.Feature(geometry=poly, properties={"id": str(id)})
                    id += 1
                    grid.append(feature)
        collection = geojson.FeatureCollection(grid)
        # jsonout = open("tmp.geojson", 'w')
        # out = dump(collection, jsonout)
        out = dumps(collection)

        # If project outline cannot be divided into multiple tasks,
        #   whole boundary is made into a single task.
        result = json.loads(out)
        if len(result['features']) == 0:
            geom = loads(data[0][0])
            out = {
                "type": "FeatureCollection",
                "features": [
                    {
                            "type": "Feature",
                            "geometry": geom,
                            "properties": {"id":project_id},
                        }
                        ]
                    }
            out = json.dumps(out)

    except Exception as e:
        logger.error(e)

    return out


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
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ----",
        )


def get_shape_from_json_str(feature: str, error_detail: str):
    try:
        geom = feature["geometry"]
        return shape(geom)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"{error_detail} ----- Error: {e} ---- Json: {feature}",
        )


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
                )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{error_detail} ----- Error: {e}")


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
                ( x for x in db_project.project_info ),
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
