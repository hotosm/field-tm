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
"""Finalize a project on ODK Central: form, entity lists, manager user, files."""

import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from psycopg import AsyncConnection

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.config import settings
from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.errors import (
    ServiceError,
    ValidationError,
)
from app.projects import project_crud, project_schemas
from app.projects.task_sync import sync_odk_tasks, tasks_geometry_hash

log = logging.getLogger(__name__)


@dataclass(slots=True)
class ODKFinalizeResult:
    """Details returned after ODK finalization."""

    odk_url: str
    manager_username: str
    manager_password: str


def _resolve_odk_public_url(custom_odk_creds: Optional[ODKCentral]) -> str:
    """Resolve public ODK base URL used for UI links and persisted instance URL."""
    if custom_odk_creds and custom_odk_creds.external_project_instance_url:
        return custom_odk_creds.external_project_instance_url.rstrip("/")
    return str(
        settings.ODK_CENTRAL_PUBLIC_URL or settings.ODK_CENTRAL_URL or ""
    ).rstrip("/")


def _validate_odk_finalization_prereqs(
    project: DbProject,
    custom_odk_creds: Optional[ODKCentral],
) -> None:
    """Validate the project state and ODK credentials before finalization."""
    if not project.xlsform_content:
        raise ValidationError("XLSForm is required. Please upload a form first.")
    if project.data_extract_geojson is None:
        raise ValidationError(
            "Data extract is required. "
            "Please download OSM data or upload GeoJSON first."
        )
    if not custom_odk_creds and (
        not settings.ODK_CENTRAL_URL or not settings.ODK_CENTRAL_USER
    ):
        raise ValidationError(
            "ODK Central credentials are not configured on the server. "
            "Please provide custom ODK credentials."
        )


async def _ensure_odk_project(
    db: AsyncConnection,
    project_id: int,
    project: DbProject,
    custom_odk_creds: Optional[ODKCentral],
) -> int:
    """Create the downstream ODK project if it does not already exist."""
    if project.external_project_id:
        return project.external_project_id

    log.info(f"Creating ODK project for Field-TM project {project_id}")
    odk_project = await central_crud.create_odk_project(
        project.project_name,
        custom_odk_creds,
    )
    project_odk_id = odk_project["id"]
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(external_project_id=project_odk_id),
    )
    await db.commit()
    log.info(f"Created ODK project {project_odk_id} for Field-TM project {project_id}")
    return project_odk_id


async def _persist_project_odk_details(
    db: AsyncConnection,
    project_id: int,
    project: DbProject,
    project_odk_id: int,
    custom_odk_creds: Optional[ODKCentral],
) -> None:
    """Persist the ODK connection details used for this project."""
    odk_instance_url = _resolve_odk_public_url(custom_odk_creds)
    should_update_odk_details = False
    update_payload = project_schemas.ProjectUpdate(external_project_id=project_odk_id)

    if odk_instance_url and odk_instance_url != (
        project.external_project_instance_url or ""
    ):
        update_payload.external_project_instance_url = odk_instance_url
        should_update_odk_details = True

    if custom_odk_creds:
        if custom_odk_creds.external_project_username:
            update_payload.external_project_username = (
                custom_odk_creds.external_project_username
            )
            should_update_odk_details = True
        if custom_odk_creds.external_project_password:
            update_payload.external_project_password = (
                custom_odk_creds.external_project_password
            )
            should_update_odk_details = True

    if not should_update_odk_details:
        return

    await DbProject.update(db, project_id, update_payload)
    await db.commit()


def _apply_default_entity_style(entities_list: list[dict]) -> None:
    """Ensure generated entities include the default map style fields."""
    default_style = {
        "fill": "#1a1a1a",
        "marker-color": "#1a1a1a",
        "stroke": "#000000",
        "stroke-width": "6",
    }
    for entity in entities_list:
        data = entity["data"]
        for key, value in default_style.items():
            data.setdefault(key, value)


