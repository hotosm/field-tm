"""Tests for the task assignment HTMX routes."""

import json
from unittest.mock import Mock

from litestar import Router
from litestar import status_codes as status

from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.htmx.assignment import assignment_routes
from app.htmx.assignment.assignment_routes import (
    assignment_geojson,
    assignment_panel_htmx,
    save_assignments_htmx,
)

# Two small task polygons inside the Kathmandu test outline. task_id is
# pre-stamped (save_task_areas would normally do this on accept-split).
_TASK_AREAS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.3000, 27.7110],
                        [85.3000, 27.7125],
                        [85.3020, 27.7125],
                        [85.3020, 27.7110],
                        [85.3000, 27.7110],
                    ]
                ],
            },
            "properties": {"task_id": 1, "building_count": 12},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.3020, 27.7110],
                        [85.3020, 27.7125],
                        [85.3040, 27.7125],
                        [85.3040, 27.7110],
                        [85.3020, 27.7110],
                    ]
                ],
            },
            "properties": {"task_id": 2},
        },
    ],
}


async def _set_task_areas(db, project_id, task_areas):
    """Persist task areas (or the {} no-split sentinel) on the project."""
    await DbProject.update(
        db,
        project_id,
        DbProject(task_areas_geojson=task_areas),
    )
    await db.commit()


def test_assignment_routes_are_registered():
    """All assignment handlers must be exported to the router."""
    assert assignment_panel_htmx in assignment_routes.ROUTE_HANDLERS
    assert assignment_geojson in assignment_routes.ROUTE_HANDLERS
    assert save_assignments_htmx in assignment_routes.ROUTE_HANDLERS


def test_assignment_routes_register_with_litestar():
    """Assignment route exports must be decorated route handlers."""
    Router(path="/", route_handlers=assignment_routes.ROUTE_HANDLERS)


