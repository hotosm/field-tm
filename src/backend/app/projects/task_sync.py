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
"""Sync a project's task plan to its mapping app (ODK entities or QField)."""

import hashlib
import json
import logging
from typing import Optional

from psycopg import AsyncConnection

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.errors import ValidationError
from app.helpers.geometry_utils import stamp_missing_task_ids
from app.i18n import _
from app.projects import project_schemas
from app.qfield.qfield_crud import resync_qfield_tasks

log = logging.getLogger(__name__)


def _first_outline_feature(outline: Optional[dict]) -> Optional[dict]:
    """Normalize a project outline to a single GeoJSON Feature."""
    if not outline or not isinstance(outline, dict):
        return None

    outline_type = str(outline.get("type", "")).strip()
    if outline_type == "FeatureCollection":
        features = outline.get("features", [])
        if isinstance(features, list) and features:
            first_feature = features[0]
            if isinstance(first_feature, dict):
                return first_feature
        return None

    if outline_type == "Feature":
        return outline

    # Stored project outlines are typically geometry objects from PostGIS.
    if "coordinates" in outline:
        return {"type": "Feature", "geometry": outline, "properties": {}}

    return None


TASK_ENTITY_PROPERTIES = [
    "geometry",
    "task_id",
    "status",
    "assigned_group",
    "assigned_to",
    "comment",
    "colour",
    "fill",
    "stroke",
    "stroke-width",
]


def _task_entity_style(entity_dict: dict, properties: dict) -> dict:
    """Build a task entity from a task plan feature's properties."""
    task_id = properties["task_id"]
    colour = properties.get("colour") or "#3388ff"
    entity_dict["label"] = f"Task {task_id}"
    entity_dict["data"] = {
        "geometry": entity_dict["data"]["geometry"],
        "task_id": str(task_id),
        "status": "ready",
        "assigned_group": properties.get("assigned_group") or "",
        "assigned_to": properties.get("assigned_to") or "",
        "comment": properties.get("comment") or "",
        "colour": properties.get("colour") or "",
        "fill": f"{colour}33",
        "stroke": colour,
        "stroke-width": "3",
    }
    return entity_dict


async def _build_task_entities(project: DbProject) -> list[dict]:
    """Build the `tasks` dataset entities, creating a fallback task if needed."""
    task_entities = []
    task_areas = project.task_areas_geojson

    if task_areas and task_areas.get("features"):
        log.info(
            f"Uploading {len(task_areas.get('features', []))} task boundaries to ODK"
        )
        # Backfill legacy task IDs using the same helper as QField exports.
        stamp_missing_task_ids(task_areas)
        for feature in task_areas.get("features", []):
            if not feature.get("geometry"):
                continue
            entity_dict = await central_crud.feature_geojson_to_entity_dict(
                feature,
                additional_features=True,
            )
            task_entities.append(_task_entity_style(entity_dict, feature["properties"]))

    if task_entities:
        return task_entities

    log.info("No task areas found, creating single task entity from project outline")
    outline_feature = _first_outline_feature(project.outline)
    if not (outline_feature and outline_feature.get("geometry")):
        raise ValidationError(
            "Project outline is missing or invalid. "
            "Cannot create fallback task for ODK finalization."
        )

    entity_dict = await central_crud.feature_geojson_to_entity_dict(
        outline_feature,
        additional_features=True,
    )
    return [_task_entity_style(entity_dict, {"task_id": 1})]


def tasks_geometry_hash(project: DbProject) -> str:
    """Hash task ids and geometries, to tell area edits from assignment edits."""
    task_areas = project.task_areas_geojson or {}
    stamp_missing_task_ids(task_areas)
    parts = sorted(
        json.dumps([f["properties"].get("task_id"), f.get("geometry")], sort_keys=True)
        for f in task_areas.get("features") or []
    )
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def tasks_geometry_changed(project: DbProject) -> bool:
    """Whether task areas changed since the last sync (unknown counts as changed)."""
    return project.tasks_synced_hash != tasks_geometry_hash(project)


async def sync_odk_tasks(
    project: DbProject,
    odk_creds: Optional[ODKCentral],
    project_odk_id: int,
    reset: bool = False,
) -> None:
    """Create or update the ODK `tasks` entity list from the task plan.

    Tasks removed from the plan are deleted. Updates keep each entity's
    `status`, which mappers change in the field, unless `reset` is set.
    """
    await central_crud.create_entity_list(
        odk_creds,
        project_odk_id,
        properties=TASK_ENTITY_PROPERTIES,
        dataset_name="tasks",
        entities_list=await _build_task_entities(project),
        keep_existing=frozenset() if reset else frozenset({"status"}),
        delete_missing=True,
    )


async def resync_tasks(
    db: AsyncConnection, project: DbProject, reset_confirmed: bool
) -> None:
    """Push the task plan to a published ODK or QField project.

    If task areas changed, the app's task progress is reset, so the caller
    must confirm it.
    """
    changed = tasks_geometry_changed(project)
    if changed and not reset_confirmed:
        raise ValidationError(
            _("Task areas changed. Confirm the reset to re-sync the tasks.")
        )

    if project.field_mapping_app == FieldMappingApp.ODK:
        await sync_odk_tasks(
            project,
            project.get_odk_credentials(),
            project.external_project_id,
            reset=changed,
        )
    else:
        await resync_qfield_tasks(db, project)

    await DbProject.update(
        db,
        project.id,
        project_schemas.ProjectUpdate(tasks_synced_hash=tasks_geometry_hash(project)),
    )
    await db.commit()
