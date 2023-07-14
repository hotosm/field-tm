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

import json
import os
import uuid
from typing import List, Optional
import tempfile
import inspect

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    Response
)
from fastapi.responses import FileResponse
from osm_fieldwork.xlsforms import xlsforms_path
from fastapi.logger import logger as logger
from osm_fieldwork.make_data_extract import getChoices
from sqlalchemy.orm import Session

import json

from ..central import central_crud
from ..db import database
from . import project_crud, project_schemas
from ..tasks import tasks_crud

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[project_schemas.ProjectOut])
async def read_projects(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    projects = project_crud.get_projects(db, user_id, skip, limit)
    return projects


@router.post("/near_me", response_model=project_schemas.ProjectSummary)
def get_task(lat: float, long: float, user_id: int = None):
    return "Coming..."


@router.get("/summaries", response_model=List[project_schemas.ProjectSummary])
async def read_project_summaries(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    projects = project_crud.get_project_summaries(db, user_id, skip, limit)
    return projects


@router.get("/{project_id}", response_model=project_schemas.ProjectOut)
async def read_project(project_id: int, db: Session = Depends(database.get_db)):
    project = project_crud.get_project_by_id(db, project_id)
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/delete/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    """Delete a project from ODK Central and the local database."""
    # FIXME: should check for error

    project = project_crud.get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Odk crendentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url = project.odk_central_url,
        odk_central_user = project.odk_central_user,
        odk_central_password = project.odk_central_password,
        )

    central_crud.delete_odk_project(project.odkid, odk_credentials)

    deleted_project = project_crud.delete_project_by_id(db, project_id)
    if deleted_project:
        return deleted_project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/create_project", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.BETAProjectUpload,
    db: Session = Depends(database.get_db),
):
    """Create a project in ODK Central and the local database."""
    logger.debug(f"Creating project {project_info.project_info.name}")

    if project_info.odk_central.odk_central_url.endswith("/"):
        project_info.odk_central.odk_central_url = project_info.odk_central.odk_central_url[:-1]

    try:
        odkproject = central_crud.create_odk_project(
            project_info.project_info.name, project_info.odk_central
        )
        logger.debug(f"ODKCentral return: {odkproject}")
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail="Connection failed to central odk. "
        ) from e

    # TODO check token against user or use token instead of passing user
    # project_info.project_name_prefix = project_info.project_info.name
    project = project_crud.create_project_with_project_info(
        db, project_info, odkproject["id"]
    )

    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")

@router.post("/update_odk_credentials")
async def update_odk_credentials(
    background_task: BackgroundTasks,
    odk_central_cred: project_schemas.ODKCentral,
    project_id: int,
    db: Session = Depends(database.get_db)
):
    """Update odk credential of a project"""
    if odk_central_cred.odk_central_url.endswith("/"):
        odk_central_cred.odk_central_url = odk_central_cred.odk_central_url[:-1]
    
    project_instance = project_crud.get_project(db, project_id)
    if not project_instance:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        odkproject = central_crud.create_odk_project(
            project_instance.project_info[0].name, odk_central_cred
        )
        logger.debug(f"ODKCentral return after update: {odkproject}")
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail="Connection failed to central odk. "
        ) from e
    
    await project_crud.update_odk_credentials(project_instance, odk_central_cred, odkproject["id"], db)
    
    extract_polygon = True if project_instance.data_extract_type == 'polygon' else False
    project_id = project_instance.id
    contents = project_instance.form_xls if project_instance.form_xls else None
    
    if contents:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        temp_file.write(contents)
        temp_file.filename = temp_file.name
    else:
        temp_file = None
        
    generate_response = await generate_files(background_tasks=background_task, 
                            project_id=project_id, 
                            extract_polygon=extract_polygon, 
                            upload=temp_file ,db=db, data_extracts=None)
    if temp_file:
        temp_file.close()
    
    return generate_response
    

@router.put("/{id}", response_model=project_schemas.ProjectOut)
async def update_project(
    id: int,
    project_info: project_schemas.BETAProjectUpload,
    db: Session = Depends(database.get_db),
):
    """Update an existing project by ID.

    Parameters:
    - id: ID of the project to update
    - author: Author username and id
    - project_info: Updated project information

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    project = project_crud.update_project_info(db, project_info, id)
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/{id}", response_model=project_schemas.ProjectOut)
async def project_partial_update(
    id: int,
    project_info: project_schemas.ProjectUpdate,
    db: Session = Depends(database.get_db),
):
    """Partial Update an existing project by ID.

    Parameters:
    - id
    - name
    - short_description
    - description

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    # Update project informations
    project = project_crud.partial_update_project_info(db, project_info, id)

    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/beta/{project_id}/upload")