async def test_assignment_panel_renders_map_and_summary(client, db, project):
    """The panel fragment should include the map slot, save form and table."""
    task_areas = json.loads(json.dumps(_TASK_AREAS))
    task_areas["features"][0]["properties"]["assigned_to"] = "alice"
    task_areas["features"][0]["properties"]["assigned_group"] = "NE"
    await _set_task_areas(db, project.id, task_areas)

    response = await client.get(
        f"/projects/{project.id}/assignments-htmx",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'id="assignment-map"' in response.text
    assert 'id="assignment-save-form"' in response.text
    assert f'hx-post="/projects/{project.id}/assignments"' in response.text
    assert 'name="assignments"' in response.text
    assert "Save assignments" in response.text
    assert "alice" in response.text
    assert "NE" in response.text
    assert "Unassigned" in response.text
    assert "/static/js/task_assignment.js" in response.text


async def test_assignment_panel_shows_no_split_callout(client, db, project):
    """The {} no-split sentinel should render an explanatory callout."""
    await _set_task_areas(db, project.id, {})

    response = await client.get(
        f"/projects/{project.id}/assignments-htmx",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "single task covering the whole area" in response.text
    assert 'id="assignment-map"' not in response.text


async def test_assignment_panel_escapes_user_supplied_assignee(client, db, project):
    """Summary table must autoescape free-text assignee values."""
    task_areas = json.loads(json.dumps(_TASK_AREAS))
    task_areas["features"][0]["properties"]["assigned_to"] = "<script>boom</script>"
    await _set_task_areas(db, project.id, task_areas)

    response = await client.get(
        f"/projects/{project.id}/assignments-htmx",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "<script>boom</script>" not in response.text
    assert "&lt;script&gt;boom&lt;/script&gt;" in response.text


async def test_assignment_panel_requires_project_context():
    """The panel should return 404 when the project context is missing."""
    response = await assignment_panel_htmx.fn(
        request=Mock(),
        current_user={"project": None},
        auth_user=Mock(),
        project_id=123,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_assignment_geojson_merges_assignment_properties(client, db, project):
    """The geojson endpoint should return stored features with defaults merged."""
    task_areas = json.loads(json.dumps(_TASK_AREAS))
    task_areas["features"][0]["properties"]["assigned_to"] = "alice"
    await _set_task_areas(db, project.id, task_areas)

    response = await client.get(f"/projects/{project.id}/assignments/geojson")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("application/geo+json")
    feature_collection = response.json()
    assert feature_collection["type"] == "FeatureCollection"
    features = feature_collection["features"]
    assert len(features) == 2
    by_task_id = {f["properties"]["task_id"]: f["properties"] for f in features}
    assert by_task_id[1]["assigned_to"] == "alice"
    assert by_task_id[1]["assigned_group"] == ""
    assert by_task_id[1]["building_count"] == 12
    assert by_task_id[2]["assigned_to"] == ""
    assert by_task_id[2]["assigned_group"] == ""


async def test_assignment_routes_handle_legacy_task_ids(client, db, project):
    """Legacy rows saved before id stamping must get usable integer ids.

    Digit-string ids are normalized and missing ids stamped in memory on
    the read paths, and persisted by the save path, so the panel renders
    and saves succeed for projects predating save_task_areas stamping.
    """
    task_areas = json.loads(json.dumps(_TASK_AREAS))
    task_areas["features"][0]["properties"] = {"task_id": "3"}
    task_areas["features"][1]["properties"] = {}
    await _set_task_areas(db, project.id, task_areas)

    panel_response = await client.get(
        f"/projects/{project.id}/assignments-htmx",
        headers={"HX-Request": "true"},
    )
    assert panel_response.status_code == status.HTTP_200_OK
    assert 'id="assignment-summary-table"' in panel_response.text

    geojson_response = await client.get(f"/projects/{project.id}/assignments/geojson")
    assert geojson_response.status_code == status.HTTP_200_OK
    task_ids = [
        feature["properties"]["task_id"]
        for feature in geojson_response.json()["features"]
    ]
    assert task_ids == [3, 1]

    save_response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"3": {"assigned_to": "alice"}})},
        headers={"HX-Request": "true"},
    )
    assert save_response.status_code == status.HTTP_200_OK

    updated_project = await DbProject.one(db, project.id)
    by_task_id = {
        f["properties"]["task_id"]: f["properties"]
        for f in updated_project.task_areas_geojson["features"]
    }
    # The in-memory stamping persisted with the save: unique integer ids
    assert set(by_task_id) == {1, 3}
    assert by_task_id[3]["assigned_to"] == "alice"


