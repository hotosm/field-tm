from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from zipfile import ZipFile
import io
import json
from geojson_pydantic import FeatureCollection
import geojson
from shapely.geometry import shape, mapping
from geoalchemy2.shape import to_shape


from ..db.postgis_utils import timestamp
from ..db import db_models
from ..users import user_crud
from . import project_schemas

# --------------
# ---- CRUD ----
# --------------

QR_CODES_DIR = 'QR_codes/'
TASK_GEOJSON_DIR = 'geojson/'

def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    if user_id:
        db_projects = db.query(db_models.DbProject).filter(db_models.DbProject.author_id == user_id).offset(skip).limit(limit).all()
    else:
        db_projects = db.query(db_models.DbProject).offset(skip).limit(limit).all()
    return convert_to_app_projects(db_projects)

def get_project_by_id(db:Session, project_id: int):
    db_project = db.query(db_models.DbProject).filter(db_models.DbProject.id == project_id).first()
    return db_project
    # return convert_to_app_project(db_project)

def create_project_with_project_info(db: Session, project_metadata: project_schemas.BETAProjectUpload):
    
    user = project_metadata.author
    project_info_1 = project_metadata.project_info
    
    # verify data coming in
    if not user:
        raise HTTPException('No user passed in')
    if not project_info_1:
        raise HTTPException('No project info passed in')
    
    # get db user
    db_user = user_crud.get_user(db, user.id)
    if not db_user:
        raise HTTPException(status_code=400, detail=f"User {user.username} does not exist")
    # TODO: get this from logged in user, return 403 (forbidden) if not authorized

    # create new project
    db_project = db_models.DbProject(
        author = db_user,
        default_locale = project_info_1.locale,
    )
    db.add(db_project)

    # add project info (project id needed to create project info)
    db_project_info = db_models.DbProjectInfo(
        project = db_project,
        locale = project_info_1.locale,
        name = project_info_1.name,
        short_description = project_info_1.short_description,
        description = project_info_1.description,
        instructions = project_info_1.instructions,
        project_id_str = f'{db_project.id}',
        per_task_instructions = project_info_1.per_task_instructions,
    )
    db.add(db_project_info)

    db.commit()
    db.refresh(db_project)

    return convert_to_app_project(db_project)