async def _build_feature_dataset_payload(
    project_id: int, project: DbProject
) -> tuple[list[str], list[dict]]:
    """Build the `features` dataset property list and entities."""
    geojson_data = project.data_extract_geojson or {}
    features = (
        geojson_data.get("features", []) if isinstance(geojson_data, dict) else []
    )
    if not features:
        log.info(
            "No existing features supplied for project %s. "
            "Creating empty 'features' dataset for collect-new-data workflow.",
            project_id,
        )
        return [], []

    entity_properties = list(features[0].get("properties", {}).keys())
    for field in ["created_by", "fill", "marker-color", "stroke", "stroke-width"]:
        if field not in entity_properties:
            entity_properties.append(field)

    entities_list = await central_crud.task_geojson_dict_to_entity_values(
        geojson_data, additional_features=True
    )
    _apply_default_entity_style(entities_list)
    return entity_properties, entities_list


async def _create_manager_credentials(
    project_odk_id: int,
    project_name: str,
    custom_odk_creds: Optional[ODKCentral],
) -> tuple[str, str]:
    """Create the project-scoped ODK Central manager account."""
    try:
        return await central_crud.create_project_manager_user(
            project_odk_id=project_odk_id,
            project_name=project_name,
            odk_credentials=custom_odk_creds,
        )
    except Exception as e:
        manager_error = getattr(e, "detail", str(e))
        raise ServiceError(
            f"Failed to create ODK Central manager user. {manager_error}"
        ) from e


async def _generate_project_files(
    db: AsyncConnection,
    project_id: int,
    custom_odk_creds: Optional[ODKCentral],
) -> bool:
    """Generate project files, tolerating legacy patched call signatures in tests."""
    try:
        return await project_crud.generate_project_files(
            db,
            project_id,
            odk_credentials=custom_odk_creds,
        )
    except TypeError as e:
        if "unexpected keyword argument 'odk_credentials'" not in str(e):
            raise
        return await project_crud.generate_project_files(db, project_id)


async def finalize_odk_project(
    db: AsyncConnection,
    project_id: int,
    custom_odk_creds: Optional[ODKCentral] = None,
) -> ODKFinalizeResult:
    """Publish to ODK Central and return its URL and manager credentials.

    custom_odk_creds=None uses deployment credentials. Raises ValidationError
    for missing prerequisites or ServiceError if creation fails.
    """
    project = await DbProject.one(db, project_id)

    _validate_odk_finalization_prereqs(project, custom_odk_creds)
    project_odk_id = await _ensure_odk_project(
        db,
        project_id,
        project,
        custom_odk_creds,
    )
    await _persist_project_odk_details(
        db,
        project_id,
        project,
        project_odk_id,
        custom_odk_creds,
    )

    entity_properties, entities_list = await _build_feature_dataset_payload(
        project_id,
        project,
    )

    log.info(f"Creating entity list 'features' for ODK project {project_odk_id}")
    await central_crud.create_entity_list(
        custom_odk_creds,
        project_odk_id,
        properties=entity_properties,
        dataset_name="features",
        entities_list=entities_list,
    )

    await sync_odk_tasks(project, custom_odk_creds, project_odk_id)

    xlsform_bytes = BytesIO(project.xlsform_content)
    xform = await central_crud.read_and_test_xform(xlsform_bytes)
    log.info(f"Uploading XLSForm to ODK project {project_odk_id}")
    await central_crud.create_odk_xform(
        project_odk_id,
        xform,
        custom_odk_creds,
    )

    log.info(f"Generating project files for project {project_id}")
    success = await _generate_project_files(db, project_id, custom_odk_creds)

    if not success:
        raise ServiceError("Failed to generate project files. Please contact support.")

    odk_url = f"{_resolve_odk_public_url(custom_odk_creds)}/#/projects/{project_odk_id}"
    manager_username, manager_password = await _create_manager_credentials(
        project_odk_id,
        project.project_name or f"Project {project_id}",
        custom_odk_creds,
    )

    # Update project status to PUBLISHED only after manager account exists.
    await DbProject.update(
        db,
        project_id,
        project_schemas.ProjectUpdate(
            status=ProjectStatus.PUBLISHED,
            tasks_synced_hash=tasks_geometry_hash(project),
        ),
    )
    await db.commit()

    return ODKFinalizeResult(
        odk_url=odk_url,
        manager_username=manager_username,
        manager_password=manager_password,
    )
