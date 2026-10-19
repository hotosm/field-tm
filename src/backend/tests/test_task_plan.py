"""Tests for the task plan API, planner serving, app catalogue and Type B flow."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from litestar import status_codes as status

from app.config import settings
from app.db.models import DbProject
from app.projects import task_plan
from app.projects.mapping_apps import FieldMappingApp, recommend_apps
from app.projects.project_services import ValidationError

SQUARE = [
    [
        [85.30, 27.71],
        [85.30, 27.70],
        [85.31, 27.70],
        [85.31, 27.71],
        [85.30, 27.71],
    ]
]


def _plan(*properties: dict) -> dict:
    return {
        "type": "FeatureCollection",
        "task_plan_version": 1,
        "algorithm": "DIVIDE_BY_SQUARE",
        "params": {"cell_size": 100},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": SQUARE},
                "properties": props,
            }
            for props in properties
        ],
    }


async def _set_project(db, project_id: int, **columns) -> None:
    assignments = ", ".join(f"{key} = %({key})s" for key in columns)
    async with db.cursor() as cur:
        await cur.execute(
            f"UPDATE projects SET {assignments} WHERE id = %(id)s",  # noqa: S608
            {**columns, "id": project_id},
        )
    await db.commit()


# --- clean_task_plan -------------------------------------------------------


def test_clean_task_plan_keeps_known_properties_and_stamps_ids():
    """Known properties are cleaned, unknown ones dropped, ids stamped."""
    cleaned = task_plan.clean_task_plan(
        _plan(
            {
                "task_id": 2,
                "assigned_group": "team-a",
                "assigned_to": " Chomba​ ",
                "comment": "Start Monday",
                "colour": "#ABC",
                "building_count": 12,
            },
            {"assigned_to": ""},
        )
    )

    first, second = (f["properties"] for f in cleaned["features"])
    assert first == {
        "task_id": 2,
        "assigned_group": "team-a",
        "assigned_to": "Chomba",
        "comment": "Start Monday",
        "colour": "#aabbcc",
    }
    assert second == {"task_id": 1}
    assert cleaned["task_plan_version"] == 1
    assert cleaned["algorithm"] == "DIVIDE_BY_SQUARE"


@pytest.mark.parametrize(
    ("plan", "message"),
    [
        ([], "FeatureCollection"),
        ({"type": "FeatureCollection", "features": []}, "no tasks"),
        (_plan({"assigned_group": "team a"}), "Group labels"),
        (_plan({"assigned_to": "x" * 101}), "100 characters"),
        (_plan({"comment": "x" * 501}), "500 characters"),
        (_plan({"colour": "red"}), "hex"),
    ],
)
def test_clean_task_plan_rejects_invalid_plans(plan, message):
    """Invalid plans raise a user-facing validation error."""
    with pytest.raises(ValidationError, match=message):
        task_plan.clean_task_plan(plan)


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Point", "coordinates": [85.3, 27.7]},
        {"type": "Polygon", "coordinates": [[[500, 27.7], [85.3, 27.7]]]},
        None,
    ],
)
def test_clean_task_plan_rejects_non_polygons(geometry):
    """Each task must be a WGS84 polygon."""
    plan = _plan({})
    plan["features"][0]["geometry"] = geometry
    with pytest.raises(ValidationError, match="Task 1 must be a Polygon"):
        task_plan.clean_task_plan(plan)


def test_clean_task_plan_limits_task_count(monkeypatch):
    """Very large plans are rejected."""
    monkeypatch.setattr(task_plan, "MAX_TASKS", 1)
    with pytest.raises(ValidationError, match="at most 1 tasks"):
        task_plan.clean_task_plan(_plan({}, {}))


# --- API -------------------------------------------------------------------


async def test_planner_input_for_manager_includes_features(client, db, project):
    """Managers get the area, data extract and current plan."""
    extract = _plan({})
    await _set_project(
        db,
        project.id,
        data_extract_geojson=json.dumps(extract),
        task_areas_geojson=json.dumps(_plan({"task_id": 1})),
    )

    response = await client.get(f"/api/v1/projects/{project.id}/planner-input")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["project"] == {
        "id": project.id,
        "name": project.project_name,
        "field_mapping_app": "ODK",
    }
    assert body["aoi"]["type"] == "Polygon"
    assert len(body["features"]["features"]) == 1
    assert body["task_plan"]["features"][0]["properties"]["task_id"] == 1


async def test_planner_input_for_guest_hides_features(client, db, project, login_as):
    """Anyone may view a public project's tasks, but not its data extract."""
    await _set_project(db, project.id, data_extract_geojson=json.dumps(_plan({})))
    await login_as(None)

    response = await client.get(f"/api/v1/projects/{project.id}/planner-input")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["features"] is None
    assert response.json()["task_plan"] is None


