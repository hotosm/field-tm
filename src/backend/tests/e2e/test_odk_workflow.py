"""ODK workflow end to end: create, publish, map in "Collect", export.

Runs against the real ODK Central in compose.test.yaml. The device side is
HeadlessCollect, which makes the same OpenRosa requests as ODK Collect.
"""

import asyncio
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import jsonschema
import pytest_asyncio
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import buildings

from app.central import central_deps
from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.projects import project_crud, project_services
from app.projects.data_extract_services import save_data_extract
from app.projects.odk_services import finalize_odk_project
from tests.e2e.odk_collect import HeadlessCollect, new_instance, settings_from_qr

WEST, MIDDLE, EAST = 85.299989110, 85.3024, 85.304783157
SOUTH, NORTH = 27.7108923499, 27.7140080437
MAPPER = "e2e-mapper"
ENTITY_UPDATE_TIMEOUT_S = 60
# Collect validates scanned QR settings with this schema, vendored from
# getodk/collect settings/src/main/resources/. Refresh when Collect adds settings.
COLLECT_SETTINGS_SCHEMA = json.loads(
    (Path(__file__).parent / "collect_settings.schema.json").read_text()
)


def _box(west: float, south: float, east: float, north: float) -> dict:
    ring = [[west, north], [west, south], [east, south], [east, north]]
    return {"type": "Polygon", "coordinates": [[*ring, ring[0]]]}


def _building(osm_id: int, lon: float, lat: float) -> dict:
    size = 0.00005
    return {
        "type": "Feature",
        "geometry": _box(lon - size, lat - size, lon + size, lat + size),
        "properties": {"osm_id": osm_id, "building": "yes"},
    }


OUTLINE = _box(WEST, SOUTH, EAST, NORTH)
TASK_AREAS = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": _box(WEST, SOUTH, MIDDLE, NORTH)},
        {"type": "Feature", "geometry": _box(MIDDLE, SOUTH, EAST, NORTH)},
    ],
}
BUILDINGS = {
    "type": "FeatureCollection",
    "features": [
        _building(101, 85.3010, 27.7120),
        _building(102, 85.3015, 27.7130),
        _building(103, 85.3035, 27.7125),
    ],
}


@pytest_asyncio.fixture
async def published_project(db, admin_user):
    """A buildings project published to ODK Central, deleted afterwards."""
    project = await project_services.create_project_stub(
        db,
        project_name=f"e2e odk {uuid4().hex[:8]}",
        field_mapping_app=FieldMappingApp.ODK,
        description="End-to-end test project",
        outline=OUTLINE,
        hashtags=["e2e"],
        user_sub=admin_user.sub,
    )
    await db.commit()
    await project_services.process_xlsform(
        db,
        project.id,
        BytesIO(convert_to_xlsform(str(buildings))),
        use_odk_collect=True,
    )
    await save_data_extract(db, project.id, BUILDINGS)
    await project_services.save_task_areas(db, project.id, TASK_AREAS)
    await finalize_odk_project(db, project.id)

    yield await DbProject.one(db, project.id)

    await project_services.delete_project_with_downstream(db, project.id)
    await db.commit()


async def _wait_for_entity_update(odk_project_id: int, entity_id: str) -> dict:
    """Poll until Central has applied the submission to the feature entity."""
    path = f"projects/{odk_project_id}/datasets/features/entities/{entity_id}"
    async with central_deps.pyodk_client(None) as client:
        for _ in range(ENTITY_UPDATE_TIMEOUT_S):
            response = client.session.get(path)
            response.raise_for_status()
            current = response.json()["currentVersion"]
            if current["version"] > 1:
                return current
            await asyncio.sleep(1)
    raise AssertionError(f"Entity {entity_id} not updated: {current}")


def _rejecting_unknown_keys(schema: dict) -> dict:
    """Collect ignores keys it does not know, so a typo would fail silently."""
    sections = {
        name: {**section, "additionalProperties": False}
        for name, section in schema["properties"].items()
    }
    return {**schema, "properties": sections, "additionalProperties": False}


async def test_qr_code_settings_import_into_collect(db, published_project):
    """The QR code holds valid Collect settings for this project and mapper."""
    qr_data = await project_crud.get_project_qr_data(
        db, published_project.id, username=MAPPER
    )
    collect_settings = settings_from_qr(qr_data)

    jsonschema.validate(
        collect_settings, _rejecting_unknown_keys(COLLECT_SETTINGS_SCHEMA)
    )
    general = collect_settings["general"]
    server_url = general["server_url"]
    assert server_url.startswith(
        f"{published_project.external_project_instance_url}/v1/key/"
    )
    assert server_url.endswith(f"/projects/{published_project.external_project_id}")
    assert general["metadata_username"] == MAPPER
    assert collect_settings["project"]["name"] == published_project.project_name


async def test_mapper_submission_updates_entity_and_export(db, published_project):
    """A mapper surveys one building, and Field-TM sees it in Central and export."""
    qr_data = await project_crud.get_project_qr_data(
        db, published_project.id, username=MAPPER
    )
    collect = HeadlessCollect(settings_from_qr(qr_data)["general"]["server_url"])
    form = await collect.download_form()

    tasks = form.entity_lists["tasks.csv"]
    features = form.entity_lists["features.csv"]
    assert len(tasks) == len(TASK_AREAS["features"])
    assert len(features) == len(BUILDINGS["features"])
    assert {f["task_id"] for f in features} == {t["task_id"] for t in tasks}

    feature = next(f for f in features if f["osm_id"] == "103")
    task = next(t for t in tasks if t["task_id"] == feature["task_id"])
    instance = new_instance(
        form,
        {
            "username": MAPPER,
            "mapping_mode": "existing",
            "task": task["name"],
            "selected_task_id": task["task_id"],
            "feature": feature["name"],
            "xid": feature["osm_id"],
            "xlocation": feature["geometry"],
            "task_id": feature["task_id"],
            "created_by": "svcftm",
            "feature_exists": "yes",
            "survey_questions/buildings/category": "housing",
            "verification/digitisation_correct": "yes",
            "meta/entity/label": f"✅ Task {task['task_id']} Feature 103",
        },
    )
    instance.find("meta/entity").attrib.update(
        id=feature["name"],
        update="1",
        create="0",
        baseVersion=feature["__version"],
    )
    await collect.submit(instance)

    entity = await _wait_for_entity_update(
        published_project.external_project_id, feature["name"]
    )
    assert entity["data"]["status"] == "mapped"

    export = await project_services.export_project_geojson(db, published_project)
    [exported] = export["features"]
    assert exported["geometry"]["type"] == "Polygon"
    assert exported["properties"]["osm_id"] == 103
    assert exported["properties"]["task_id"] == int(feature["task_id"])
    assert exported["properties"]["status"] == "mapped"
    assert exported["properties"]["username"] == MAPPER
    assert exported["properties"]["category"] == "housing"
