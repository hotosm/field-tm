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
"""Logic for interaction with QFieldCloud & data."""

import json
import shutil
from io import BytesIO
from pathlib import Path
from random import getrandbits
from uuid import uuid4

import geojson
from aiohttp import ClientSession
from fastapi.exceptions import HTTPException
from loguru import logger as log
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import Connection
from qfieldcloud_sdk.sdk import FileTransferType

from app.config import settings
from app.db.enums import FieldMappingApp, HTTPStatus
from app.db.models import DbProject, DbProjectExternalURL
from app.projects.project_crud import get_project_features_geojson, get_task_geometry
from app.projects.project_schemas import ProjectUpdate
from app.qfield.qfield_deps import qfield_client
from app.qfield.qfield_schemas import QFieldCloud

# Configuration
CONTAINER_IMAGE = "ghcr.io/opengisch/qfieldcloud-qgis:25.24"
SHARED_VOLUME_NAME = "qfield_projects"  # docker/nerdctl volume name
SHARED_VOLUME_PATH = "/opt/qfield"  # inside the container


def clean_tags_for_qgis(
    geojson_data: geojson.FeatureCollection,
) -> geojson.FeatureCollection:
    """Clean tags field in GeoJSON to be compatible with QGIS.

    QGIS has issues with JSON string tags like '{"building": "yes"}', so we convert
    them to a format that QGIS can handle.

    Args:
        geojson_data: GeoJSON FeatureCollection to clean

    Returns:
        Cleaned GeoJSON FeatureCollection
    """
    if not geojson_data or "features" not in geojson_data:
        return geojson_data

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        tags = properties.get("tags")

        if tags:
            if isinstance(tags, str) and tags.startswith("{") and tags.endswith("}"):
                try:
                    tags_dict = json.loads(tags)
                    if isinstance(tags_dict, dict):
                        # Convert to "key=value;key2=value2" format
                        tags_str = ";".join([f"{k}={v}" for k, v in tags_dict.items()])
                        properties["tags"] = tags_str
                    else:
                        # If it's not a dict, keep as string
                        properties["tags"] = str(tags)
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, keep as string
                    properties["tags"] = str(tags)
            else:
                properties["tags"] = str(tags) if tags else ""
        else:
            properties["tags"] = ""

        feature["properties"] = properties

    return geojson_data


