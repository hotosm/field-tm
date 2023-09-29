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

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from loguru import logger as log
from osm_fieldwork.make_data_extract import getChoices
from osm_fieldwork.xlsforms import xlsforms_path
from sqlalchemy.orm import Session

from ..central import central_crud
from ..db import database, db_models
from ..models.enums import TILES_SOURCE
from ..tasks import tasks_crud
from . import project_crud, project_schemas, utils

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
    """Get a list of projects.

    Args:
        user_id (int, optional): The ID of the user to filter projects by. Defaults to None.
        skip (int, optional): The number of projects to skip. Defaults to 0.
        limit (int, optional): The maximum number of projects to return. Defaults to 100.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        List[project_schemas.ProjectOut]: A list of projects.
    """
    projects = project_crud.get_projects(db, user_id, skip, limit)
    return projects


@router.get("/project_details/{project_id}/")
async def get_projet_details(project_id: int, db: Session = Depends(database.get_db)):
    """Returns the project details.

    Parameters:
        project_id: int

    Returns:
        Response: Project details.
    """
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, details={"Project not found"})

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project.odk_central_url,
        odk_central_user=project.odk_central_user,
        odk_central_password=project.odk_central_password,
    )

    odk_details = await central_crud.get_project_full_details(
        project.odkid, odk_credentials
    )

    # Features count
    query = f"select count(*) from features where project_id={project_id} and task_id is not null"
    result = db.execute(query)
    features = result.fetchone()[0]

    return {
        "id": project_id,
        "name": odk_details["name"],
        "createdAt": odk_details["createdAt"],
        "tasks": odk_details["forms"],
        "lastSubmission": odk_details["lastSubmission"],
        "total_features": features,
    }


@router.post("/near_me", response_model=project_schemas.ProjectSummary)
def get_task(lat: float, long: float, user_id: int = None):
    """Get a task near the specified location.

    Args:
        lat (float): The latitude of the location.
        long (float): The longitude of the location.
        user_id (int, optional): The ID of the user. Defaults to None.

    Returns:
        project_schemas.ProjectSummary: A summary of the project.
    """
    return "Coming..."


@router.get("/summaries", response_model=List[project_schemas.ProjectSummary])
async def read_project_summaries(
    user_id: int = None,
    hashtags: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    """Get a list of project summaries.

    Args:
        user_id (int, optional): The ID of the user to filter projects by. Defaults to None.
        hashtags (str, optional): A comma-separated list of hashtags to filter projects by. Defaults to None.
        skip (int, optional): The number of projects to skip. Defaults to 0.
        limit (int, optional): The maximum number of projects to return. Defaults to 100.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        List[project_schemas.ProjectSummary]: A list of project summaries.
    """
    if hashtags:
        hashtags = hashtags.split(",")  # create list of hashtags
        hashtags = list(
            filter(lambda hashtag: hashtag.startswith("#"), hashtags)
        )  # filter hashtags that do start with #

    projects = project_crud.get_project_summaries(db, user_id, skip, limit, hashtags)
    return projects


@router.get("/{project_id}", response_model=project_schemas.ProjectOut)
async def read_project(project_id: int, db: Session = Depends(database.get_db)):
    """Get a project by its ID.

    Args:
        project_id (int): The ID of the project.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        project_schemas.ProjectOut: The project.

    Raises:
        HTTPException: If the project is not found.

    """
    project = project_crud.get_project_by_id(db, project_id)
    if project:
        return project
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/delete/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    """Delete a project by its ID.

    Args:
        project_id (int): The ID of the project.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The deleted project.

    Raises:
        HTTPException: If the project is not found.
    """
    # FIXME: should check for error

    project = project_crud.get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Odk crendentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project.odk_central_url,
        odk_central_user=project.odk_central_user,
        odk_central_password=project.odk_central_password,
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
    log.debug(f"Creating project {project_info.project_info.name}")

    if project_info.odk_central.odk_central_url.endswith("/"):
        project_info.odk_central.odk_central_url = (
            project_info.odk_central.odk_central_url[:-1]
        )

    try:
        odkproject = central_crud.create_odk_project(
            project_info.project_info.name, project_info.odk_central
        )
    except Exception as e:
        log.error(e)
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
    db: Session = Depends(database.get_db),
):
    """Update odk credential of a project."""
    if odk_central_cred.odk_central_url.endswith("/"):
        odk_central_cred.odk_central_url = odk_central_cred.odk_central_url[:-1]

    project_instance = project_crud.get_project(db, project_id)

    if not project_instance:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        odkproject = central_crud.create_odk_project(
            project_instance.project_info[0].name, odk_central_cred
        )
        log.debug(f"ODKCentral return after update: {odkproject}")
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=400, detail="Connection failed to central odk. "
        ) from e

    await project_crud.update_odk_credentials(
        project_instance, odk_central_cred, odkproject["id"], db
    )

    extract_polygon = True if project_instance.data_extract_type == "polygon" else False
    project_id = project_instance.id
    contents = project_instance.form_xls if project_instance.form_xls else None

    generate_response = await utils.generate_files(
        background_tasks=background_task,
        project_id=project_id,
        extract_polygon=extract_polygon,
        upload=contents if contents else None,
        db=db,
    )

    return generate_response