async def test_planner_input_private_project_needs_role(client, db, project, login_as):
    """Private projects need login (401) and a project role (403)."""
    await _set_project(db, project.id, visibility="PRIVATE")
    url = f"/api/v1/projects/{project.id}/planner-input"

    await login_as(None)
    assert (await client.get(url)).status_code == status.HTTP_401_UNAUTHORIZED
    await login_as("stranger")
    assert (await client.get(url)).status_code == status.HTTP_403_FORBIDDEN


async def test_planner_api_missing_project_is_404(client):
    """Unknown projects are 404 for both endpoints (admin user)."""
    assert (
        await client.get("/api/v1/projects/999999/planner-input")
    ).status_code == status.HTTP_404_NOT_FOUND
    response = await client.put("/api/v1/projects/999999/task-plan", json=_plan({}))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("project_status", ["DRAFT", "PUBLISHED"])
async def test_put_task_plan_saves_and_stamps_ids(client, db, project, project_status):
    """A valid plan is saved for draft and published projects."""
    await _set_project(db, project.id, status=project_status)

    response = await client.put(
        f"/api/v1/projects/{project.id}/task-plan",
        json=_plan({"assigned_group": "team-a"}, {"task_id": 7}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"task_count": 2}
    saved = await DbProject.one(db, project.id)
    assert [
        f["properties"]["task_id"] for f in saved.task_areas_geojson["features"]
    ] == [
        1,
        7,
    ]
    assert saved.task_areas_geojson["features"][0]["properties"]["assigned_group"] == (
        "team-a"
    )


async def test_put_task_plan_rejects_invalid_plan(client, db, project):
    """Validation errors are 422 with a readable detail, and nothing is saved."""
    response = await client.put(
        f"/api/v1/projects/{project.id}/task-plan",
        json=_plan({"colour": "red"}),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "hex" in response.json()["detail"]
    assert (await DbProject.one(db, project.id)).task_areas_geojson is None


# --- HTMX task routes ------------------------------------------------------


async def test_upload_task_plan_saves_file(client, db, project):
    """The upload fallback uses the same validation and redirects back."""
    response = await client.post(
        f"/projects/{project.id}/task-plan/upload",
        files={"data": ("plan.geojson", json.dumps(_plan({})), "application/json")},
    )

    assert response.headers["HX-Redirect"] == f"/projects/{project.id}"
    saved = await DbProject.one(db, project.id)
    assert len(saved.task_areas_geojson["features"]) == 1


async def test_upload_task_plan_rejects_bad_file(client, project):
    """Non-JSON uploads show an error."""
    response = await client.post(
        f"/projects/{project.id}/task-plan/upload",
        files={"data": ("plan.geojson", b"not json", "application/json")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not valid GeoJSON" in response.text


async def test_use_whole_area_clears_plan(client, db, project):
    """'Use whole area' stores the single-task sentinel."""
    await _set_project(db, project.id, task_areas_geojson=json.dumps(_plan({})))

    response = await client.post(f"/projects/{project.id}/task-plan/whole-area")

    assert response.headers["HX-Redirect"] == f"/projects/{project.id}"
    assert (await DbProject.one(db, project.id)).task_areas_geojson == {}


async def test_sync_task_plan_pushes_to_published_odk(client, db, project):
    """Re-sync updates the ODK tasks entity list for published projects."""
    url = f"/projects/{project.id}/task-plan/sync"
    assert (await client.post(url)).status_code == status.HTTP_400_BAD_REQUEST

    await _set_project(db, project.id, status="PUBLISHED")
    with patch(
        "app.htmx.task_plan_routes.sync_odk_tasks", new_callable=AsyncMock
    ) as mock_sync:
        response = await client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert "Tasks updated" in response.text
    assert mock_sync.await_args.args[2] == project.external_project_id


# --- Planner static files --------------------------------------------------


@pytest.fixture
def planner_dir(tmp_path, monkeypatch):
    """A fake planner build."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Planner</title>")
    (tmp_path / "assets" / "pglite.wasm").write_bytes(b"\0asm")
    (tmp_path / "assets" / "postgis.tar.gz").write_bytes(b"\x1f\x8b")
    (tmp_path.parent / "secret.txt").write_text("secret")
    monkeypatch.setattr(settings, "PLANNER_DIR", str(tmp_path))
    return tmp_path


async def test_planner_redirects_to_trailing_slash(client, planner_dir):
    """/planner needs the slash for relative asset paths; the query is kept."""
    response = await client.get("/planner?project=3", follow_redirects=False)

    assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert response.headers["location"] == "/planner/?project=3"


async def test_planner_serves_index_and_assets(client, planner_dir):
    """Index, wasm and gz files get the right headers."""
    index = await client.get("/planner/?project=3")
    assert index.status_code == status.HTTP_200_OK
    assert index.headers["content-type"].startswith("text/html")
    assert index.headers["x-frame-options"] == "SAMEORIGIN"
    assert "Planner" in index.text

    wasm = await client.get("/planner/assets/pglite.wasm")
    assert wasm.headers["content-type"] == "application/wasm"

    gz = await client.get("/planner/assets/postgis.tar.gz")
    assert "content-encoding" not in gz.headers
    assert gz.content == b"\x1f\x8b"


async def test_planner_blocks_path_traversal(client, planner_dir):
    """Files outside the planner directory are never served."""
    response = await client.get("/planner/..%2Fsecret.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "secret" not in response.text


async def test_planner_missing_build_explains(client, monkeypatch, tmp_path):
    """Without a build, a helpful 404 page is shown."""
    monkeypatch.setattr(settings, "PLANNER_DIR", str(tmp_path / "missing"))
    response = await client.get("/planner/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "just build planner" in response.text


# --- App catalogue and recommendation --------------------------------------


@pytest.mark.parametrize(
    ("mapping_type", "for_osm", "well_mapped", "expected"),
    [
        ("buildings", False, None, ["QField", "ODK"]),
        ("buildings", True, True, ["EveryDoor", "StreetComplete"]),
        ("pois", True, True, ["EveryDoor", "StreetComplete"]),
        ("roads", True, True, ["StreetComplete", "Panoramax"]),
        ("rivers", True, True, ["QField"]),
        ("other", True, None, ["QField"]),
        ("buildings", True, False, ["QField", "ODK"]),
        ("roads", True, False, ["QField", "ODK"]),
    ],
)
def test_recommend_apps(mapping_type, for_osm, well_mapped, expected):
    """The guided questions map to the documented recommendations."""
    apps, reason = recommend_apps(mapping_type, for_osm, well_mapped)
    assert [app.value for app in apps] == expected
    assert reason


async def test_app_picker_fragment_marks_recommended_first(client):
    """The picker lists recommended apps first, keeping the selection."""
    response = await client.get(
        "/new/app-picker",
        params={
            "mapping_type": "roads",
            "for_osm": "yes",
            "well_mapped": "yes",
            "field_mapping_app": "ODK",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    text = response.text
    assert text.index('value="StreetComplete"') < text.index('value="QField"')
    assert text.count("Recommended") == 2
    odk_input = text[text.index('value="ODK"') :].split("/>")[0]
    assert "checked" in odk_input


async def test_new_custom_page_lists_all_apps(client):
    """The custom create page shows every app with a logo or initial."""
    response = await client.get("/new/custom")
    for app in FieldMappingApp:
        assert f'value="{app.value}"' in response.text
    assert "/static/images/apps/everydoor.png" in response.text


async def test_app_logo_served_from_subfolder(client):
    """App logos live in static/images/apps/."""
    response = await client.get("/static/images/apps/streetcomplete.svg")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("image/svg+xml")
    traversal = await client.get("/static/images/..%2F..%2Fmain.py")
    assert traversal.status_code == status.HTTP_403_FORBIDDEN


# --- Type B ("files only") projects ----------------------------------------


async def test_type_b_project_skips_form_and_data_steps(client, db, project):
    """Files-only apps go straight to Tasks, then Publish (no sync)."""
    await _set_project(
        db, project.id, field_mapping_app="EveryDoor", xlsform_content=None
    )

    response = await client.get(f"/projects/{project.id}")
    assert "Survey Form" not in response.text
    assert 'id="step-2-container"' not in response.text
    assert "Split &amp; assign tasks" in response.text
    assert 'id="step-5-container"' not in response.text

    await _set_project(db, project.id, task_areas_geojson=json.dumps(_plan({})))
    response = await client.get(f"/projects/{project.id}")
    assert "Publish Project" in response.text

    response = await client.post(f"/create-project-htmx?project_id={project.id}")
    assert response.headers["HX-Redirect"] == f"/projects/{project.id}"
    published = await DbProject.one(db, project.id)
    assert published.status == "PUBLISHED"

    response = await client.get(f"/projects/{project.id}")
    assert "Open tasks for download and sharing" in response.text
    assert "https://every-door.app" in response.text
    assert "qrcode-container" not in response.text