async def upload_project_boundary_with_zip(
    project_id: int,
    project_name_prefix: str,
    task_type_prefix: str,
    upload: UploadFile,
    db: Session = Depends(database.get_db),
):
    r"""Upload a ZIP with task geojson polygons and QR codes for an existing project.

    {PROJECT_NAME}/\n
    ├─ {PROJECT_NAME}.geojson\n
    ├─ {PROJECT_NAME}_polygons.geojson\n
    ├─ geojson/\n
    │  ├─ {PROJECT_NAME}_TASK_TYPE__{TASK_NUM}.geojson\n
    ├─ QR_codes/\n
    │  ├─ {PROJECT_NAME}_{TASK_TYPE}__{TASK_NUM}.png\n
    """
    # TODO: consider replacing with this: https://stackoverflow.com/questions/73442335/how-to-upload-a-large-file-%e2%89%a53gb-to-fastapi-backend/73443824#73443824
    project = project_crud.update_project_with_zip(
        db, project_id, project_name_prefix, task_type_prefix, upload
    )
    if project:
        return project

    return {"Message": "Uploading project ZIP failed"}


@router.post("/upload_xlsform")
async def upload_custom_xls(
    upload: UploadFile = File(...),
    category: str = Form(...),
    db: Session = Depends(database.get_db),
):
    """Upload a custom XLSForm to the database.
    Parameters:
    - upload: the XLSForm file
    - category: the category of the XLSForm.
    """
    content = await upload.read()  # read file content
    name = upload.filename.split(".")[0]  # get name of file without extension
    project_crud.upload_xlsform(db, content, name, category)

    # FIXME: fix return value
    return {"xform_title": f"{category}"}


@router.post("/{project_id}/upload_multi_polygon")
async def upload_multi_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """This API allows for the uploading of a multi-polygon project boundary
        in JSON format for a specified project ID. Each polygon in the uploaded geojson are made a single task.

    Required Parameters:
    project_id: ID of the project to which the boundary is being uploaded.
    upload: a file upload containing the multi-polygon boundary in geojson format.

    Returns:
    A success message indicating that the boundary was successfully uploaded.
    If the project ID does not exist in the database, an HTTP 428 error is raised.
    """
    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    """Create tasks for each polygon """
    result = project_crud.update_multi_polygon_project_boundary(
        db, project_id, boundary
    )

    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    return {"message": "Project Boundary Uploaded", "project_id": f"{project_id}"}


@router.post("/task_split")
async def task_split(
    upload: UploadFile = File(...),
    db: Session = Depends(database.get_db)
    ):

    # read entire file
    content = await upload.read()

    result = await project_crud.split_into_tasks(db, content)

    return result


@router.post("/{project_id}/upload")
async def upload_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    dimension: int = Form(500),
    db: Session = Depends(database.get_db),
):
    """
    Uploads the project boundary. The boundary is uploaded as a geojson file.

    Params:
    - project_id (int): The ID of the project to update.
    - upload (UploadFile): The boundary file to upload.
    - dimension (int): The new dimension of the project.
    - db (Session): The database session to use.

    Returns:
    - Dict: A dictionary with a message, the project ID, and the number of tasks in the project.
    """

    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    # update project boundary and dimension
    result = project_crud.update_project_boundary(db, project_id, boundary, dimension)
    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    # Get the number of tasks in a project
    task_count = await tasks_crud.get_task_count_in_project(db, project_id)

    return {
        "message": "Project Boundary Uploaded", 
        "project_id": project_id,
        "task_count": task_count
    }


@router.post("/edit_project_boundary/{project_id}/")
async def edit_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    dimension: int = Form(500),
    db: Session = Depends(database.get_db)
    ):

    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    result = project_crud.update_project_boundary(db, project_id, boundary, dimension)
    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    # Get the number of tasks in a project
    task_count = await tasks_crud.get_task_count_in_project(db, project_id)

    return {
        "message": "Project Boundary Uploaded", 
        "project_id": project_id,
        "task_count": task_count
    }


