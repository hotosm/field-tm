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
"""Functions for task submissions."""

import csv
import hashlib
import io
import json
import uuid
from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import sozipfile.sozipfile as zipfile
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Response
from loguru import logger as log

# from osm_fieldwork.json2osm import json2osm
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.central.central_crud import (
    get_odk_form,
    get_odk_project,
    list_odk_xforms,
)
from app.config import settings
from app.db import db_models
from app.models.enums import HTTPStatus
from app.projects import project_crud, project_deps
from app.s3 import add_obj_to_bucket, get_obj_from_bucket
from app.tasks import tasks_crud

# async def convert_json_to_osm(file_path):
#     """Wrapper for osm-fieldwork json2osm."""
#     osm_xml_path = json2osm(file_path)
#     return osm_xml_path


# TODO remove this
# async def convert_to_osm_for_task(odk_id: int, form_id: int, xform: any):
#     """Convert JSON --> OSM XML for a specific XForm/Task."""
#     # This file stores the submission data.
#     file_path = f"/tmp/{odk_id}_{form_id}.json"

#     # Get the submission data from ODK Central
#     file = xform.getSubmissions(odk_id, form_id, None, False, True)

#     if file is None:
#         return None, None

#     with open(file_path, "wb") as f:
#         f.write(file)

#     osmoutfile = await convert_json_to_osm(file_path)
#     return osmoutfile


# # FIXME 07/06/2024 since osm-fieldwork update
# def convert_to_osm(db: Session, project_id: int, task_id: Optional[int]):
#     """Convert submissions to OSM XML format."""
#     project_sync = async_to_sync(project_deps.get_project_by_id)
#     project = project_sync(db, project_id)

#     get_submission_sync = async_to_sync(get_submission_by_project)
#     data = get_submission_sync(project_id, {}, db)

#     submissions = data.get("value", [])

#     # Create a new ZIP file for the extracted files
#     final_zip_file_path = f"/tmp/{project.project_name_prefix}_osm.zip"

#     # Remove the ZIP file if it already exists
#     if os.path.exists(final_zip_file_path):
#         os.remove(final_zip_file_path)

#     # filter submission by task_id
#     if task_id:
#         submissions = [
#             sub
#             for sub in submissions
#             if sub.get("task_id") == str(task_id)
#         ]

#     if not submissions:
#         raise HTTPException(status_code=404, detail="Submission not found")

#     # JSON FILE PATH
#     jsoninfile = "/tmp/json_infile.json"

#     # Write the submission to a file
#     with open(jsoninfile, "w") as f:
#         f.write(json.dumps(submissions))

#     # Convert the submission to osm xml format
#     convert_json_to_osm_sync = async_to_sync(convert_json_to_osm)

#     if osm_file_path := convert_json_to_osm_sync(jsoninfile):
#         with open(osm_file_path, "r") as osm_file:
#             osm_data = osm_file.read()
#             last_osm_index = osm_data.rfind("</osm>")
#             processed_xml_string = (
#                 osm_data[:last_osm_index] + osm_data[last_osm_index + len("</osm>") :]
#             )

#         with open(osm_file_path, "w") as osm_file:
#             osm_file.write(processed_xml_string)

#         final_zip_file_path = f"/tmp/{project.project_name_prefix}_osm.zip"
#         if os.path.exists(final_zip_file_path):
#             os.remove(final_zip_file_path)

#         with zipfile.ZipFile(final_zip_file_path, mode="a") as final_zip_file:
#             final_zip_file.write(osm_file_path)

#     return final_zip_file_path


async def gather_all_submission_csvs(db: Session, project: db_models.DbProject):
    """Gather all of the submission CSVs for a project.

    Generate a single zip with all submissions.
    """
    log.info(f"Downloading all CSV submissions for project {project.id}")

    odkid = project.odkid

    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    xform = get_odk_form(odk_credentials)
    db_xform = await project_deps.get_project_xform(db, project.id)
    file = xform.getSubmissionMedia(odkid, db_xform.odk_form_id)
    return file.content