def update_project_with_upload(
    db: Session, 
    project_id: int, 
    project_name_prefix: str, 
    task_type_prefix: str,
    uploaded_zip: UploadFile,
):
    # TODO: ensure that logged in user is user who created this project, return 403 (forbidden) if not authorized

    # ensure file upload is zip
    if uploaded_zip.content_type not in ["application/zip"]: 
        raise HTTPException(status_code=415, detail=f"File must be a zip. Uploaded file was {uploaded_zip.content_type}")
    
    with ZipFile(io.BytesIO(uploaded_zip.file.read()), 'r') as zip:
        # verify valid zip file
        bad_file = zip.testzip()
        if bad_file:
            raise HTTPException(status_code=400, detail=f'Zip contained a bad file: {bad_file}')

        # verify zip includes top level files & directories
        listed_files = zip.namelist()

        if QR_CODES_DIR not in listed_files:
            raise HTTPException(status_code=400, detail=f'Zip must contain directory named {QR_CODES_DIR}')

        if TASK_GEOJSON_DIR not in listed_files:
            raise HTTPException(status_code=400, detail=f'Zip must contain directory named {TASK_GEOJSON_DIR}')

        outline_filename = f'{project_name_prefix}.geojson'
        if outline_filename not in listed_files:
            raise HTTPException(status_code=400, detail=f'Zip must contain file named "{outline_filename}" that contains a FeatureCollection outlining the project')

        task_outlines_filename = f'{project_name_prefix}_polygons.geojson'
        if task_outlines_filename not in listed_files:
            raise HTTPException(status_code=400, detail=f'Zip must contain file named "{task_outlines_filename}" that contains a FeatureCollection where each Feature outlines a task')
        
        # verify project exists in db
        db_project = get_project_by_id(db, project_id)
        if not db_project:
            raise HTTPException(status_code=428, detail=f'Project with id {project_id} does not exist')
        
        # add prefixes
        db_project.project_name_prefix = project_name_prefix
        db_project.task_type_prefix = task_type_prefix

        # generate outline from file and add to project
        outline_shape = get_outline_from_geojson_file_in_zip(zip, outline_filename, f'Could not generate Shape from {outline_filename}')
        db_project.outline = outline_shape.wkt

        # get all task outlines from file
        project_tasks_feature_collection = get_json_from_zip(zip, task_outlines_filename, f'Could not generate FeatureCollection from {task_outlines_filename}')

        # generate task for each feature
        try:
            task_count = 0
            db_project.total_tasks = len(project_tasks_feature_collection['features'])
            for feature in project_tasks_feature_collection['features']:
                task_name = feature['properties']['task']

                # generate and save qr code in db
                qr_filename = f'{project_name_prefix}_{task_type_prefix}__{task_name}.png'
                db_qr = get_dbqrcode_from_file(
                    zip, 
                    QR_CODES_DIR+qr_filename, 
                    f'QRCode for task {task_name} does not exist. File should be in {qr_filename}',
                )
                db.add(db_qr)

                # save outline
                task_outline_shape = get_shape_from_json_str(
                    feature, 
                    f'Could not create task outline for {task_name} using {feature}',
                )
                
                # extract task geojson
                task_geojson_filename = f'{project_name_prefix}_{task_type_prefix}__{task_name}.geojson'
                task_geojson = get_json_from_zip(
                    zip, 
                    TASK_GEOJSON_DIR+task_geojson_filename,  
                    f'Geojson for task {task_name} does not exist',
                )

                # save task in db
                task = db_models.DbTask(
                    project_id = project_id,
                    project_task_index = feature['properties']['fid'],
                    project_task_name = task_name,
                    qr_code = db_qr,
                    outline = task_outline_shape.wkt, 
                    geometry_geojson = json.dumps(task_geojson),
                    initial_feature_count = len(task_geojson['features']),
                )
                db.add(task)

                # for error messages
                task_count = task_count+1
            db_project.last_updated = timestamp()

            db.commit()
            db.refresh(db_project) # should now include outline, geometry and tasks
            
            return db_project
        
        # Exception was raised by app logic and has an error message, just pass it along
        except HTTPException as http_e:
            raise http_e

        # Unexpected exception
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'{task_count} tasks were created before the following error was thrown: {e}, on feature: {feature}') 

# ---------------------------
# ---- SUPPORT FUNCTIONS ----
# ---------------------------

def get_json_from_zip(zip, filename: str, error_detail: str):
    try:
        with zip.open(filename) as file:
            data = file.read()
            return json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{error_detail} ----- Error: {e}')

def get_outline_from_geojson_file_in_zip(zip, filename: str, error_detail: str, feature_index: int = 0):
    try:
        # json_dump = get_json_from_zip(zip, filename, error_detail)
        with zip.open(filename) as file:
            data = file.read()
            json_dump = json.loads(data)
            feature_collection = geojson.FeatureCollection(json_dump)
            feature = feature_collection['features'][feature_index]
            geom = feature['geometry']
            shape_from_geom = shape(geom)
            return shape_from_geom
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{error_detail} ----- Error: {e} ---- FeatureCollection: {feature_collection}')

def get_shape_from_json_str(feature: str, error_detail: str):
    try:
        # json_dump = json.loads(feature)
        geom = feature['geometry']
        return shape(geom)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{error_detail} ----- Error: {e} ---- Json: {feature}')   

def get_dbqrcode_from_file(zip, qr_filename: str, error_detail: str):
    try:
        with zip.open(qr_filename) as qr_file:
            binary_qrcode = qr_file.read()
            if binary_qrcode:
                return db_models.DbQrCode(
                    filename = qr_filename,
                    image = binary_qrcode,
                )
            else:
                raise HTTPException(status_code=400, detail=f'{qr_filename} is an empty file')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{error_detail} ----- Error: {e}')

# --------------------
# ---- CONVERTERS ----
# --------------------

# TODO: write tests for these

def convert_to_app_project(db_project: db_models.DbProject):
    if db_project:
        app_project: project_schemas.Project = db_project
        geom_outline = to_shape(db_project.outline)
        app_project.outline_json = json.dumps(mapping(geom_outline))
        return app_project
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