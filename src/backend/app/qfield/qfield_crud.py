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
import logging
import shutil
from io import BytesIO
from pathlib import Path
from random import getrandbits
from uuid import uuid4

from aiohttp import ClientSession
from fastapi.exceptions import HTTPException
from osm_fieldwork.update_xlsform import modify_form_for_qfield
from psycopg import Connection
from qfieldcloud_sdk.sdk import FileTransferType

from app.config import settings
from app.db.enums import HTTPStatus
from app.db.models import DbProject
from app.projects.project_crud import get_project_features_geojson, get_task_geometry
from app.qfield.qfield_deps import qfield_client

log = logging.getLogger(__name__)

# Configuration
CONTAINER_IMAGE = "ghcr.io/opengisch/qfieldcloud-qgis:25.24"
SHARED_VOLUME_NAME = "qfield_projects"  # docker/nerdctl volume name
SHARED_VOLUME_PATH = "/opt/qfield"  # inside the container


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

    # Write files locally for QGIS job
    xlsform_path = job_dir / "xlsform.xlsx"
    with open(xlsform_path, "wb") as f:
        f.write(final_form.getvalue())

    features_geojson_path = job_dir / "features.geojson"
    with open(features_geojson_path, "w") as f:
        json.dump(features_geojson, f)

    tasks_geojson_path = job_dir / "tasks.geojson"
    with open(tasks_geojson_path, "w") as f:
        json.dump(json.loads(tasks_geojson), f)

    # TODO ensure xlsform has geometry field, if not add in

    # 1. Create QGIS project via internal API
    qgis_container_url = "http://qfield-qgis:8080"
    project_name = f"field-tm-{project.name}-{getrandbits(32)}"
    log.info(f"Creating QGIS project via API: {qgis_container_url}")
    async with ClientSession() as http_client:
        response = await http_client.post(
            f"{qgis_container_url}/",
            json={
                "project_dir": str(job_dir),
                "title": project_name,
                "language": form_language,
                "extent": bbox_str,
            },
        )

        if response.status_code != 200:
            msg = f"QGIS API request failed: {response.text}"
            log.error(msg)
            shutil.rmtree(job_dir)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        result = response.json()
        if result.get("status") != "success":
            msg = f"Failed to generate QGIS project: {result.get('message')}"
            log.error(msg)
            shutil.rmtree(job_dir)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=msg,
            )

    # Ensure output file exists
    final_project_file = Path(
        f"{SHARED_VOLUME_PATH}/{qgis_job_id}/final/{project_name}.qgz"
    )
    if not final_project_file.exists():
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="QGIS job completed but output file was not created",
        )

    # 2. Create QFieldCloud project
    async with qfield_client() as client:
        qfield_project = client.create_project(
            project_name,
            owner="admin",  # FIXME
            description=project.description,
            is_public=True,
        )

        # 3. Upload generated files from shared volume
        qfield_project_id = qfield_project.get("id")
        qfield_project_owner = qfield_project.get("owner")
        qfield_project_name = qfield_project.get("name")

        try:
            upload_info = client.upload_files(
                project_id=qfield_project_id,
                upload_type=FileTransferType.PROJECT,
                project_path=str(final_project_file.parent),
                filter_glob="*",
                throw_on_error=True,
                force=True,
            )
            log.debug(f"File upload complete: {upload_info}")
        except Exception as e:
            log.warning(
                f"File upload failed, deleting QFieldCloud project {qfield_project_id}"
            )
            # Delete the project if upload fails
            client.delete_project(qfield_project_id)
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=(f"Failed to upload files to project {qfield_project_id}: {e}"),
            ) from e

    return (
        f"{settings.QFIELDCLOUD_URL.split('/api/v1/')[0]}"
        f"/a/{qfield_project_owner}/{qfield_project_name}"
    )