# FIXME not needed if the performance to retrieve submissions is good enough
def update_submission_in_s3(
    db: Session, project_id: int, background_task_id: uuid.UUID
):
    """Update or create new submission JSON in S3 for a project."""
    try:
        # Get Project
        get_project_sync = async_to_sync(project_crud.get_project)
        project = get_project_sync(db, project_id)

        # Gather metadata
        odk_sync = async_to_sync(project_deps.get_odk_credentials)
        odk_credentials = odk_sync(db, project_id)
        odk_forms = list_odk_xforms(project.odkid, odk_credentials, True)

        if not odk_forms:
            msg = f"No odk forms returned for project ({project_id})"
            log.warning(msg)
            return HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        # Get latest submission date
        valid_datetimes = [
            form["lastSubmission"]
            for form in odk_forms
            if form["lastSubmission"] is not None
        ]

        review_states = [
            form["reviewStates"]
            for form in odk_forms
            if form["reviewStates"] is not None
        ]

        last_submission = (
            max(
                valid_datetimes,
                key=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"),
            )
            if valid_datetimes
            else None
        )
        if not last_submission:
            msg = f"Could not identify last submission for project ({project_id})"
            log.warning(msg)
            return HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=msg,
            )

        # Check if the file already exists in s3
        s3_project_path = f"/{project.organisation_id}/{project_id}"
        metadata_s3_path = f"/{s3_project_path}/submissions.meta.json"
        try:
            # Get the last submission date and review state from the metadata
            data = get_obj_from_bucket(settings.S3_BUCKET_NAME, metadata_s3_path)
            submission_metadata = json.loads(data.getvalue())

            zip_file_last_submission = submission_metadata["last_submission"]
            zip_file_review_states = (
                submission_metadata["review_states"]
                if "review_states" in submission_metadata
                else None
            )

            # converting list into hash str to compare them easily
            odk_review_state_hash = hashlib.sha256(
                json.dumps(review_states).encode()
            ).hexdigest()
            s3_review_state_hash = hashlib.sha256(
                json.dumps(zip_file_review_states).encode()
            ).hexdigest()

            if (
                last_submission <= zip_file_last_submission
                and odk_review_state_hash == s3_review_state_hash
            ):
                # Update background task status to COMPLETED
                update_bg_task_sync = async_to_sync(
                    project_crud.update_background_task_status_in_database
                )
                update_bg_task_sync(db, background_task_id, 4)  # 4 is COMPLETED
                return

        except Exception as e:
            log.warning(str(e))

        # Zip file is outdated, regenerate
        metadata = {
            "last_submission": last_submission,
            "review_states": review_states,
        }

        # Get submissions from ODK Central
        get_submission_sync = async_to_sync(get_submission_by_project)
        submissions = get_submission_sync(project_id, {}, db)

        submissions_zip = BytesIO()
        # Create a sozipfile with metadata and submissions
        with zipfile.ZipFile(
            submissions_zip,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            chunk_size=zipfile.SOZIP_DEFAULT_CHUNK_SIZE,
        ) as myzip:
            myzip.writestr("submissions.json", json.dumps(submissions))

        # Add zipfile to the s3 bucket
        add_obj_to_bucket(
            settings.S3_BUCKET_NAME,
            submissions_zip,
            f"/{s3_project_path}/submission.zip",
        )

        # Upload metadata to s3
        metadata_obj = BytesIO(json.dumps(metadata).encode())
        add_obj_to_bucket(
            settings.S3_BUCKET_NAME,
            metadata_obj,
            metadata_s3_path,
        )

        # Update background task status to COMPLETED
        update_bg_task_sync = async_to_sync(
            project_crud.update_background_task_status_in_database
        )
        update_bg_task_sync(db, background_task_id, 4)  # 4 is COMPLETED

        return True

    except Exception as e:
        log.warning(str(e))
        # Update background task status to FAILED
        update_bg_task_sync = async_to_sync(
            project_crud.update_background_task_status_in_database
        )
        update_bg_task_sync(db, background_task_id, 2, str(e))  # 2 is FAILED


def get_all_submissions_json(db: Session, project_id):
    """Get all submissions for a project in JSON format."""
    get_project_sync = async_to_sync(project_crud.get_project)
    project_info = get_project_sync(db, project_id)

    # ODK Credentials
    odk_sync = async_to_sync(project_deps.get_odk_credentials)
    odk_credentials = odk_sync(db, project_id)
    project = get_odk_project(odk_credentials)

    get_task_id_list_sync = async_to_sync(tasks_crud.get_task_id_list)
    task_list = get_task_id_list_sync(db, project_id)

    # FIXME use db_xform
    xform_list = [
        f"{project_info.project_name_prefix}_task_{task}" for task in task_list
    ]
    # FIXME use separate func
    submissions = project.getAllSubmissions(project_info.odkid, xform_list)
    return submissions


async def download_submission_in_json(db: Session, project: db_models.DbProject):
    """Download submission data from ODK Central."""
    project_name = project.project_name_prefix

    if data := await get_submission_by_project(project, {}, db):
        json_data = data
    else:
        json_data = None

    json_bytes = BytesIO(json.dumps(json_data).encode("utf-8"))
    headers = {
        "Content-Disposition": f"attachment; filename={project_name}_submissions.json"
    }
    return Response(content=json_bytes.getvalue(), headers=headers)


