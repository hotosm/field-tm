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

import concurrent.futures
import csv
import io
import json
import os
import threading
import uuid
from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO

import sozipfile.sozipfile as zipfile
from asgiref.sync import async_to_sync
from fastapi import HTTPException, Response
from fastapi.responses import FileResponse
from loguru import logger as log
from osm_fieldwork.json2osm import json2osm
from sqlalchemy.orm import Session

from app.central.central_crud import get_odk_form, get_odk_project, list_odk_xforms
from app.config import settings
from app.projects import project_crud, project_schemas
from app.s3 import add_obj_to_bucket, get_obj_from_bucket
from app.tasks import tasks_crud


def get_submission_of_project(db: Session, project_id: int, task_id: int = None):
    """Gets the submission of project.

    If task_id is provided, it submissions for a specific task,
    else all the submission made for a project are returned.
    """
    get_project_sync = async_to_sync(project_crud.get_project)
    project_info = get_project_sync(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        return []

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    if not (
        project_info.odk_central_url
        or project_info.odk_central_user
        or project_info.odk_central_password
    ):
        raise HTTPException(
            status_code=404, detail="ODK Central Credentials not found in project"
        )

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    xform = get_odk_form(odk_credentials)

    # If task id is not provided, submission for all the task are listed
    if task_id is None:
        task_list = []

        task_list = [x.id for x in project_tasks]

        data = []

        for id in task_list:
            # XML Form Id is a combination or project_name, category and task_id
            xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
            submission_list = xform.listSubmissions(odkid, xml_form_id)

            # data.append(submission_list)
            if isinstance(submission_list, list):
                for submission in submission_list:
                    data.append(submission)
        return data

    else:
        # If task_id is provided, submission made to this particular task is returned.
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
        submission_list = xform.listSubmissionBasicInfo(odkid, xml_form_id)
        for x in submission_list:
            x["submitted_by"] = f"{project_name}_{form_category}_{task_id}"
        return submission_list


async def convert_json_to_osm(file_path):
    """Wrapper for osm-fieldwork json2osm.

    FIXME add json output to osm2json (in addition to default OSM XML output)
    """
    # TODO check speed of json2osm
    # TODO if slow response, use run_in_threadpool
    osm_xml_path = json2osm(file_path)
    return osm_xml_path


async def convert_to_osm_for_task(odk_id: int, form_id: int, xform: any):
    """Convert JSON --> OSM XML for a specific XForm/Task."""
    # This file stores the submission data.
    file_path = f"/tmp/{odk_id}_{form_id}.json"

    # Get the submission data from ODK Central
    file = xform.getSubmissions(odk_id, form_id, None, False, True)

    if file is None:
        return None, None

    with open(file_path, "wb") as f:
        f.write(file)

    osmoutfile = await convert_json_to_osm(file_path)
    return osmoutfile


def convert_to_osm(db: Session, project_id: int, task_id: int):
    """Convert submissions to OSM XML format."""
    get_project_sync = async_to_sync(project_crud.get_project)
    project_info = get_project_sync(db, project_id)

    # Return exception if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    # Create a new ZIP file for the extracted files
    final_zip_file_path = f"/tmp/{project_name}_{form_category}_osm.zip"

    # Remove the ZIP file if it already exists
    if os.path.exists(final_zip_file_path):
        os.remove(final_zip_file_path)

    # Submission JSON
    if task_id:
        submission = xform.getSubmissions(odkid, task_id, None, False, True)
        submission = (json.loads(submission))["value"]
    else:
        submission = get_all_submissions_json(db, project_id)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # JSON FILE PATH
    jsoninfile = "/tmp/json_infile.json"

    # Write the submission to a file
    with open(jsoninfile, "w") as f:
        f.write(json.dumps(submission))

    # Convert the submission to osm xml format
    convert_json_to_osm_sync = async_to_sync(convert_json_to_osm)
    osmoutfile = convert_json_to_osm_sync(jsoninfile)

    # if osmoutfile and jsonoutfile:
    if osmoutfile:
        # FIXME: Need to fix this when generating osm file

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

        # Add the files to the ZIP file
        with zipfile.ZipFile(final_zip_file_path, mode="a") as final_zip_file:
            final_zip_file.write(osmoutfile)
            # final_zip_file.write(jsonoutfile)

    return FileResponse(final_zip_file_path)


def gather_all_submission_csvs(db, project_id):
    """Gather all of the submission CSVs for a project.

    Generate a single zip with all submissions.
    """
    log.info(f"Downloading all CSV submissions for project {project_id}")

    get_project_sync = async_to_sync(project_crud.get_project)
    project_info = get_project_sync(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    def download_submission_for_task(task_id):
        log.info(
            f"Thread {threading.current_thread().name} - "
            f"Downloading submission for Task ID {task_id}"
        )
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
        file = xform.getSubmissionMedia(odkid, xml_form_id)
        file_path = f"{project_name}_{form_category}_submission_{task_id}.zip"
        with open(file_path, "wb") as f:
            f.write(file.content)
        return file_path

    def extract_files(zip_file_path):
        log.info(
            f"Thread {threading.current_thread().name} - "
            f"Extracting files from {zip_file_path}"
        )
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            extract_dir = os.path.splitext(zip_file_path)[0]
            zip_file.extractall(extract_dir)
            return [os.path.join(extract_dir, f) for f in zip_file.namelist()]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        task_list = [x.id for x in project_tasks]

        # Download submissions using thread pool
        futures = {
            executor.submit(download_submission_for_task, task_id): task_id
            for task_id in task_list
        }

        files = []
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            try:
                file_path = future.result()
                files.append(file_path)
                log.info(
                    f"Thread {threading.current_thread().name} -"
                    f" Task {task_id} - Download completed."
                )
            except Exception as e:
                log.error(
                    f"Thread {threading.current_thread().name} -"
                    f" Error occurred while downloading submission for task "
                    f"{task_id}: {e}"
                )

        # Extract files using thread pool
        extracted_files = []
        futures = {
            executor.submit(extract_files, file_path): file_path for file_path in files
        }
        for future in concurrent.futures.as_completed(futures):
            file_path = futures[future]
            try:
                extracted_files.extend(future.result())
                log.info(
                    f"Thread {threading.current_thread().name} -"
                    f" Extracted files from {file_path}"
                )
            except Exception as e:
                log.error(
                    f"Thread {threading.current_thread().name} -"
                    f" Error occurred while extracting files from {file_path}: {e}"
                )

    # Create a new ZIP file for the extracted files
    final_zip_file_path = f"{project_name}_{form_category}_submissions_final.zip"
    with zipfile.ZipFile(final_zip_file_path, mode="w") as final_zip_file:
        for file_path in extracted_files:
            final_zip_file.write(file_path)

    return final_zip_file_path


def update_submission_in_s3(
    db: Session, project_id: int, background_task_id: uuid.UUID
):
    """Update or create new submission JSON in S3 for a project."""
    try:
        # Get Project
        get_project_sync = async_to_sync(project_crud.get_project)
        project = get_project_sync(db, project_id)

        # Gather metadata
        odk_credentials = project_schemas.ODKCentral(
            odk_central_url=project.odk_central_url,
            odk_central_user=project.odk_central_user,
            odk_central_password=project.odk_central_password,
        )
        odk_forms = list_odk_xforms(project.odkid, odk_credentials, True)

        # Get latest submission date
        valid_datetimes = [
            form["lastSubmission"]
            for form in odk_forms
            if form["lastSubmission"] is not None
        ]
        last_submission = (
            max(
                valid_datetimes,
                key=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"),
            )
            if valid_datetimes
            else None
        )

        # Check if the file already exists in s3
        s3_project_path = f"/{project.organisation_id}/{project_id}"
        metadata_s3_path = f"/{s3_project_path}/submissions.meta.json"
        try:
            # Get the last submission date from the metadata
            file = get_obj_from_bucket(settings.S3_BUCKET_NAME, metadata_s3_path)
            zip_file_last_submission = (json.loads(file.getvalue()))["last_submission"]
            if last_submission <= zip_file_last_submission:
                # Update background task status to COMPLETED
                update_bg_task_sync = async_to_sync(
                    project_crud.update_background_task_status_in_database
                )
                update_bg_task_sync(db, background_task_id, 4)  # 4 is COMPLETED
                return

        except Exception as e:
            log.warning(str(e))
            pass

        # Zip file is outdated, regenerate
        metadata = {
            "last_submission": last_submission,
        }

        # Get submissions from ODK Central
        submissions = get_all_submissions_json(db, project_id)

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
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    project = get_odk_project(odk_credentials)

    get_task_id_list_sync = async_to_sync(tasks_crud.get_task_id_list)
    task_list = get_task_id_list_sync(db, project_id)
    submissions = project.getAllSubmissions(project_info.odkid, task_list)
    return submissions


# TODO delete me
# def get_project_submission(db: Session, project_id: int):
#     """Get."""
#     get_project_sync = async_to_sync(project_crud.get_project)
#     project_info = get_project_sync(db, project_id)

#     # Return empty list if project is not found
#     if not project_info:
#         raise HTTPException(status_code=404, detail="Project not found")

#     odkid = project_info.odkid
#     project_name = project_info.project_name_prefix
#     form_category = project_info.xform_title
#     project_tasks = project_info.tasks

#     # ODK Credentials
#     odk_credentials = project_schemas.ODKCentral(
#         odk_central_url=project_info.odk_central_url,
#         odk_central_user=project_info.odk_central_user,
#         odk_central_password=project_info.odk_central_password,
#     )

#     # Get ODK Form with odk credentials from the project.
#     xform = get_odk_form(odk_credentials)

#     submissions = []

#     task_list = [x.id for x in project_tasks]
#     for id in task_list:
#         xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
#         file = xform.getSubmissions(odkid, xml_form_id, None, False, True)
#         if not file:
#             json_data = None
#         else:
#             json_data = json.loads(file)
#             json_data_value = json_data.get("value")
#             if json_data_value:
#                 submissions.extend(json_data_value)

#     return submissions


async def download_submission(
    db: Session, project_id: int, task_id: int, export_json: bool
):
    """Download submission data from ODK Central and aggregate."""
    project_info = await project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)
    if not export_json:
        file_path = f"{project_id}_submissions.zip"

        # If task id is not provided, submission for all the task are listed
        if task_id is None:
            task_list = []

            task_list = [x.id for x in project_tasks]

            # # Create a new ZIP file for all submissions
            # zip_file_path = f"{project_name}_{form_category}_submissions.zip"
            files = []

            for id in task_list:
                # XML Form Id is a combination or project_name, category and task_id
                # FIXME: fix xml_form_id
                xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
                file = xform.getSubmissionMedia(odkid, xml_form_id)

                # Create a new output file for each submission
                file_path = f"{project_name}_{form_category}_submission_{id}.zip"
                with open(file_path, "wb") as f:
                    f.write(file.content)

                # Add the output file path to the list of files for the final ZIP file
                files.append(file_path)

            extracted_files = []
            for file_path in files:
                with zipfile.ZipFile(file_path, "r") as zip_file:
                    # Extract the contents of the nested ZIP files to a directory
                    # with the same name as the ZIP file
                    zip_file.extractall(os.path.splitext(file_path)[0])
                    extracted_files += [
                        os.path.join(os.path.splitext(file_path)[0], f)
                        for f in zip_file.namelist()
                    ]  # Add the extracted file paths to the list of extracted files

            # Create a new ZIP file for the extracted files
            final_zip_file_path = (
                f"{project_name}_{form_category}_submissions_final.zip"
            )
            with zipfile.ZipFile(final_zip_file_path, mode="w") as final_zip_file:
                for file_path in extracted_files:
                    final_zip_file.write(file_path)

            return FileResponse(final_zip_file_path)
        else:
            xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
            file = xform.getSubmissionMedia(odkid, xml_form_id)
            with open(file_path, "wb") as f:
                f.write(file.content)
            return FileResponse(file_path)
    else:
        headers = {
            "Content-Disposition": "attachment; filename=submission_data.json",
            "Content-Type": "application/json",
        }

        files = []

        if task_id is None:
            task_list = [x.id for x in project_tasks]
            for id in task_list:
                xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
                file = xform.getSubmissions(odkid, xml_form_id, None, False, True)
                if not file:
                    json_data = None
                else:
                    json_data = json.loads(file)
                    json_data_value = json_data.get("value")
                    if json_data_value:
                        files.extend(json_data_value)
        else:
            xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
            file = xform.getSubmissions(odkid, xml_form_id, None, False, True)
            json_data = json.loads(file)

        response_content = json.dumps(
            files if task_id is None else json_data, indent=4
        ).encode()

        return Response(content=response_content, headers=headers)


async def get_submission_points(db: Session, project_id: int, task_id: int = None):
    """Gets the submission points of project.

    If task_id is provided, it return point specific to a task,
    else the entire project.
    """
    project_info = await project_crud.get_project_by_id(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    xform = get_odk_form(odk_credentials)

    if task_id:
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[
            2
        ]  # FIXME: fix xml_form_id
        # file_path = f"{project_id}_submissions.zip"
        response_file = xform.getSubmissionMedia(odkid, xml_form_id)

        # Create a file-like object from the bytes object
        response_file_obj = io.BytesIO(response_file.content)
        try:
            # Open the zipfile
            with zipfile.ZipFile(response_file_obj, "r") as zip_ref:
                # Find the CSV file in the zipfile (assuming it has a .csv extension)
                csv_filename = [f for f in zip_ref.namelist() if f.endswith(".csv")][0]
                # Open the CSV file
                with zip_ref.open(csv_filename) as csv_file:
                    # Read the CSV data
                    csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
                    geometry = []
                    for row in csv_reader:
                        # Check if the row contains the 'warmup-Latitude' and
                        # 'warmup-Longitude' columns
                        # FIXME: fix the column names (they might not be same
                        # warmup-Latitude and warmup-Longitude)
                        if "warmup-Latitude" in row and "warmup-Longitude" in row:
                            point = (row["warmup-Latitude"], row["warmup-Longitude"])

                            # Create a GeoJSON Feature object
                            geometry.append(
                                {
                                    "type": "Feature",
                                    "geometry": {"type": "Point", "coordinates": point},
                                }
                            )
                            # points.append(point)
                return geometry
        except zipfile.BadZipFile:
            print("The file is not a valid zip file.")
            return None
    else:
        return None


async def get_submission_count_of_a_project(db: Session, project_id: int):
    """Return the total number of submissions made for a project."""
    project_info = await project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    files = []

    task_list = [x.id for x in project_tasks]
    for id in task_list:
        xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
        file = xform.getSubmissions(odkid, xml_form_id, None, False, True)
        if not file:
            json_data = None
        else:
            json_data = json.loads(file)
            json_data_value = json_data.get("value")
            if json_data_value:
                files.extend(json_data_value)

    return len(files)


async def get_submissions_by_date(
    db: Session, project_id: int, days: int, planned_task: int
):
    """Get submissions by date.

    Fetches the submissions for a given project within a specified number of days.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project.
        days (int): The number of days to consider for fetching submissions.
        planned_task (int): Associated task id.

    Returns:
        dict: A dictionary containing the submission counts for each date.

    Examples:
        # Fetch submissions for project with ID 1 within the last 7 days
        submissions = await get_submissions_by_date(db, 1, 7)
    """
    project = await project_crud.get_project(db, project_id)
    s3_project_path = f"/{project.organisation_id}/{project_id}"
    s3_submission_path = f"/{s3_project_path}/submission.zip"

    try:
        file = get_obj_from_bucket(settings.S3_BUCKET_NAME, s3_submission_path)
    except ValueError:
        return []

    with zipfile.ZipFile(file, "r") as zip_ref:
        with zip_ref.open("submissions.json") as file_in_zip:
            content = file_in_zip.read()

    content = json.loads(content)
    end_dates = [
        datetime.fromisoformat(entry["end"].split("+")[0])
        for entry in content
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


async def get_submission_by_project(project_id: int, skip: 0, limit: 100, db: Session):
    """Get submission by project.

    Retrieves a paginated list of submissions for a given project.

    Args:
        project_id (int): The ID of the project.
        skip (int): The number of submissions to skip.
        limit (int): The maximum number of submissions to retrieve.
        db (Session): The database session.

    Returns:
        Tuple[int, List]: A tuple containing the total number of submissions and
        the paginated list of submissions.

    Raises:
        ValueError: If the submission file cannot be found.

    """
    project = await project_crud.get_project(db, project_id)
    s3_project_path = f"/{project.organisation_id}/{project_id}"
    s3_submission_path = f"/{s3_project_path}/submission.zip"

    try:
        file = get_obj_from_bucket(settings.S3_BUCKET_NAME, s3_submission_path)
    except ValueError:
        return 0, []

    with zipfile.ZipFile(file, "r") as zip_ref:
        with zip_ref.open("submissions.json") as file_in_zip:
            content = file_in_zip.read()

    content = json.loads(content)
    start_index = skip
    end_index = skip + limit
    paginated_content = content[start_index:end_index]
    return len(content), paginated_content
