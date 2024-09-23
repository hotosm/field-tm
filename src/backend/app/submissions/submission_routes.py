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
import uuid
from io import BytesIO
from typing import Annotated, Optional

import geojson
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, Response
from loguru import logger as log
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.auth_schemas import AuthUser, ProjectUserDict
from app.auth.osm import login_required
from app.auth.roles import mapper, project_manager
from app.central import central_crud
from app.db import database, postgis_utils
from app.models.enums import HTTPStatus, ReviewStateEnum
from app.projects import project_crud, project_deps
from app.submissions import submission_crud, submission_schemas
from app.tasks.task_deps import get_task_by_id

router = APIRouter(
    prefix="/submission",
    tags=["submission"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_submissions(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
) -> list[dict]:
    """Get all submissions made for a project.

    Returns:
        list[dict]: The list of submissions.
    """
    project = project_user.get("project")
    data = await submission_crud.get_submission_by_project(project, {}, db)
    return data.get("value", [])


@router.get("/download")
async def download_submission(
    export_json: bool = True,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Download the submissions for a given project.

    Returned as either a JSONResponse, or a file to download.

    Returns:
        Union[list[dict], File]: JSON of submissions, or submission file.
    """
    project = project_user.get("project")
    project_name = project.project_name_prefix
    if not export_json:
        file_content = await submission_crud.gather_all_submission_csvs(db, project)
        headers = {"Content-Disposition": f"attachment; filename={project_name}.zip"}
        return Response(file_content, headers=headers)

    return await submission_crud.download_submission_in_json(db, project)


@router.get("/submission-points")
async def submission_points(
    project_id: int,
    task_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Get submission points for a given project.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        db (Session): The database session, automatically provided.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        File: a zip containing submission points.
    """
    return await submission_crud.get_submission_points(db, project_id, task_id)


@router.get("/convert-to-osm")
async def convert_to_osm(
    project_id: int,
    task_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Convert JSON submissions to OSM XML for a project.

    Args:
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task.
            If provided, returns the submissions made for a specific task only.
        db (Session): The database session, automatically provided.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        File: an OSM XML of submissions.
    """
    # NOTE runs in separate thread using run_in_threadpool
    return FileResponse(
        await run_in_threadpool(
            lambda: submission_crud.convert_to_osm(db, project_id, task_id)
        )
    )


@router.get("/get-submission-count")
async def get_submission_count(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Get the submission count for a project."""
    project = project_user.get("project")
    return await submission_crud.get_submission_count_of_a_project(db, project)


# FIXME 07/06/2024 since osm-fieldwork update
# @router.post("/conflate_data")
# async def conflate_osm_data(
#     project_id: int,
#     db: Session = Depends(database.get_db),
#     current_user: AuthUser = Depends(login_required),
# ):
#     """Conflate submission data against existing OSM data."""
#     # All Submissions JSON
#     # NOTE runs in separate thread using run_in_threadpool
#     # FIXME we probably need to change this func
#     submission = await run_in_threadpool(
#         lambda: submission_crud.get_all_submissions_json(db, project_id)
#     )

#     # Data extracta file
#     data_extracts_file = "/tmp/data_extracts_file.geojson"

#     await project_crud.get_extracted_data_from_db(db, project_id, data_extracts_file)

#     # Output file
#     outfile = "/tmp/output_file.osm"
#     # JSON FILE PATH
#     jsoninfile = "/tmp/json_infile.json"

#     # # Delete if these files already exist
#     if os.path.exists(outfile):
#         os.remove(outfile)
#     if os.path.exists(jsoninfile):
#         os.remove(jsoninfile)

#     # Write the submission to a file
#     with open(jsoninfile, "w") as f:
#         f.write(json.dumps(submission))

#     # Convert the submission to osm xml format
#     osmoutfile = await submission_crud.convert_json_to_osm(jsoninfile)

#     # Remove the extra closing </osm> tag from the end of the file
#     with open(osmoutfile, "r") as f:
#         osmoutfile_data = f.read()
#         # Find the last index of the closing </osm> tag
#         last_osm_index = osmoutfile_data.rfind("</osm>")
#         # Remove the extra closing </osm> tag from the end
#         processed_xml_string = (
#             osmoutfile_data[:last_osm_index]
#             + osmoutfile_data[last_osm_index + len("</osm>") :]
#         )

#     # Write the modified XML data back to the file
#     with open(osmoutfile, "w") as f:
#         f.write(processed_xml_string)

#     odkf = OsmFile(outfile)
#     osm = odkf.loadFile(osmoutfile)
#     if osm:
#         odk_merge = OdkMerge(data_extracts_file, None)
#         data = odk_merge.conflateData(osm)
#         return data
#     return []


# TODO remove this redundant endpoint
# @router.post("/download-submission")
# async def download_submission_json(
#     background_tasks: BackgroundTasks,
#     project_id: int,
#     background_task_id: Optional[str] = None,
#     db: Session = Depends(database.get_db),
#     current_user: AuthUser = Depends(mapper),
# ):
#     """Download submissions for a project in JSON format.

#     TODO check for redundancy with submission/download endpoint and refactor.
#     """
#     # Get Project
#     project = await project_crud.get_project(db, project_id)

#     # Return existing export if complete
#     if background_task_id:
#         # Get the background task status
#         task_status, task_message = await project_crud.get_background_task_status(
#             background_task_id, db
#         )

#         if task_status != 4:
#             return project_schemas.BackgroundTaskStatus(
#                 status=task_status.name, message=task_message or ""
#             )

#         bucket_root = f"{settings.S3_DOWNLOAD_ROOT}/{settings.S3_BUCKET_NAME}"
#         return JSONResponse(
#        status_code=200,
#        content=f"{bucket_root}/{project.organisation_id}/{project_id}/submission.zip",
#       )
#     # Create task in db and return uuid
#     background_task_id = await project_crud.insert_background_task_into_database(
#         db, "sync_submission", project_id
#     )

#     background_tasks.add_task(
#         submission_crud.update_submission_in_s3, db, project_id, background_task_id
#     )
#     return JSONResponse(
#         status_code=200,
#         content={
#             "Message": "Submission update process initiated",
#             "task_id": str(background_task_id),
#         },
#     )


# FIXME 07/06/2024 since osm-fieldwork update
# @router.get("/get_osm_xml/{project_id}")
# async def get_osm_xml(
#     project_id: int,
#     db: Session = Depends(database.get_db),
#     current_user: AuthUser = Depends(login_required),
# ):
#     """Get the submissions in OSM XML format for a project.

#     TODO refactor to put logic in crud for easier testing.
#     """
#     # JSON FILE PATH
#     jsoninfile = f"/tmp/{project_id}_json_infile.json"

#     # # Delete if these files already exist
#     if os.path.exists(jsoninfile):
#         os.remove(jsoninfile)

#     # All Submissions JSON
#     # NOTE runs in separate thread using run_in_threadpool
#     # FIXME we probably need to change this func
#     submission = await run_in_threadpool(
#         lambda: submission_crud.get_all_submissions_json(db, project_id)
#     )

#     # Write the submission to a file
#     with open(jsoninfile, "w") as f:
#         f.write(json.dumps(submission))

#     # Convert the submission to osm xml format
#     osmoutfile = await submission_crud.convert_json_to_osm(jsoninfile)

#     # Remove the extra closing </osm> tag from the end of the file
#     with open(osmoutfile, "r") as f:
#         osmoutfile_data = f.read()

#     # Create a plain XML response
#     return Response(content=osmoutfile_data, media_type="application/xml")


@router.get("/submission_page")
async def get_submission_page(
    days: int,
    planned_task: Optional[int] = None,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Summary submissison details for submission page.

    Returns:
        dict: A dictionary containing the submission counts for each date.
    """
    project = project_user.get("project")
    data = await submission_crud.get_submissions_by_date(
        db, project, days, planned_task
    )

    return data


@router.get("/submission_form_fields")
async def get_submission_form_fields(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Retrieves the submission form for a specific project.

    Returns:
        Any: The response from the submission form API.
    """
    project = project_user.get("project")
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    odk_form = central_crud.get_odk_form(odk_credentials)
    return odk_form.formFields(project.odkid, project.odk_form_id)


@router.get("/submission_table")
async def submission_table(
    background_tasks: BackgroundTasks,
    page: int = Query(1, ge=1),
    results_per_page: int = Query(13, le=100),
    background_task_id: Optional[uuid.UUID] = None,
    task_id: Optional[int] = None,
    submitted_by: Optional[str] = None,
    review_state: Optional[str] = None,
    submitted_date: Optional[str] = Query(
        None, title="Submitted Date", description="Date in format (e.g., 'YYYY-MM-DD')"
    ),
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """This api returns the submission table of a project.

    Returns:
        dict: Paginated submissions with `results` and `pagination` keys.
    """
    project = project_user.get("project")
    skip = (page - 1) * results_per_page
    filters = {
        "$top": results_per_page,
        "$skip": skip,
        "$count": True,
        "$wkt": True,
    }

    if submitted_date:
        filters["$filter"] = (
            "__system/submissionDate ge {}T00:00:00+00:00 "
            "and __system/submissionDate le {}T23:59:59.999+00:00"
        ).format(submitted_date, submitted_date)

    if submitted_by:
        if "$filter" in filters:
            filters["$filter"] += f"and (username eq '{submitted_by}')"
        else:
            filters["$filter"] = f"username eq '{submitted_by}'"

    if review_state:
        if "$filter" in filters:
            filters["$filter"] += f" and (__system/reviewState eq '{review_state}')"
        else:
            filters["$filter"] = f"__system/reviewState eq '{review_state}'"

    data = await submission_crud.get_submission_by_project(project, filters, db)
    count = data.get("@odata.count", 0)
    submissions = data.get("value", [])
    instance_ids = []
    for submission in submissions:
        if submission["__system"]["attachmentsPresent"] != 0:
            instance_ids.append(submission["__id"])

    if instance_ids:
        background_task_id = await project_crud.insert_background_task_into_database(
            db, "upload_submission_photos", project.id
        )
        log.info("uploading submission photos to s3")
        background_tasks.add_task(
            submission_crud.upload_attachment_to_s3,
            project.id,
            instance_ids,
            background_task_id,
            db,
        )

    if task_id:
        submissions = [sub for sub in submissions if sub.get("task_id") == str(task_id)]

    pagination = await project_crud.get_pagination(page, count, results_per_page, count)
    response = submission_schemas.PaginatedSubmissions(
        results=submissions,
        pagination=submission_schemas.PaginationInfo(**pagination.model_dump()),
    )

    return response


@router.post("/update_review_state")
async def update_review_state(
    instance_id: str,
    review_state: ReviewStateEnum,
    current_user: ProjectUserDict = Depends(project_manager),
    db: Session = Depends(database.get_db),
):
    """Updates the review state of a project submission."""
    try:
        project = current_user.get("project")
        odk_creds = await project_deps.get_odk_credentials(db, project.id)
        odk_project = central_crud.get_odk_project(odk_creds)

        response = odk_project.updateReviewState(
            project.odkid,
            project.odk_form_id,
            instance_id,
            {"reviewState": review_state},
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/download-submission-geojson")
async def download_submission_geojson(
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
):
    """Download submission geojson for a specific project."""
    project = project_user.get("project")
    data = await submission_crud.get_submission_by_project(project, {}, db)
    submission_json = data.get("value", [])

    submission_geojson = await central_crud.convert_odk_submission_json_to_geojson(
        submission_json
    )
    submission_data = BytesIO(json.dumps(submission_geojson).encode("utf-8"))
    filename = project.project_name_prefix

    headers = {"Content-Disposition": f"attachment; filename={filename}.geojson"}

    return Response(submission_data.getvalue(), headers=headers)


@router.get("/conflate-submission-geojson/")
async def conflate_geojson(
    task_id: int,
    project_user: ProjectUserDict = Depends(mapper),  # FIXME change this to validator
    remove_conflated: Annotated[
        bool,
        Query(
            description="Removes geometries not overlapping with OSM data",
        ),
    ] = False,
    db: Session = Depends(database.get_db),
):
    """Conflates the input GeoJSON with OpenStreetMap data.

    Returns:
        str: Updated GeoJSON string with conflated features.
    """
    try:
        project = project_user.get("project")
        db_task = await get_task_by_id(project.id, task_id, db)
        task_aoi = postgis_utils.wkb_geom_to_feature(db_task.outline)
        task_geojson = geojson.dumps(task_aoi, indent=2)

        data = await submission_crud.get_submission_by_project(project, {}, db)
        submission_json = data.get("value", [])
        task_submission = [
            sub for sub in submission_json if sub["task_id"] == str(task_id)
        ]

        if not task_submission:
            return JSONResponse(
                status_code=HTTPStatus.NOT_FOUND,
                content=f"No Submissions found within the task {task_id}",
            )

        submission_geojson = await central_crud.convert_odk_submission_json_to_geojson(
            task_submission
        )
        form_category = project.xform_category
        input_features = submission_geojson["features"]

        osm_features = postgis_utils.get_osm_geometries(form_category, task_geojson)
        conflated_features = postgis_utils.conflate_features(
            input_features, osm_features.get("features", []), remove_conflated
        )
        submission_geojson["features"] = conflated_features

        return submission_geojson
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process conflation: {str(e)}"
        ) from e


@router.get("/{submission_id}")
async def submission_detail(
    submission_id: str,
    db: Session = Depends(database.get_db),
    project_user: ProjectUserDict = Depends(mapper),
) -> dict:
    """This api returns the submission detail of individual submission."""
    project = project_user.get("project")
    submission_detail = await submission_crud.get_submission_detail(
        submission_id, project, db
    )
    return submission_detail


@router.get("/{submission_id}/photos")
async def submission_photo(
    submission_id: str,
    db: Session = Depends(database.get_db),
) -> dict:
    """Get submission photos.

    Retrieves the S3 paths of the submission photos for the given submission ID.

    Args:
        submission_id (str): The ID of the submission.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the S3 path of the submission photo.
            If no photo is found,
            the dictionary will contain a None value for the S3 path.

    Raises:
        HTTPException: If an error occurs while retrieving the submission photo.
    """
    try:
        sql = text("""
            SELECT
                s3_path
            FROM
                submission_photos
            WHERE
                submission_id = :submission_id;
        """)
        results = db.execute(sql, {"submission_id": submission_id}).fetchall()

        # Extract the s3_path from each result and return as a list
        s3_paths = [result.s3_path for result in results] if results else []

        return {"image_urls": s3_paths}

    except Exception as e:
        log.warning(
            f"Failed to get submission photos for submission {submission_id}: {e}"
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to get submission photos",
        ) from e