async def test_assignment_panel_renders_assignee_suggestions(
    client, db, project, monkeypatch
):
    """QFC collaborator suggestions should render as datalist options."""

    async def fake_suggestions(_project):
        return ["alice", "bob"]

    monkeypatch.setattr(
        assignment_routes, "_qfc_assignee_suggestions", fake_suggestions
    )
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.get(
        f"/projects/{project.id}/assignments-htmx",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'id="assignment-assignee-options"' in response.text
    assert '<option value="alice"></option>' in response.text
    assert '<option value="bob"></option>' in response.text


async def test_assignment_geojson_404_for_no_split_sentinel(client, db, project):
    """The {} sentinel has no features to assign, so the endpoint 404s."""
    await _set_task_areas(db, project.id, {})

    response = await client.get(f"/projects/{project.id}/assignments/geojson")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.json()


async def test_assignment_geojson_requires_project_context():
    """The geojson endpoint should return a JSON 404 without project context."""
    response = await assignment_geojson.fn(
        request=Mock(),
        current_user={"project": None},
        auth_user=Mock(),
        project_id=123,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in json.loads(response.content)


async def test_save_assignments_happy_path(client, db, project):
    """Saving valid assignments should persist and return the summary."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={
            "assignments": json.dumps(
                {
                    "1": {"assigned_to": "alice", "assigned_group": "NE"},
                    "2": {"assigned_to": "bob", "assigned_group": "SW"},
                }
            )
        },
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    hx_trigger = json.loads(response.headers.get("HX-Trigger", "{}"))
    trigger_payload = hx_trigger.get("assignment:saved")
    assert trigger_payload is not None
    assert trigger_payload["projectId"] == project.id
    assert trigger_payload["updated"] == 2
    assert "Assignments saved" in response.text
    assert "alice" in response.text
    assert "bob" in response.text

    updated_project = await DbProject.one(db, project.id)
    by_task_id = {
        f["properties"]["task_id"]: f["properties"]
        for f in updated_project.task_areas_geojson["features"]
    }
    assert by_task_id[1]["assigned_to"] == "alice"
    assert by_task_id[1]["assigned_group"] == "NE"
    assert by_task_id[1]["building_count"] == 12
    assert by_task_id[2]["assigned_to"] == "bob"
    assert by_task_id[2]["assigned_group"] == "SW"
    # Assignment is advisory: the save path must never write task status
    assert "status" not in by_task_id[1]
    assert "status" not in by_task_id[2]


async def test_save_assignments_strips_control_characters(client, db, project):
    """Control characters in free-text assignees should be stripped."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_to": "ali\u0007ce"}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    updated_project = await DbProject.one(db, project.id)
    properties = updated_project.task_areas_geojson["features"][0]["properties"]
    assert properties["assigned_to"] == "alice"


async def test_save_assignments_rejects_bad_group_label(client, db, project):
    """Group labels outside the ODK-safe charset should be rejected."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_group": "north east!"}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Group labels may only contain" in response.text

    updated_project = await DbProject.one(db, project.id)
    properties = updated_project.task_areas_geojson["features"][0]["properties"]
    assert "assigned_group" not in properties


async def test_save_assignments_rejects_overlong_assignee(client, db, project):
    """Assignee values longer than 100 characters should be rejected."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_to": "a" * 101}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "100 characters or fewer" in response.text


async def test_save_assignments_rejects_overlong_group_label(client, db, project):
    """Group labels longer than 100 characters should be rejected."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_group": "g" * 101}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "100 characters or fewer" in response.text


async def test_save_assignments_keeps_entity_sequences_verbatim(client, db, project):
    """Assignees typed with HTML entity sequences must be stored verbatim.

    The assignments payload is plain JSON from JSON.stringify, never
    entity-encoded, so the save path must not HTML-unescape it.
    """
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_to": "Bob &amp; Co"}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    updated_project = await DbProject.one(db, project.id)
    properties = updated_project.task_areas_geojson["features"][0]["properties"]
    assert properties["assigned_to"] == "Bob &amp; Co"


async def test_save_assignments_rejects_unknown_task_id(client, db, project):
    """Task ids not present in the stored task areas should be rejected."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"99": {"assigned_to": "alice"}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unknown task id" in response.text


async def test_save_assignments_rejects_missing_payload(client, db, project):
    """An empty form post should return a clear 400 error."""
    await _set_task_areas(db, project.id, json.loads(json.dumps(_TASK_AREAS)))

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": ""},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No assignments data provided" in response.text


async def test_save_assignments_rejects_no_split_sentinel(client, db, project):
    """Saving against the {} sentinel should fail with a split-first hint."""
    await _set_task_areas(db, project.id, {})

    response = await client.post(
        f"/projects/{project.id}/assignments",
        data={"assignments": json.dumps({"1": {"assigned_to": "alice"}})},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No task areas to assign" in response.text


async def test_published_project_page_includes_assignment_panel_slot(
    client, db, project
):
    """The PUBLISHED setup view should lazy-load the assignment panel."""
    await DbProject.update(
        db,
        project.id,
        DbProject(status=ProjectStatus.PUBLISHED),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'id="assignment-panel"' in response.text
    assert f'hx-get="/projects/{project.id}/assignments-htmx"' in response.text