async def get_submission_points(db: Session, project_id: int, task_id: Optional[int]):
    """Get submission points for a project."""
    project_info = await project_crud.get_project_by_id(db, project_id)
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odk_id = project_info.odkid
    odk_credentials = await project_deps.get_odk_credentials(db, project_id)
    xform = get_odk_form(odk_credentials)
    db_xform = await project_deps.get_project_xform(db, project_id)

    response_file = xform.getSubmissionMedia(odk_id, db_xform.odk_form_id)
    response_file_bytes = response_file.content

    try:
        with zipfile.ZipFile(io.BytesIO(response_file_bytes), "r") as zip_ref:
            csv_filenames = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if not csv_filenames:
                print("No CSV files found in the zip archive.")
                return None

            csv_filename = csv_filenames[0]
            with zip_ref.open(csv_filename) as csv_file:
                csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
                geometry = []

                for row in csv_reader:
                    if not task_id or int(row["all-task_id"]) == task_id:
                        latitude = row.get("warmup-Latitude")
                        longitude = row.get("warmup-Longitude")
                        if latitude and longitude:
                            point = (latitude, longitude)
                            geometry.append(
                                {
                                    "type": "Feature",
                                    "geometry": {"type": "Point", "coordinates": point},
                                }
                            )

                return geometry

    except zipfile.BadZipFile:
        print("The file is not a valid zip file.")
        return None


async def get_submission_count_of_a_project(db: Session, project: db_models.DbProject):
    """Return the total number of submissions made for a project."""
    # ODK Credentials
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    db_xform = await project_deps.get_project_xform(db, project.id)
    data = xform.listSubmissions(project.odkid, db_xform.odk_form_id, {})
    return len(data["value"])


async def get_submissions_by_date(
    db: Session,
    project: db_models.DbProject,
    days: int,
    planned_task: Optional[int] = None,
):
    """Get submissions by date.

    Fetches the submissions for a given project within a specified number of days.

    Args:
        db (Session): The database session.
        project (DbProject): The database project object.
        days (int): The number of days to consider for fetching submissions.
        planned_task (int): Associated task id.

    Returns:
        dict: A dictionary containing the submission counts for each date.

    Examples:
        # Fetch submissions for project with ID 1 within the last 7 days
        submissions = await get_submissions_by_date(db, 1, 7)
    """
    data = await get_submission_by_project(project, {}, db)

    end_dates = [
        datetime.fromisoformat(entry["end"].split("+")[0])
        for entry in data["value"]
        if entry.get("end")
    ]

    dates = [
        date.strftime("%m/%d")
        for date in end_dates
        if datetime.now() - date <= timedelta(days=days)
    ]

    submission_counts = Counter(sorted(dates))

    response = [
        {"date": key, "count": value} for key, value in submission_counts.items()
    ]
    if planned_task:
        count_dict = {}
        cummulative_count = 0
        for date, count in submission_counts.items():
            cummulative_count += count
            count_dict[date] = cummulative_count
        response = [
            {"date": key, "count": count_dict[key], "planned": planned_task}
            for key, value in submission_counts.items()
        ]

    return response


async def get_submission_by_project(
    project: db_models.DbProject,
    filters: dict,
    db: Session,
):
    """Get submission by project.

    Retrieves a paginated list of submissions for a given project.

    Args:
        project (DbProject): The database project object.
        filters (dict): The filters to apply directly to submissions
            in odk central.
        db (Session): The database session.

    Returns:
        Tuple[int, List]: A tuple containing the total number of submissions and
        the paginated list of submissions.

    Raises:
        ValueError: If the submission file cannot be found.

    """
    db_xform = await project_deps.get_project_xform(db, project.id)
    odk_central = await project_deps.get_odk_credentials(db, project.id)

    xform = get_odk_form(odk_central)
    return xform.listSubmissions(project.odkid, db_xform.odk_form_id, filters)


# FIXME this is not needed now it can be directly filtered from submission table
# async def get_submission_by_task(
#     project: db_models.DbProject,
#     task_id: int,
#     filters: dict,
#     db: Session,
# ):
#     """Get submissions and count by task.

#     Args:
#         project: The project instance.
#         task_id: The ID of the task.
#         filters: A dictionary of filters.
#         db: The database session.

#     Returns:
#         Tuple: A tuple containing the list of submissions and the count.
#     """
#     odk_credentials = await project_deps.get_odk_credentials(db, project.id)

#     xform = get_odk_form(odk_credentials)
#     db_xform = await project_deps.get_project_xform(db, project.id)
#     data = xform.listSubmissions(project.odkid, db_xform.odk_form_id, filters)
#     submissions = data.get("value", [])
#     count = data.get("@odata.count", 0)

#     return submissions, count


async def get_submission_detail(
    submission_id: str,
    project: db_models.DbProject,
    db: Session,
):
    """Get the details of a submission.

    Args:
        submission_id: The instance uuid of the submission.
        project: The project object representing the project.
        db: The database session.

    Returns:
        The details of the submission as a JSON object.
    """
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    odk_form = get_odk_form(odk_credentials)
    db_xform = await project_deps.get_project_xform(db, project.id)
    submission = json.loads(
        odk_form.getSubmissions(project.odkid, db_xform.odk_form_id, submission_id)
    )
    return submission.get("value", [])[0]