@router.put("/{id}", response_model=project_schemas.ProjectOut)
async def update_project(
    id: int,
    project_info: project_schemas.BETAProjectUpload,
    db: Session = Depends(database.get_db),
):
    """Update an existing project by its ID.

    Args:
        id (int): The ID of the project to update.
        project_info (project_schemas.BETAProjectUpload): The updated information about the project.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The updated project.

    Raises:
        HTTPException: If the project is not found.

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
    """Partially update an existing project by its ID.

    Args:
        id (int): The ID of the project to update.
        project_info (project_schemas.ProjectUpdate): The updated information about the project.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The updated project.

    Raises:
        HTTPException: If the project is not found.

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
    """Upload a ZIP file with task geojson polygons and QR codes for an existing project.

    Args:
        project_id (int): The ID of the project to upload to.
        project_name_prefix (str): The prefix for the project name.
        task_type_prefix (str): The prefix for the task type.
        upload (UploadFile): The ZIP file to upload.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The updated project or a message indicating that uploading failed.

    Raises:
        HTTPException: If there is a connection error to ODK Central.

    """
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

    Args:
        upload (UploadFile): The XLSForm file to upload.
        category (str): The category of the XLSForm.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        A dictionary with the title of the XLSForm.
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
    """Upload a multi-polygon project boundary in JSON format for a specified project ID.

    Args:
        project_id (int): The ID of the project to which the boundary is being uploaded.
        upload (UploadFile): A file upload containing the multi-polygon boundary in geojson format.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        A dictionary with a message and the project ID.

    Raises:
        HTTPException: If the project ID does not exist in the database.

    """
    log.debug(
        "Uploading project boundary multipolygon for " f"project ID: {project_id}"
    )
    # read entire file
    await upload.seek(0)
    content = await upload.read()
    boundary = json.loads(content)

    log.debug("Creating tasks for each polygon in project")
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
    no_of_buildings: int = Form(50),
    has_data_extracts: bool = Form(False),
    db: Session = Depends(database.get_db),
):
    """Split a task into subtasks.

    Args:
        upload (UploadFile): The file to split.
        no_of_buildings (int, optional): The number of buildings per subtask. Defaults to 50.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The result of splitting the task into subtasks.

    """
    # read entire file
    await upload.seek(0)
    content = await upload.read()

    result = await project_crud.split_into_tasks(
        db, content, no_of_buildings, has_data_extracts
    )

    return result


@router.post("/{project_id}/upload")
async def upload_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    dimension: int = Form(500),
    db: Session = Depends(database.get_db),
):
    """Uploads the project boundary. The boundary is uploaded as a geojson file.

    Args:
        project_id (int): The ID of the project to update.
        upload (UploadFile): The boundary file to upload.
        dimension (int, optional): The new dimension of the project. Defaults to 500.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        A dictionary with a message, the project ID, and the number of tasks in the project.

    Raises:
        HTTPException: If the provided file is not valid or if the project ID does not exist in the database.

    """
    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    await upload.seek(0)
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
        "task_count": task_count,
    }