@router.post("/{project_id}/download")
async def download_project_boundary(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the boundary polygon for this project."""
    out = project_crud.download_geometry(db, project_id, False)
    
    buffer = json.dumps(out['filespec']).encode()

    headers = {
        "Content-Disposition": "attachment; filename=out.geojson",
        "Content-Type": "application/media",
    }

    return Response(buffer, headers=headers)


@router.get("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Download the task boundary polygons for this project."""
    out = project_crud.download_geometry(db, project_id, True)
    
    buffer = json.dumps(out['filespec']).encode()
    
    headers = {
        "Content-Disposition": "attachment; filename=task_outline.geojson",
        "Content-Type": "application/media",
    }

    return Response(buffer, headers=headers)


@router.post("/{project_id}/generate")
async def generate_files(
    background_tasks: BackgroundTasks,
    project_id: int,
    extract_polygon: bool = Form(False),
    upload: Optional[UploadFile] = File(None),
    data_extracts: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
):
    """Generate required media files tasks in the project based on the provided params.

    Accepts a project ID, category, custom form flag, and an uploaded file as inputs.
    The generated files are associated with the project ID and stored in the database.
    This api generates qr_code, forms. This api also creates an app user for each task and provides the required roles.
    Some of the other functionality of this api includes converting a xls file provided by the user to the xform,
    generates osm data extracts and uploads it to the form.


    Parameters:

    project_id (int): The ID of the project for which files are being generated. This is a required field.
    polygon (bool): A boolean flag indicating whether the polygon is extracted or not.

    upload (UploadFile): An uploaded file that is used as input for generating the files.
        This is not a required field. A file should be provided if user wants to upload a custom xls form.

    Returns:
    Message (str): A success message containing the project ID.

    """
    contents = None
    xform_title = None

    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    project.data_extract_type = 'polygon' if extract_polygon else 'centroid'
    db.commit()

    if upload:
        # Validating for .XLS File.
        file_name = os.path.splitext(upload.filename)
        file_ext = file_name[1]
        allowed_extensions = [".xls", '.xlsx', '.xml']
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Provide a valid .xls file")
        xform_title = file_name[0]
        
        if inspect.iscoroutinefunction(upload.read):
            contents = await upload.read()
        else:
            contents = upload.read()

        project.form_xls = contents
        db.commit()

    if data_extracts:
        # Validating for .geojson File.
        data_extracts_file_name = os.path.splitext(data_extracts.filename)
        extracts_file_ext = data_extracts_file_name[1]
        if extracts_file_ext != '.geojson':
            raise HTTPException(status_code=400, detail="Provide a valid geojson file")
        try:
            extracts_contents = await data_extracts.read()
            json.loads(extracts_contents)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Provide a valid geojson file")


    # generate a unique task ID using uuid
    background_task_id = uuid.uuid4()

    # insert task and task ID into database
    await project_crud.insert_background_task_into_database(
        db, task_id=background_task_id
    )

    background_tasks.add_task(
        project_crud.generate_appuser_files,
        db,
        project_id,
        extract_polygon,
        contents,
        extracts_contents if data_extracts else None,
        xform_title,
        file_ext[1:] if upload else 'xls',
        background_task_id,
    )

    return {"Message": f"{project_id}", "task_id": f"{background_task_id}"}


@router.post("/update-form/{project_id}")
async def update_project_form(
    project_id: int,
    form: Optional[UploadFile],
    db: Session = Depends(database.get_db),
    ):

    file_name = os.path.splitext(form.filename)
    file_ext = file_name[1]
    allowed_extensions = [".xls"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .xls file")
    contents = await form.read()

    form_updated = await project_crud.update_project_form(
        db, 
        project_id,  
        contents,    # Form Contents
        file_ext[1:] # File type
        )

    return form_updated


@router.get("/{project_id}/features", response_model=List[project_schemas.Feature])
def get_project_features(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Get api for fetching all the features of a project.

    This endpoint allows you to get all the features of a project.

    ## Request Body
    - `project_id` (int): the project's id. Required.

    ## Response
    - Returns a JSON object containing a list of features.

    """
    features = project_crud.get_project_features(db, project_id, task_id)
    return features


@router.get("/generate-log/")
async def generate_log(
    project_id: int, uuid: uuid.UUID, db: Session = Depends(database.get_db)
):
    r"""Get the contents of a log file in a log format.

    ### Response
    - **200 OK**: Returns the contents of the log file in a log format. Each line is separated by a newline character "\n".

    - **500 Internal Server Error**: Returns an error message if the log file cannot be generated.

    ### Return format
    Task Status and Logs are returned in a JSON format.
    """
    try:
        # Get the backgrund task status
        task_status, task_message = await project_crud.get_background_task_status(uuid, db)
        extract_completion_count = await project_crud.get_extract_completion_count(
            project_id, db
        )

        with open(f"/tmp/{project_id}_generate.log", "r") as f:
            lines = f.readlines()
            last_100_lines = lines[-50:]
            logs = "".join(last_100_lines)
            return {
                "status": task_status.name,
                "message":task_message,
                "progress": extract_completion_count,
                "logs": logs,
            }
    except Exception as e:
        logger.error(e)
        return "Error in generating log file"


@router.get("/categories/")
async def get_categories():
    """Get api for fetching all the categories.

    This endpoint fetches all the categories from osm_fieldwork.

    ## Response
    - Returns a JSON object containing a list of categories and their respoective forms.

    """
    categories = (
        getChoices()
    )  # categories are fetched from osm_fieldwork.make_data_extracts.getChoices()
    return categories


@router.post("/preview_tasks/")
async def preview_tasks(upload: UploadFile = File(...), dimension: int = Form(500)):
    """Preview tasks for a project.

    This endpoint allows you to preview tasks for a project.

    ## Request Body
    - `project_id` (int): the project's id. Required.

    ## Response
    - Returns a JSON object containing a list of tasks.

    """
    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await upload.read()
    boundary = json.loads(content)

    result = await project_crud.preview_tasks(boundary, dimension)
    return result


@router.post("/add_features/")
async def add_features(
    background_tasks: BackgroundTasks,
    project_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """Add features to a project.

    This endpoint allows you to add features to a project.

    ## Request Body
    - `project_id` (int): the project's id. Required.
    - `upload` (file): Geojson files with the features. Required.

    """
    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await upload.read()
    features = json.loads(content)

    # generate a unique task ID using uuid
    background_task_id = uuid.uuid4()

    # insert task and task ID into database
    await project_crud.insert_background_task_into_database(
        db, task_id=background_task_id
    )

    background_tasks.add_task(
        project_crud.add_features_into_database,
        db,
        project_id,
        features,
        background_task_id,
    )
    return True


@router.get("/download_form/{project_id}/")
async def download_form(project_id: int, 
                        db: Session = Depends(database.get_db)
                        ):
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    headers = {
        "Content-Disposition": "attachment; filename=submission_data.xls",
        "Content-Type": "application/json",
    }
    if not project.form_xls:
        project_category = project.xform_title
        xlsform_path = f"{xlsforms_path}/{project_category}.xls"
        if os.path.exists(xlsform_path):
            return FileResponse(xlsform_path, filename="form.xls")
        else:
            raise HTTPException(status_code=404, detail="Form not found")
    return Response(content=project.form_xls, headers=headers)


@router.post("/update_category")
async def update_project_category(
    # background_tasks: BackgroundTasks,
    project_id: int,
    category: str,
    upload: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    ):

    contents = None

    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=400, detail=f"Project with id {project_id} does not exist"
        )

    current_category = project.xform_title
    if current_category == category:
        raise HTTPException(status_code=400, detail="Current category is same as new category")


    if upload:
        # Validating for .XLS File.
        file_name = os.path.splitext(upload.filename)
        file_ext = file_name[1]
        allowed_extensions = [".xls", '.xlsx', '.xml']
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Provide a valid .xls file")
        contents = await upload.read()

        project.form_xls = contents
        db.commit()
    else:
        form_path = f"{xlsforms_path}/{category}.xls"
        contents = open(form_path, 'rb')

    project.category = category
    db.commit()

    # Update odk forms
    form_updated = await project_crud.update_project_form(
        db, 
        project_id,  
        contents,    # Form Contents
        file_ext[1:] if upload else 'xls',
        )


    return True


@router.get("/download_template/")
async def download_template(category: str, db: Session = Depends(database.get_db)):
    xlsform_path = f"{xlsforms_path}/{category}.xls"
    if os.path.exists(xlsform_path):
        return FileResponse(xlsform_path, filename="form.xls")
    else:
        raise HTTPException(status_code=404, detail="Form not found")

        