# FIXME might not needed
# async def get_submission_geojson(
#     project_id: int,
#     db: Session,
# ):
#     """Retrieve GeoJSON data for a submission associated with a project.

#     Args:
#         project_id (int): The ID of the project.
#         db (Session): The database session.

#     Returns:
#         FeatCol: A GeoJSON FeatCol containing the submission features.
#     """
#     data = await get_submission_by_project(project_id, {}, db)
#     submission_json = data.get("value", [])

#     if not submission_json:
#         raise HTTPException(
#             status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
#             detail="Loading JSON submission failed",
#         )

#     all_features = []
#     for submission in submission_json:
#         keys_to_remove = ["meta", "__id", "__system"]
#         for key in keys_to_remove:
#             submission.pop(key)

#         data = {}
#         flatten_json(submission, data)

#         geojson_geom = await postgis_utils.javarosa_to_geojson_geom(
#             data.pop("xlocation", {}), geom_type="Polygon"
#         )

#         feature = geojson.Feature(geometry=geojson_geom, properties=data)
#         all_features.append(feature)

#     return geojson.FeatureCollection(features=all_features)


async def upload_attachment_to_s3(
    project_id: int, instance_ids: list, background_task_id: uuid.UUID, db: Session
):
    """Uploads attachments to S3 for a given project and instance IDs.

    Args:
        project_id (int): The ID of the project.
        instance_ids (list): List of instance IDs.
        background_task_id (uuid.UUID): The ID of the background task.
        db (Session): The database session.

    Returns:
        bool: True if the upload is successful.

    Raises:
        Exception: If an error occurs during the upload process.
    """
    try:
        project = await project_deps.get_project_by_id(db, project_id)
        db_xform = await project_deps.get_project_xform(db, project_id)
        odk_central = await project_deps.get_odk_credentials(db, project_id)
        xform = get_odk_form(odk_central)
        s3_bucket = settings.S3_BUCKET_NAME
        s3_base_path = f"{project.organisation_id}/{project_id}"

        # Fetch existing photos from the database
        existing_photos = db.execute(
            text("""
            SELECT submission_id, s3_path
            FROM submission_photos
            WHERE project_id = :project_id
            """),
            {"project_id": project_id},
        ).fetchall()

        existing_photos_dict = {}
        for submission_id, s3_path in existing_photos:
            existing_photos_dict[submission_id] = s3_path

        batch_insert_data = []
        for instance_id in instance_ids:
            submission_detail = await get_submission_detail(instance_id, project, db)
            attachments = submission_detail["verification"]["image"]

            if not isinstance(attachments, list):
                attachments = [attachments]

            for idx, filename in enumerate(attachments):
                s3_key = f"{s3_base_path}/{instance_id}/{idx + 1}.jpeg"
                img_url = f"{settings.S3_DOWNLOAD_ROOT}/{s3_bucket}/{s3_key}"

                # Skip if the img_url already exists in the database
                if img_url in existing_photos_dict.get(instance_id, []):
                    log.warning(
                        f"Image {img_url} for instance {instance_id} "
                        "already exists in DB. Skipping upload."
                    )
                    continue

                try:
                    attachment = xform.getSubmissionPhoto(
                        project.odkid,
                        str(instance_id),
                        db_xform.odk_form_id,
                        str(filename),
                    )
                    if attachment:
                        image_stream = io.BytesIO(attachment)

                        # Upload the attachment to S3
                        add_obj_to_bucket(
                            s3_bucket, image_stream, s3_key, content_type="image/jpeg"
                        )

                        # Collect the data for batch insert
                        batch_insert_data.append(
                            {
                                "project_id": project_id,
                                "task_id": submission_detail["task_id"],
                                "submission_id": instance_id,
                                "s3_path": img_url,
                            }
                        )

                except Exception as e:
                    log.warning(
                        f"Failed to process {filename} for instance {instance_id}: {e}"
                    )
                    continue

        # Perform batch insert if there are new records to insert
        if batch_insert_data:
            sql = text("""
            INSERT INTO submission_photos (
                    project_id,
                    task_id,
                    submission_id,
                    s3_path
                )
            VALUES (:project_id, :task_id, :submission_id, :s3_path)
            """)
            db.execute(sql, batch_insert_data)

        db.commit()
        return True

    except Exception as e:
        log.warning(str(e))
        # Update background task status to FAILED
        update_bg_task_sync = async_to_sync(
            project_crud.update_background_task_status_in_database
        )
        update_bg_task_sync(db, background_task_id, 2, str(e))
        return False