@router.post("/edit_project_boundary/{project_id}/")
async def edit_project_boundary(
    project_id: int,
    upload: UploadFile = File(...),
    dimension: int = Form(500),
    db: Session = Depends(database.get_db),
):
    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    await upload.seek(0)
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
        "task_count": task_count,
    }


@router.post("/validate_form")
async def validate_form(
    form: UploadFile,
):
    """Tests the validity of the xls form uploaded.

    Parameters:
        - form: The xls form to validate
    """
    file_name = os.path.splitext(form.filename)
    file_ext = file_name[1]

    allowed_extensions = [".xls", ".xlsx"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .xls file")

    await form.seek(0)
    contents = await form.read()
    return await central_crud.test_form_validity(contents, file_ext[1:])


@router.post("/{project_id}/generate")
async def generate_files(
    background_tasks: BackgroundTasks,
    project_id: int,
    extract_polygon: bool = Form(False),
    upload: Optional[UploadFile] = File(None),
    config_file: Optional[UploadFile] = File(None),
    data_extracts: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
):
    """Generate required media files for tasks in the project based on the provided parameters.

    Args:
        background_tasks (BackgroundTasks): The background tasks object.
        project_id (int): The ID of the project for which files are being generated.
        extract_polygon (bool, optional): A boolean flag indicating whether the polygon is extracted or not. Defaults to False.
        upload (Optional[UploadFile], optional): An uploaded file that is used as input for generating the files. A file should be provided if user wants to upload a custom xls form. Defaults to None.
        data_extracts (Optional[UploadFile], optional): An uploaded file containing data extracts. Defaults to None.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        A dictionary with a message containing the project ID and a task ID.

    Raises:
        HTTPException: If the project ID does not exist in the database or if an invalid file is provided.

    """
    log.debug(f"Generating media files tasks for project: {project_id}")
    contents = None
    xform_title = None

    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    project.data_extract_type = "polygon" if extract_polygon else "centroid"
    db.commit()

    if upload:
        log.debug("Validating uploaded XLS file")
        # Validating for .XLS File.
        file_name = os.path.splitext(upload.filename)
        file_ext = file_name[1]
        allowed_extensions = [".xls", ".xlsx", ".xml"]
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Provide a valid .xls file")
        xform_title = file_name[0]
        await upload.seek(0)
        contents = await upload.read()

        project.form_xls = contents

        if config_file:
            config_file_name = os.path.splitext(config_file.filename)
            config_file_ext = config_file_name[1]
            if not config_file_ext == ".yaml":
                raise HTTPException(
                    status_code=400, detail="Provide a valid .yaml config file"
                )
            await config_file.seek(0)
            config_file_contents = await config_file.read()
            project.form_config_file = config_file_contents

        db.commit()

    if data_extracts:
        log.debug("Validating uploaded geojson file")
        # Validating for .geojson File.
        data_extracts_file_name = os.path.splitext(data_extracts.filename)
        extracts_file_ext = data_extracts_file_name[1]
        if extracts_file_ext != ".geojson":
            raise HTTPException(status_code=400, detail="Provide a valid geojson file")
        try:
            extracts_contents = await data_extracts.read()
            json.loads(extracts_contents)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Provide a valid geojson file")

    # generate a unique task ID using uuid
    background_task_id = uuid.uuid4()

    # insert task and task ID into database
    log.debug(
        f"Creating background task ID {background_task_id} "
        f"for project ID: {project_id}"
    )
    await project_crud.insert_background_task_into_database(
        db, task_id=background_task_id, project_id=project_id
    )

    log.debug(f"Submitting {background_task_id} to background tasks stack")
    background_tasks.add_task(
        project_crud.generate_appuser_files,
        db,
        project_id,
        extract_polygon,
        contents,
        extracts_contents if data_extracts else None,
        xform_title,
        file_ext[1:] if upload else "xls",
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
        db, project_id, contents, file_ext[1:]  # Form Contents  # File type
    )

    return form_updated


@router.get("/{project_id}/features", response_model=List[project_schemas.Feature])
def get_project_features(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Get all the features of a project.

    Args:
        project_id (int): The project's ID.
        task_id (int, optional): The task ID. Defaults to None.
        db (Session, optional): The database session. Defaults to Depends(database.get_db).

    Returns:
        List[project_schemas.Feature]: A list of project features.
    """
    features = project_crud.get_project_features(db, project_id, task_id)
    return features


@router.get("/generate-log/")
async def generate_log(
    project_id: int, uuid: uuid.UUID, db: Session = Depends(database.get_db)
):
    """Get the contents of a log file in a log format.

    Args:
        project_id (int): The project's ID.
        uuid (uuid.UUID): The UUID of the background task.
        db (Session, optional): The database session. Defaults to Depends(database.get_db).

    Returns:
        dict: Task status, message, progress, and logs.
    """
    r"""Get the contents of a log file in a log format.

    ### Response
    - **200 OK**: Returns the contents of the log file in a log format. Each line is separated by a newline character "\n".

    - **500 Internal Server Error**: Returns an error message if the log file cannot be generated.

    ### Return format
    Task Status and Logs are returned in a JSON format.
    """
    try:
        # Get the backgrund task status
        task_status, task_message = await project_crud.get_background_task_status(
            uuid, db
        )
        extract_completion_count = await project_crud.get_extract_completion_count(
            project_id, db
        )

        with open("/opt/logs/create_project.json", "r") as log_file:
            logs = [json.loads(line) for line in log_file]

            filtered_logs = [
                log.get("record", {}).get("message", None)
                for log in logs
                if log.get("record", {}).get("extra", {}).get("project_id")
                == project_id
            ]
            last_50_logs = filtered_logs[-50:]

            logs = "\n".join(last_50_logs)
            return {
                "status": task_status.name,
                "message": task_message,
                "progress": extract_completion_count,
                "logs": logs,
            }
    except Exception as e:
        log.error(e)
        return "Error in generating log file"


@router.get("/categories/")
async def get_categories():
    """Get all the categories from osm_fieldwork.

    Returns:
        A list of categories and their respective forms.

    """
    categories = (
        getChoices()
    )  # categories are fetched from osm_fieldwork.make_data_extracts.getChoices()
    return categories


@router.post("/preview_tasks/")
async def preview_tasks(upload: UploadFile = File(...), dimension: int = Form(500)):
    """Preview tasks for a project.

    Args:
        upload (UploadFile): The boundary file to preview tasks for.
        dimension (int, optional): The dimension of the tasks. Defaults to 500.

    Returns:
        The result of previewing tasks for a project.

    Raises:
        HTTPException: If an invalid file is provided.

    """
    # Validating for .geojson File.
    file_name = os.path.splitext(upload.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    await upload.seek(0)
    content = await upload.read()
    boundary = json.loads(content)

    result = await project_crud.preview_tasks(boundary, dimension)
    return result


@router.post("/add_features/")
async def add_features(
    background_tasks: BackgroundTasks,
    upload: UploadFile = File(...),
    feature_type: str = Query(
        ..., description="Select feature type ", enum=["buildings", "lines"]
    ),
    db: Session = Depends(database.get_db),
):
    """Add features to a project.

    This endpoint allows you to add features to a project.

    Request Body
    - 'project_id' (int): the project's id. Required.
    - 'upload' (file): Geojson files with the features. Required.

    Returns:
        bool: True if features were added successfully.
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
        features,
        background_task_id,
        feature_type,
    )
    return True


@router.get("/download_form/{project_id}/")
async def download_form(project_id: int, db: Session = Depends(database.get_db)):
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    headers = {
        "Content-Disposition": "attachment; filename=submission_data.xls",
        "Content-Type": "application/media",
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
    project_id: int = Form(...),
    category: str = Form(...),
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
        if not upload:
            raise HTTPException(
                status_code=400, detail="Current category is same as new category"
            )

    if upload:
        # Validating for .XLS File.
        file_name = os.path.splitext(upload.filename)
        file_ext = file_name[1]
        allowed_extensions = [".xls", ".xlsx", ".xml"]
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Provide a valid .xls file")

        project.form_xls = contents
        db.commit()

    project.xform_title = category
    db.commit()

    # Update odk forms
    await project_crud.update_project_form(
        db, project_id, file_ext[1:] if upload else "xls", upload  # Form
    )

    return True


@router.get("/download_template/")
async def download_template(category: str, db: Session = Depends(database.get_db)):
    """Download a template based on the provided category.

    Args:
        category (str): The category of the template.
        db (Session): The database session.

    Returns:
        Response: The downloaded template file.
    """
    xlsform_path = f"{xlsforms_path}/{category}.xls"
    if os.path.exists(xlsform_path):
        return FileResponse(xlsform_path, filename="form.xls")
    else:
        raise HTTPException(status_code=404, detail="Form not found")


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Downloads the boundary of a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    out = project_crud.get_project_geometry(db, project_id)
    headers = {
        "Content-Disposition": "attachment; filename=project_outline.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=out, headers=headers)


@router.get("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Downloads the boundary of the tasks for a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    out = project_crud.get_task_geometry(db, project_id)

    headers = {
        "Content-Disposition": "attachment; filename=project_outline.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=out, headers=headers)


@router.get("/features/download/")
async def download_features(project_id: int, db: Session = Depends(database.get_db)):
    """Downloads the features of a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    out = await project_crud.get_project_features_geojson(db, project_id)

    headers = {
        "Content-Disposition": "attachment; filename=project_features.geojson",
        "Content-Type": "application/media",
    }

    return Response(content=json.dumps(out), headers=headers)


@router.get("/tiles/{project_id}")
async def generate_project_tiles(
    background_tasks: BackgroundTasks,
    project_id: int,
    source: str = Query(
        ..., description="Select a source for tiles", enum=TILES_SOURCE
    ),
    db: Session = Depends(database.get_db),
):
    """Returns the tiles for a project.

    Args:
        project_id (int): The id of the project.
        source (str): The selected source.

    Returns:
        Response: The File response object containing the tiles.
    """
    # generate a unique task ID using uuid
    background_task_id = uuid.uuid4()

    # insert task and task ID into database
    await project_crud.insert_background_task_into_database(
        db, task_id=background_task_id, project_id=project_id
    )

    background_tasks.add_task(
        project_crud.get_project_tiles, db, project_id, source, background_task_id
    )

    return {"Message": "Tile generation started"}


@router.get("/tiles_list/{project_id}/")
async def tiles_list(project_id: int, db: Session = Depends(database.get_db)):
    """Returns the list of tiles for a project.

    Parameters:
        project_id: int

    Returns:
        Response: List of generated tiles for a project.
    """
    return await project_crud.get_mbtiles_list(db, project_id)


@router.get("/download_tiles/")
async def download_tiles(tile_id: int, db: Session = Depends(database.get_db)):
    tiles_path = (
        db.query(db_models.DbTilesPath)
        .filter(db_models.DbTilesPath.id == str(tile_id))
        .first()
    )
    return FileResponse(
        tiles_path.path,
        headers={"Content-Disposition": "attachment; filename=tiles.mbtiles"},
    )


@router.get("/boundary_in_osm/{project_id}/")
async def download_task_boundary_osm(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Downloads the boundary of a task as a OSM file.

    Args:
        project_id (int): The id of the project.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    out = project_crud.get_task_geometry(db, project_id)
    file_path = f"/tmp/{project_id}_task_boundary.geojson"

    # Write the response content to the file
    with open(file_path, "w") as f:
        f.write(out)
    result = await project_crud.convert_geojson_to_osm(file_path)

    with open(result, "r") as f:
        content = f.read()

    response = Response(content=content, media_type="application/xml")
    return response


from sqlalchemy.sql import text


@router.get("/centroid/")
async def project_centroid(
    project_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Get a centroid of each projects.

    Parameters:
        project_id (int): The ID of the project.

    Returns:
        List[Tuple[int, str]]: A list of tuples containing the task ID and the centroid as a string.
    """
    query = text(
        f"""SELECT id, ARRAY_AGG(ARRAY[ST_X(ST_Centroid(outline)), ST_Y(ST_Centroid(outline))]) AS centroid
            FROM projects
            WHERE {f"id={project_id}" if project_id else "1=1"}
            GROUP BY id;"""
    )

    result = db.execute(query)
    result_dict_list = [{"id": row[0], "centroid": row[1]} for row in result.fetchall()]
    return result_dict_list