async def create_qfield_project(
    db: Connection,
    project: DbProject,
):
    """Create QField project in QFieldCloud via QGIS job API."""
    qgis_job_id = str(uuid4())
    job_dir = Path(SHARED_VOLUME_PATH) / qgis_job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Get XLSForm and features geojson from project
    bbox_str = ",".join(map(str, project.bbox))

    # NOTE xlsform_content is the already processed ODK-ready form,
    # NOTE so we modify this as needed
    form_language, final_form = await modify_form_for_qfield(
        BytesIO(project.xlsform_content),
        geom_layer_type=project.primary_geom_type,
    )
    features_geojson = await get_project_features_geojson(db, project)
    tasks_geojson = await get_task_geometry(db, project.id)

    # Clean up tags field for QGIS compatibility
    features_geojson = clean_tags_for_qgis(features_geojson)

    # Write updated XLSForm content to db (for latest inspection)
    xlsform_bytes = final_form.getvalue()
    if len(xlsform_bytes) == 0:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="There was an error modifying the XLSForm!",
        )
    log.debug(f"Setting project XLSForm db data for project ({project.id})")
    await DbProject.update(
        db,
        project.id,
        ProjectUpdate(
            xlsform_content=xlsform_bytes,
        ),
    )
    await db.commit()

    # Write files locally for QGIS job
    xlsform_path = job_dir / "xlsform.xlsx"
    with open(xlsform_path, "wb") as f:
        f.write(xlsform_bytes)

    features_geojson_path = job_dir / "features.geojson"
    with open(features_geojson_path, "w") as f:
        json.dump(features_geojson, f)

    tasks_geojson_path = job_dir / "tasks.geojson"
    tasks_geojson_parsed = json.loads(tasks_geojson)
    tasks_geojson_cleaned = clean_tags_for_qgis(tasks_geojson_parsed)
    with open(tasks_geojson_path, "w") as f:
        json.dump(tasks_geojson_cleaned, f)

    # 1. Create QGIS project via internal API
    qgis_container_url = "http://qfield-qgis:8080"
    # Here we need the name without spaces for the final .qgz filename
    qgis_project_name = project.slug
    qfc_project_name = f"FieldTM-{qgis_project_name}-{getrandbits(32)}"
    log.info(f"Creating QGIS project via API: {qgis_container_url}")

    async with ClientSession() as http_client:
        async with http_client.post(
            f"{qgis_container_url}/",
            json={
                "project_dir": str(job_dir),
                "title": qgis_project_name,
                "language": form_language,
                "extent": bbox_str,
            },
        ) as response:
            if response.status != 200:
                msg = f"QGIS API request failed: {await response.text()}"
                log.error(msg)
                shutil.rmtree(job_dir)
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=msg,
                )

            result = await response.json()
            if result.get("status") != "success":
                msg = f"Failed to generate QGIS project: {result.get('message')}"
                log.error(msg)
                shutil.rmtree(job_dir)
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=msg,
                )
    log.debug("Successfully created QGIS project via API")

    # Ensure output file exists (directory generated by project_gen_svc.py)
    final_project_file = Path(
        f"{SHARED_VOLUME_PATH}/{qgis_job_id}/final/{qgis_project_name}.qgz"
    )
    print(f'\n---- final_project_file: "{final_project_file}"----\n')
    if not final_project_file.exists():
        msg = (
            f"QGIS job completed but output file was not created: {final_project_file}"
        )
        log.error(msg)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=msg,
        )

    # 2. Create QFieldCloud project
    # TODO: Find solution to create organization before creating project.
    # This will be handled while decoupling backend.
    # IF organization is not given then it will use default username as owner.
    log.debug(f"Creating QFieldCloud project: {qfc_project_name}")
    async with qfield_client() as client:
        qfield_project = client.create_project(
            qfc_project_name,
            owner=settings.DEFAULT_ORG_NAME,
            description="Created by the Field Tasking Manager",
            is_public=True,
        )
        log.debug(f"Successfully created QFieldCloud project: {qfield_project}")
        # 3. Upload generated files from shared volume
        api_project_id = qfield_project.get("id")
        api_project_owner = qfield_project.get("owner")
        api_project_name = qfield_project.get("name")

        try:
            log.debug(f"Uploading files to QFieldCloud project: {api_project_name}")
            upload_info = client.upload_files(
                project_id=api_project_id,
                upload_type=FileTransferType.PROJECT,
                project_path=str(final_project_file.parent),
                filter_glob="*",
                throw_on_error=True,
                force=True,
            )
            log.debug(f"File upload complete: {upload_info}")
        except Exception as e:
            log.warning(
                f"File upload failed, deleting QFieldCloud project {api_project_id}"
            )
            # Delete the project if upload fails
            client.delete_project(api_project_id)
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=(f"Failed to upload files to project {api_project_id}: {e}"),
            ) from e

    log.info("Finished QFieldCloud project upload")
    # Create QField URL
    qfield_url = (
        f"http://qfield.{settings.FMTM_DOMAIN}:{settings.FMTM_DEV_PORT}"
        f"/a/{api_project_owner}/{api_project_name}"
        if settings.DEBUG
        else f"{settings.QFIELDCLOUD_URL.split('/api/v1/')[0]}"
        f"/a/{api_project_owner}/{api_project_name}"
    )

    # Store QField URL in project_external_urls
    await DbProjectExternalURL.create_or_update(
        db=db,
        project_id=project.id,
        source=FieldMappingApp.QFIELD,
        url=qfield_url,
        qfield_project_id=api_project_id,
    )
    await db.commit()

    return qfield_url


async def qfc_credentials_test(qfc_creds: QFieldCloud):
    """Test QFieldCloud credentials by attempting to open a session.

    Returns status 200 if credentials are valid, otherwise raises HTTPException.
    """
    try:
        creds = QFieldCloud(
            qfield_cloud_url=qfc_creds.qfield_cloud_url,
            qfield_cloud_user=qfc_creds.qfield_cloud_user,
            qfield_cloud_password=qfc_creds.qfield_cloud_password,
        )
        async with qfield_client(creds):
            pass
        return HTTPStatus.OK
    except Exception as e:
        msg = f"QFieldCloud credential test failed: {str(e)}"
        log.debug(msg)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="QFieldCloud credentials are invalid.",
        ) from e


async def delete_qfield_project(db: Connection, project_id: int):
    """Delete a project from QFieldCloud using the stored `qfield_project_id`."""
    # Fetch external URL record using model helper
    try:
        ext = await DbProjectExternalURL.one(db, project_id)
    except KeyError as e:
        raise ValueError(
            f"No external project URL found for project ID {project_id}"
        ) from e

    qfield_project_id = ext.qfield_project_id
    if not qfield_project_id:
        raise ValueError(f"No QField project id set for project ID {project_id}")

    # Now, delete the project from QFieldCloud
    async with qfield_client() as client:
        client.delete_project(qfield_project_id)

    return f"Project {project_id} deleted from QFieldCloud."
