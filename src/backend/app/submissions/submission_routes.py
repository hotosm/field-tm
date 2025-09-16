# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Routes associated with data submission to and from ODK Central."""

import json
from io import BytesIO
from typing import Annotated, Optional

import geojson
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import JSONResponse, Response
from loguru import logger as log
from osm_fieldwork.OdkCentralAsync import OdkCentral
from psycopg import Connection
from pyodk._endpoints.submissions import Submission as CentralSubmissionOut

from app.auth.auth_schemas import ProjectUserDict
from app.auth.roles import Mapper, ProjectManager, project_contributors
from app.central import central_crud
from app.db import postgis_utils
from app.db.database import db_conn
from app.db.enums import HTTPStatus, SubmissionDownloadType
from app.db.models import DbTask
from app.projects import project_crud
from app.submissions import submission_crud, submission_deps, submission_schemas
from app.submissions.submission_crud import upload_submission_geojson_to_s3
from app.tasks.task_deps import get_task

router = APIRouter(
    prefix="/submission",
    tags=["submission"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def read_submissions(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
) -> list[dict]:
    """Get all submissions made for a project.

    Returns:
        list[dict]: The list of submissions.
    """
    project = project_user.get("project")
    data = await submission_crud.get_submission_by_project(project, {})
    return data.get("value", [])


@router.post("", response_model=CentralSubmissionOut)
async def create_submission(
    project_user: Annotated[ProjectUserDict, Depends(Mapper(check_completed=True))],
    submission_xml: Annotated[UploadFile, File()],
    device_id: Annotated[Optional[str], Form()] = None,
    submission_attachments: Annotated[
        Optional[dict[str, BytesIO]], Depends(submission_deps.read_submission_uploads)
    ] = None,
):
    """Create a new submission via ODK Central REST endpoint.

    Typically it would be best to use the OpenRosa submission endpoint,
    as used by ODK Collect.

    However, for now ODK Web Forms do not have direct ODK Central access
    configured. Meaning we must handle getting forms and submitting new
    data to ODK Central within Field-TM.

    This endpoint helps to facilitate, by allowing submission, alongside
    any form attachments, via the ODK Central REST API (via pyodk),
    """
    project = project_user.get("project")
    xml_str = (await submission_xml.read()).decode("utf-8")

    new_submission = await submission_crud.create_new_submission(
        project.odk_credentials,
        project.odkid,
        project.odk_form_id,
        xml_str,
        device_id,
        submission_attachments,
    )

    # Ensure S3 photos are upload to S3 after upload
    async with OdkCentral(
        url=project.odk_credentials.odk_central_url,
        user=project.odk_credentials.odk_central_user,
        passwd=project.odk_credentials.odk_central_password,
    ) as odk_central:
        try:
            await odk_central.s3_sync()
        except Exception:
            log.warning(
                "Fails to sync media to S3 - is the linked ODK Central "
                "instance correctly configured?"
            )

    return new_submission


@router.get("/download")
async def download_submission(
    background_tasks: BackgroundTasks,
    project_user: Annotated[ProjectUserDict, Depends(project_contributors)],
    file_type: SubmissionDownloadType,
    submitted_date_range: Optional[str] = Query(
        None,
        title="Submitted Date Range",
        description="Date range in format (e.g., 'YYYY-MM-DD,YYYY-MM-DD')",
    ),
):
    """Download the submissions for a given project.

    Returns a JSON, CSV, or GeoJSON file.
    """
    project = project_user.get("project")
    filters = {}

    if submitted_date_range:
        start_date, end_date = submitted_date_range.split(",")
        filters = {
            "$filter": (
                f"__system/submissionDate ge {start_date}T00:00:00+00:00 "
                f"and __system/submissionDate le {end_date}T23:59:59.999+00:00"
            )
        }

    if file_type == SubmissionDownloadType.JSON:
        return await submission_crud.download_submission_in_json(project, filters)

    elif file_type == SubmissionDownloadType.CSV:
        file_content = await submission_crud.gather_all_submission_csvs(
            project, filters
        )
        headers = {"Content-Disposition": f"attachment; filename={project.slug}.zip"}
        return Response(file_content, headers=headers)

    # Else is GeoJSON download
    submission_geojson = await submission_crud.get_project_submission_geojson(
        project, filters
    )
    background_tasks.add_task(
        upload_submission_geojson_to_s3, project, submission_geojson
    )
    submission_data = BytesIO(json.dumps(submission_geojson).encode("utf-8"))

    headers = {"Content-Disposition": f"attachment; filename={project.slug}.geojson"}
    return Response(submission_data.getvalue(), headers=headers)


# # FIXME 07/06/2024 since osm-fieldwork update
# @router.get("/convert-to-osm")
# async def convert_to_osm(
#     db: Annotated[Connection, Depends(db_conn)],
#     current_user: Annotated[AuthUser, Depends(login_required)],
#     project_id: int,
#     task_id: Optional[int] = None,
# ):
#     """Convert JSON submissions to OSM XML for a project.

#     Args:
#         project_id (int): The ID of the project.
#         task_id (int, optional): The ID of the task.
#             If provided, returns the submissions made for a specific task only.
#         db (Connection): The database connection.
#         current_user (AuthUser): Check if user is logged in.

#     Returns:
#         File: an OSM XML of submissions.
#     """
#     # NOTE runs in separate thread using run_in_threadpool
#     return FileResponse(
#         await run_in_threadpool(
#             lambda: submission_crud.convert_to_osm(db, project_id, task_id)
#         )
#     )


@router.get("/get-submission-count")
async def get_submission_count(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Get the submission count for a project."""
    project = project_user.get("project")
    return await submission_crud.get_submission_count_of_a_project(project)


# FIXME 07/06/2024 since osm-fieldwork update
# @router.post("/conflate_data")
# async def conflate_osm_data(
#     db: Annotated[Connection, Depends(db_conn)],
#     project_id: int,
#     current_user: Annotated[AuthUser, Depends(login_required)],
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


# FIXME 07/06/2024 since osm-fieldwork update
# @router.get("/get_osm_xml/{project_id}")
# async def get_osm_xml(
#     db: Annotated[Connection, Depends(db_conn)],
#     project_id: int,
#     current_user: Annotated[AuthUser, Depends(login_required)],
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


@router.get("/submission-form-fields")
async def get_submission_form_fields(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """Retrieves the submission form for a specific project.

    Returns:
        Any: The response from the submission form API.
    """
    project = project_user.get("project")
    odk_form = central_crud.get_odk_form(project.odk_credentials)
    return odk_form.formFields(project.odkid, project.odk_form_id)


@router.get("/submission-table")
async def submission_table(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    page: int = Query(1, ge=1),
    results_per_page: int = Query(13, le=100),
    task_id: Optional[int] = None,
    submitted_by: Optional[str] = None,
    review_state: Optional[str] = None,
    submitted_date_range: Optional[str] = Query(
        None,
        title="Submitted Date Range",
        description="Date range in format (e.g., 'YYYY-MM-DD,YYYY-MM-DD')",
    ),
):
    """This api returns the submission table of a project.

    Returns:
        dict: Paginated submissions with `results` and `pagination` keys.
    """
    project = project_user.get("project")
    filters = {
        "$count": True,
        "$wkt": True,
    }

    filter_clauses = []

    if submitted_date_range:
        start_date, end_date = submitted_date_range.split(",")
        filter_clauses.append(
            f"__system/submissionDate ge {start_date}T00:00:00+00:00 "
            f"and __system/submissionDate le {end_date}T23:59:59.999+00:00"
        )

    if review_state and review_state != "received":
        filter_clauses.append(f"__system/reviewState eq '{review_state}'")

    if filter_clauses:
        filters["$filter"] = " and ".join(filter_clauses)

    data = await submission_crud.get_submission_by_project(project, filters)

    submissions = data.get("value", [])

    if review_state == "received":
        submissions = [
            sub for sub in submissions if sub["__system"].get("reviewState") is None
        ]

    if task_id:
        submissions = [sub for sub in submissions if sub.get("task_id") == str(task_id)]

    if submitted_by:
        submissions = [
            sub for sub in submissions if sub.get("username") == submitted_by
        ]

    total_count = len(submissions)
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    paginated_submissions = submissions[start_index:end_index]

    pagination = await project_crud.get_pagination(
        page, len(submissions), results_per_page, total_count
    )

    return submission_schemas.PaginatedSubmissions(
        results=paginated_submissions,
        pagination=submission_schemas.PaginationInfo(**pagination.model_dump()),
    )


@router.post(
    "/update-review-state",
    response_model=submission_schemas.ReviewStateOut,
)
async def update_review_state(
    post_data: submission_schemas.ReviewStateIn,
    current_user: Annotated[
        ProjectUserDict, Depends(ProjectManager(check_completed=True))
    ],
):
    """Updates the review state of a project submission."""
    try:
        project = current_user.get("project")
        odk_project = central_crud.get_odk_project(project.odk_credentials)

        response = odk_project.updateReviewState(
            project.odkid,
            project.odk_form_id,
            post_data.instance_id,
            {"reviewState": post_data.review_state},
        )
        # FIXME we have this due to bad exception handling code in osm-fieldwork
        if response == {}:
            raise Exception(
                "ODK Central could not find or process the submission "
                f"({post_data.instance_id})"
            )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.get("/conflate-submission-geojson")
async def conflate_geojson(
    db_task: Annotated[DbTask, Depends(get_task)],
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    remove_conflated: Annotated[
        bool,
        Query(
            description="Removes geometries not overlapping with OSM data",
        ),
    ] = False,
):
    """Conflates the input GeoJSON with OpenStreetMap data.

    Returns:
        str: Updated GeoJSON string with conflated features.
    """
    try:
        project = project_user.get("project")
        task_geojson = geojson.dumps(db_task.outline, indent=2)

        data = await submission_crud.get_submission_by_project(project, {})
        submission_json = data.get("value", [])
        task_submission = [
            sub for sub in submission_json if sub["task_id"] == str(db_task.id)
        ]

        if not task_submission:
            return JSONResponse(
                status_code=HTTPStatus.NOT_FOUND,
                content=f"No Submissions found within the task {db_task.id}",
            )

        submission_geojson = await central_crud.convert_odk_submission_json_to_geojson(
            task_submission
        )
        osm_category = project.osm_category
        input_features = submission_geojson["features"]

        osm_features = await postgis_utils.get_osm_geometries(
            osm_category, task_geojson
        )
        conflated_features = postgis_utils.conflate_features(
            input_features, osm_features.get("features", []), remove_conflated
        )
        submission_geojson["features"] = conflated_features

        return submission_geojson
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to process conflation: {str(e)}",
        ) from e


@router.get("/{submission_id}/photos", response_model=dict[str, str])
async def submission_photos(
    submission_id: str,
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """This api returns the submission detail of individual submission.

    NOTE Prerequisites:

    1) The ODK server must have the S3_ENDPOINT param set to enable
       S3 media uploads.

       If it's not set, then these URLs will be direct downloads from ODK
       (requiring auth).

       If the S3 is configured, then these URLs should be pre-signed download
       links to S3.

    2) The media is uploaded to S3 by using `node lib/bin/s3.js upload-pending`
       in the Central container (this is triggered automatically every 24hrs).
    """
    project = project_user.get("project")
    submission_attachment_urls = await submission_crud.get_submission_photos(
        submission_id,
        project,
    )  # this is a dict {filename:url}

    return submission_attachment_urls


@router.get(
    "/{project_id}/dashboard", response_model=submission_schemas.SubmissionDashboard
)
async def project_submission_dashboard(
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
    db: Annotated[Connection, Depends(db_conn)],
):
    """Get the project dashboard details."""
    project = project_user.get("project")
    details = await submission_crud.get_dashboard_detail(db, project)
    details["slug"] = project.slug
    details["organisation_id"] = project.organisation_id
    details["organisation_name"] = project.organisation_name
    details["created_at"] = project.created_at
    details["organisation_logo"] = project.organisation_logo
    details["last_active"] = project.last_active
    details["status"] = project.status
    return details


@router.get("/{submission_id}")
async def submission_detail(
    submission_id: str,
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
) -> dict:
    """This api returns the submission detail of individual submission."""
    project = project_user.get("project")
    submission_detail = await submission_crud.get_submission_detail(
        submission_id,
        project,
    )
    return submission_detail


@router.put("/{submission_id}", response_model=CentralSubmissionOut)
async def edit_submission(
    submission_id: str,
    project_user: Annotated[ProjectUserDict, Depends(Mapper(check_completed=True))],
    submission_xml: Annotated[UploadFile, File()],
    device_id: Annotated[Optional[str], Form()] = None,
    submission_attachments: Annotated[
        Optional[dict[str, BytesIO]], Depends(submission_deps.read_submission_uploads)
    ] = None,
):
    """Edit an existing submission.

    This endpoint allows updating a submission by uploading a new XML and optional
    attachments.
    """
    project = project_user.get("project")
    xml_str = (await submission_xml.read()).decode("utf-8")

    updated_submission = await submission_crud.edit_submission(
        project.odk_credentials,
        project.odkid,
        project.odk_form_id,
        submission_id,
        xml_str,
        device_id,
        submission_attachments,
    )

    async with OdkCentral(
        url=project.odk_credentials.odk_central_url,
        user=project.odk_credentials.odk_central_user,
        passwd=project.odk_credentials.odk_central_password,
    ) as odk_central:
        try:
            await odk_central.s3_sync()
        except Exception:
            log.warning("Fails to sync media to S3 after edit.")

    return updated_submission


@router.get("/{submission_id}/versions")
async def list_submission_versions(
    submission_id: str,
    project_user: Annotated[ProjectUserDict, Depends(Mapper())],
):
    """List all versions of a submission."""
    project = project_user.get("project")
    versions = await submission_crud.list_submission_versions(
        project.odk_credentials,
        project.odkid,
        project.odk_form_id,
        submission_id,
    )
    return versions
