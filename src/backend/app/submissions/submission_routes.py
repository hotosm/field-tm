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
"""Routes associated with data submission to and from ODK Central."""

import json
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from osm_fieldwork.odk_merge import OdkMerge
from osm_fieldwork.osmfile import OsmFile
from sqlalchemy.orm import Session

from app.central import central_crud
from app.config import settings
from app.db import database
from app.projects import project_crud, project_schemas
from app.submissions import submission_crud, submission_schemas
from app.tasks import tasks_crud

router = APIRouter(
    prefix="/submission",
    tags=["submission"],
    dependencies=[Depends(database.get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_submissions(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
) -> list[dict]:
    """Get all submissions made for a project.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        db (Session): The database session, automatically provided.

    Returns:
        list[dict]: The list of submissions.
    """
    return submission_crud.get_submission_of_project(db, project_id, task_id)


@router.get("/download")
async def download_submission(
    project_id: int,
    task_id: int = None,
    export_json: bool = True,
    db: Session = Depends(database.get_db),
):
    """Download the submissions for a given project.

    Returned as either a JSONResponse, or a file to download.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        export_json (bool): Export in JSON format, else returns a file.
        db (Session): The database session, automatically provided.

    Returns:
        Union[list[dict], File]: JSON of submissions, or submission file.
    """
    if not (task_id or export_json):
        file = submission_crud.gather_all_submission_csvs(db, project_id)
        return FileResponse(file)

    return await submission_crud.download_submission(
        db, project_id, task_id, export_json
    )


@router.get("/submission-points")
async def submission_points(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Get submission points for a given project.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        db (Session): The database session, automatically provided.

    Returns:
        File: a zip containing submission points.
    """
    return await submission_crud.get_submission_points(db, project_id, task_id)


@router.get("/convert-to-osm")
async def convert_to_osm(
    project_id: int,
    task_id: int = None,
    db: Session = Depends(database.get_db),
) -> str:
    """Convert JSON submissions to OSM XML for a project.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        db (Session): The database session, automatically provided.

    Returns:
        File: an OSM XML of submissions.
    """
    # NOTE runs in separate thread using run_in_threadpool
    converted = await run_in_threadpool(
        lambda: submission_crud.convert_to_osm(db, project_id, task_id)
    )
    return converted


@router.get("/get-submission-count/{project_id}")
async def get_submission_count(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Get the submission count for a project."""
    return await submission_crud.get_submission_count_of_a_project(db, project_id)


@router.post("/conflate_data")
async def conflate_osm_data(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Conflate submission data against existing OSM data."""
    # All Submissions JSON
    # NOTE runs in separate thread using run_in_threadpool
    submission = await run_in_threadpool(
        lambda: submission_crud.get_all_submissions_json(db, project_id)
    )

    # Data extracta file
    data_extracts_file = "/tmp/data_extracts_file.geojson"

    await project_crud.get_extracted_data_from_db(db, project_id, data_extracts_file)

    # Output file
    outfile = "/tmp/output_file.osm"
    # JSON FILE PATH
    jsoninfile = "/tmp/json_infile.json"

    # # Delete if these files already exist
    if os.path.exists(outfile):
        os.remove(outfile)
    if os.path.exists(jsoninfile):
        os.remove(jsoninfile)

    # Write the submission to a file
    with open(jsoninfile, "w") as f:
        f.write(json.dumps(submission))

    # Convert the submission to osm xml format
    osmoutfile = await submission_crud.convert_json_to_osm(jsoninfile)

    # Remove the extra closing </osm> tag from the end of the file
    with open(osmoutfile, "r") as f:
        osmoutfile_data = f.read()
        # Find the last index of the closing </osm> tag
        last_osm_index = osmoutfile_data.rfind("</osm>")
        # Remove the extra closing </osm> tag from the end
        processed_xml_string = (
            osmoutfile_data[:last_osm_index]
            + osmoutfile_data[last_osm_index + len("</osm>") :]
        )

    # Write the modified XML data back to the file
    with open(osmoutfile, "w") as f:
        f.write(processed_xml_string)

    odkf = OsmFile(outfile)
    osm = odkf.loadFile(osmoutfile)
    if osm:
        odk_merge = OdkMerge(data_extracts_file, None)
        data = odk_merge.conflateData(osm)
        return data
    return []


@router.post("/download-submission")
async def download_submission_json(
    background_tasks: BackgroundTasks,
    project_id: int,
    background_task_id: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    """Download submissions for a project in JSON format.

    TODO check for redundancy with submission/download endpoint and refactor.
    """
    # Get Project
    project = await project_crud.get_project(db, project_id)

    # Return existing export if complete
    if background_task_id:
        # Get the backgrund task status
        task_status, task_message = await project_crud.get_background_task_status(
            background_task_id, db
        )

        if task_status != 4:
            return project_schemas.BackgroundTaskStatus(
                status=task_status.name, message=task_message or ""
            )

        bucket_root = f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}"
        return JSONResponse(
            status_code=200,
            content=f"{bucket_root}/{project.organisation_id}/{project_id}/submission.zip",
        )

    # Create task in db and return uuid
    background_task_id = await project_crud.insert_background_task_into_database(
        db, "sync_submission", project_id
    )

    background_tasks.add_task(
        submission_crud.update_submission_in_s3, db, project_id, background_task_id
    )
    return JSONResponse(
        status_code=200,
        content={
            "Message": "Submission update process initiated",
            "task_id": str(background_task_id),
        },
    )


@router.get("/get_osm_xml/{project_id}")
async def get_osm_xml(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Get the submissions in OSM XML format for a project.

    TODO refactor to put logic in crud for easier testing.
    """
    # JSON FILE PATH
    jsoninfile = f"/tmp/{project_id}_json_infile.json"

    # # Delete if these files already exist
    if os.path.exists(jsoninfile):
        os.remove(jsoninfile)

    # All Submissions JSON
    # NOTE runs in separate thread using run_in_threadpool
    submission = await run_in_threadpool(
        lambda: submission_crud.get_all_submissions_json(db, project_id)
    )

    # Write the submission to a file
    with open(jsoninfile, "w") as f:
        f.write(json.dumps(submission))

    # Convert the submission to osm xml format
    osmoutfile = await submission_crud.convert_json_to_osm(jsoninfile)

    # Remove the extra closing </osm> tag from the end of the file
    with open(osmoutfile, "r") as f:
        osmoutfile_data = f.read()
        # Find the last index of the closing </osm> tag
        last_osm_index = osmoutfile_data.rfind("</osm>")
        # Remove the extra closing </osm> tag from the end
        processed_xml_string = (
            osmoutfile_data[:last_osm_index]
            + osmoutfile_data[last_osm_index + len("</osm>") :]
        )

    # Write the modified XML data back to the file
    with open(osmoutfile, "w") as f:
        f.write(processed_xml_string)

    # Create a plain XML response
    response = Response(content=processed_xml_string, media_type="application/xml")
    return response


@router.get("/submission_page/{project_id}")
async def get_submission_page(
    project_id: int,
    days: int,
    background_tasks: BackgroundTasks,
    planned_task: Optional[int] = None,
    db: Session = Depends(database.get_db),
):
    """Summary submissison details for submission page.

    Args:
        background_tasks (BackgroundTasks): FastAPI bg tasks, provided automatically.
        db (Session): The database session, automatically generated.
        project_id (int): The ID of the project.
        days (int): The number of days to consider for fetching submissions.
        planned_task (int): Associated task id.

    Returns:
        dict: A dictionary containing the submission counts for each date.
    """
    data = await submission_crud.get_submissions_by_date(
        db, project_id, days, planned_task
    )

    # Update submission cache in the background
    background_task_id = await project_crud.insert_background_task_into_database(
        db, "sync_submission", project_id
    )

    background_tasks.add_task(
        submission_crud.update_submission_in_s3, db, project_id, background_task_id
    )

    return data


@router.get("/submission_form_fields/{project_id}")
async def get_submission_form_fields(
    project_id: int, db: Session = Depends(database.get_db)
):
    """Retrieves the submission form for a specific project.

    Args:
        project_id (int): The ID of the project.
        db (Session): The database session, automatically generated.

    Returns:
        Any: The response from the submission form API.
    """
    project = await project_crud.get_project(db, project_id)
    task_list = await tasks_crud.get_task_id_list(db, project_id)
    odk_form = central_crud.get_odk_form(project)
    response = odk_form.form_fields(project.odkid, str(task_list[0]))
    return response


@router.get("/submission_table/{project_id}")
async def submission_table(
    background_tasks: BackgroundTasks,
    project_id: int,
    page: int = Query(1, ge=1),
    results_per_page: int = Query(13, le=100),
    db: Session = Depends(database.get_db),
):
    """This API returns the submission table of a project.

    Args:
        background_tasks (BackgroundTasks): The background tasks manager.

        project_id (int): The ID of the project.

        page (int, optional): The page number for pagination. Defaults to 1.

        results_per_page (int, optional): The number of results per page for pagination.
        Defaults to 13.

        db (Session, optional): The database session.

    Returns:
        PaginatedSubmissions: The paginated submission table of the project.

    """
    skip = (page - 1) * results_per_page
    limit = results_per_page
    count, data = await submission_crud.get_submission_by_project(
        project_id, skip, limit, db
    )
    background_task_id = await project_crud.insert_background_task_into_database(
        db, "sync_submission", project_id
    )

    background_tasks.add_task(
        submission_crud.update_submission_in_s3, db, project_id, background_task_id
    )
    pagination = await project_crud.get_pagination(page, count, results_per_page, count)
    response = submission_schemas.PaginatedSubmissions(
        results=data,
        pagination=submission_schemas.PaginationInfo(**pagination.dict()),
    )
    return response
