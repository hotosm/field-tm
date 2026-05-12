"""Tests for HTMX routes."""

import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from area_splitter import SplittingAlgorithm
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.config import AuthProvider, settings
from app.htmx.project_create.project_create_page_routes import (
    new_project_chooser,
    new_project_custom,
    new_project_simple,
)
from app.htmx.project_create.project_create_parsing import (
    parse_outline_payload as _parse_outline_payload,
)
from app.htmx.project_create.project_create_simple_flow import (
    prepare_simple_project_data_extract as _prepare_simple_project_data_extract,
)
from app.htmx.project_create.project_create_submit_routes import (
    create_simple_project_htmx,
)
from app.htmx.project_create.project_create_xlsform_routes import upload_xlsform_htmx
from app.projects.project_services import (
    ConflictError,
    ServiceError,
)
from app.projects.project_services import ValidationError as SvcValidationError

# We patch where project_crud is used/defined.
# htmx_routes imports `from app.projects import project_crud`
# so we patch `app.projects.project_crud.get_project_qrcode`


async def test_create_project_htmx(client, stub_project_data):
    """Test project creation via HTMX."""
    # The route expects form data
    response = await client.post(
        "/projects/create",
        data=stub_project_data,
        headers={"HX-Request": "true"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "HX-Redirect" in response.headers
    location = response.headers["HX-Redirect"]
    assert "/projects/" in location


async def test_create_project_htmx_returns_inline_error_for_missing_description(
    client, stub_project_data
):
    """Validation errors should return 400 with an inline HTML error fragment."""
    payload = dict(stub_project_data)
    payload["description"] = ""

    response = await client.post(
        "/projects/create",
        data=payload,
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Description is required." in response.text


async def test_create_simple_project_htmx_success(monkeypatch):
    """Simple HTMX creation should auto-complete setup, split tasks, and redirect."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=321)

    captured: dict = {}

    async def fake_process_xlsform(**kwargs):
        captured["process_xlsform"] = kwargs

    async def fake_prepare_simple_project_data_extract(*, db, project_id):
        captured["prepare_extract"] = {"db": db, "project_id": project_id}

    async def fake_split_aoi(db, project_id, options):
        captured["split_aoi"] = {
            "db": db,
            "project_id": project_id,
            "options": options,
        }
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"task_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [85.0, 27.0],
                                [85.1, 27.0],
                                [85.1, 27.1],
                                [85.0, 27.1],
                                [85.0, 27.0],
                            ]
                        ],
                    },
                }
            ],
        }

    async def fake_save_task_areas(db, project_id, tasks_geojson):
        captured["save_task_areas"] = {
            "db": db,
            "project_id": project_id,
            "tasks_geojson": tasks_geojson,
        }
        return 1

    async def fake_finalize_qfield_project(*, db, project_id):
        captured["finalize_qfield"] = {"db": db, "project_id": project_id}
        return SimpleNamespace(qfield_url="https://example.com/p/321")

    async def fake_claim_simple_project_basemap_generation(*, db, project_id):
        captured["claim_generation"] = {"db": db, "project_id": project_id}
        return True

    async def fake_autostart_basemap_for_simple_project(project_id, outline):
        return None

    def fake_create_task(coro):
        captured["autostart_coro"] = coro
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        fake_process_xlsform,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        fake_prepare_simple_project_data_extract,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi", fake_split_aoi
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        fake_save_task_areas,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        fake_finalize_qfield_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._autostart_basemap_for_simple_project",
        fake_autostart_basemap_for_simple_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    db = AsyncMock()
    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=db,
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/321"
    assert captured["process_xlsform"]["project_id"] == 321
    assert isinstance(captured["process_xlsform"]["xlsform_bytes"], BytesIO)
    assert captured["prepare_extract"]["project_id"] == 321
    assert captured["split_aoi"]["project_id"] == 321
    assert (
        captured["split_aoi"]["options"].algorithm
        == SplittingAlgorithm.AVG_BUILDING_SKELETON.value
    )
    assert captured["split_aoi"]["options"].no_of_buildings == 10
    assert captured["save_task_areas"]["project_id"] == 321
    assert captured["finalize_qfield"]["project_id"] == 321
    assert captured["claim_generation"]["project_id"] == 321
    assert "autostart_coro" in captured


async def test_create_simple_project_htmx_skips_split_for_empty_extract(monkeypatch):
    """Empty extract should skip splitting and show collect-new-data mode."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=323)

    captured: dict = {}

    async def fake_claim_simple_project_basemap_generation(*, db, project_id):
        captured["claim_generation"] = {"db": db, "project_id": project_id}
        return True

    def fake_create_task(coro):
        captured["autostart_coro"] = coro
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={"type": "FeatureCollection", "features": []}
            )
        ),
    )
    split_aoi_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi", split_aoi_mock
    )
    save_task_areas_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        save_task_areas_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/323")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/323"
    assert "HX-Trigger" in response.headers
    trigger_payload = json.loads(response.headers["HX-Trigger"])
    assert "simpleCollectNewDataNotice" in trigger_payload
    assert "No existing OSM buildings" in trigger_payload["simpleCollectNewDataNotice"]
    split_aoi_mock.assert_not_awaited()
    save_task_areas_mock.assert_not_awaited()
    assert captured["claim_generation"]["project_id"] == 323


async def test_create_simple_project_htmx_returns_inline_error_when_split_fails(
    monkeypatch,
):
    """Non-empty extract split failures should return inline form errors."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=324)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi",
        AsyncMock(side_effect=SvcValidationError("Split failed for AOI")),
    )
    finalize_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        finalize_mock,
    )
    claim_generation_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        claim_generation_mock,
    )
    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        create_task_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Split failed for AOI" in response.content
    assert "HX-Redirect" not in response.headers
    finalize_mock.assert_not_awaited()
    claim_generation_mock.assert_not_awaited()
    create_task_mock.assert_not_called()


async def test_create_simple_project_htmx_success_even_if_autostart_will_fail(
    monkeypatch,
):
    """Simple creation should still redirect successfully even if later attach fails."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=322)

    captured: dict = {}

    async def fake_autostart_basemap_for_simple_project(project_id, outline):
        raise RuntimeError("temporary DNS lookup failure")

    async def fake_claim_simple_project_basemap_generation(*, db, project_id):
        captured["claim_generation"] = {"db": db, "project_id": project_id}
        return True

    def fake_create_task(coro):
        captured["autostart_coro"] = coro
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/322")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._autostart_basemap_for_simple_project",
        fake_autostart_basemap_for_simple_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/322"
    assert captured["claim_generation"]["project_id"] == 322
    assert "autostart_coro" in captured


async def test_create_simple_project_htmx_requires_default_form(monkeypatch):
    """Missing default OSM Buildings template should return inline error."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=321)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=None),
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Could not load default OSM Buildings form" in response.content


async def test_create_simple_project_htmx_rejects_invalid_outline():
    """Invalid outline payload should return inline form validation markup."""
    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": "not-json"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Project area must be valid JSON" in response.content


async def test_create_simple_project_htmx_sets_missing_outline_trigger(
    monkeypatch,
):
    """AOI validation failures should trigger the map-outline HTMX event."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        raise SvcValidationError("Area of Interest is too large for this workflow.")

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("HX-Trigger")
    assert "missingOutline" in response.headers["HX-Trigger"]


async def test_create_simple_project_htmx_handles_conflict(monkeypatch):
    """Duplicate simple project names should retry with a unique suffix."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    captured_names: list[str] = []

    async def fake_create_project_stub(**kwargs):
        captured_names.append(kwargs["project_name"])
        if len(captured_names) == 1:
            raise ConflictError("Project already exists")
        return SimpleNamespace(id=654)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/654")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        lambda coro: (coro.close(), Mock())[1],
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/654"
    assert len(captured_names) == 2
    assert captured_names[0] == "Kathmandu OSM Buildings"
    assert captured_names[1].startswith("Kathmandu OSM Buildings ")
    assert captured_names[1] != captured_names[0]


async def test_create_simple_project_htmx_uses_deterministic_fallback_name(monkeypatch):
    """Simple-flow fallback naming stays deterministic before uniqueness suffix."""
    captured: dict = {}

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Area 27.7050_85.3050 OSM Buildings",
            "Simple workflow project",
            ["osm", "buildings", "simple"],
            None,
        )

    call_count = 0

    async def fake_create_project_stub(**kwargs):
        nonlocal call_count
        call_count += 1
        captured[f"project_name_{call_count}"] = kwargs["project_name"]
        if call_count == 1:
            raise ConflictError("Project already exists")
        return SimpleNamespace(id=777)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/777")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        lambda coro: (coro.close(), Mock())[1],
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/777"
    assert captured["project_name_1"].startswith("Area 27.7050_85.3050")
    assert captured["project_name_1"] != "Unnamed Area OSM Buildings"
    assert captured["project_name_2"].startswith("Area 27.7050_85.3050 OSM Buildings ")


async def test_create_simple_project_htmx_skips_autostart_when_claim_not_acquired(
    monkeypatch,
):
    """Simple creation should not enqueue autostart when claim is already held."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        return (
            "Kathmandu OSM Buildings",
            "Simple workflow project",
            ["#osm", "#buildings", "#simple"],
            "Kathmandu, Nepal",
        )

    async def fake_create_project_stub(**kwargs):
        return SimpleNamespace(id=333)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes._create_simple_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/333")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.claim_simple_project_basemap_generation",
        AsyncMock(return_value=False),
    )
    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        create_task_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.get_user_sub",
        lambda _auth_user: "user-sub-1",
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/projects/333"
    create_task_mock.assert_not_called()


async def test_create_simple_project_htmx_handles_service_error(monkeypatch):
    """Service-layer failures should return an inline error block."""

    async def fake_derive_simple_project_metadata(*, db, outline):
        raise ServiceError("Failed to create simple project")

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_submit_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )

    response = await create_simple_project_htmx.fn(
        request=Mock(),
        db=AsyncMock(),
        auth_user=Mock(),
        data={"outline": json.dumps({"type": "Polygon", "coordinates": []})},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Failed to create simple project" in response.content


async def test_prepare_simple_project_data_extract_falls_back_on_no_valid_geometries(
    monkeypatch,
):
    """Empty-geometry validation should degrade to collect-new-data persistence."""
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.download_osm_data",
        AsyncMock(
            side_effect=SvcValidationError(
                "No valid geometries found in OSM. "
                "Please continue with collect new data."
            )
        ),
    )
    save_data_extract_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.save_data_extract",
        save_data_extract_mock,
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.DbProject.update",
        update_mock,
    )

    await _prepare_simple_project_data_extract(db=db, project_id=987)

    save_data_extract_mock.assert_not_awaited()
    update_mock.assert_awaited_once()
    project_update = update_mock.await_args.args[2]
    assert project_update.data_extract_geojson == {
        "type": "FeatureCollection",
        "features": [],
    }
    assert project_update.task_areas_geojson == {}
    db.commit.assert_awaited_once()


async def test_prepare_simple_project_data_extract_reraises_unrelated_validation(
    monkeypatch,
):
    """Unrelated validation failures should still propagate to callers."""
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_simple_flow.download_osm_data",
        AsyncMock(side_effect=SvcValidationError("Area of Interest is too large.")),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.DbProject.update",
        update_mock,
    )

    with pytest.raises(SvcValidationError, match="Area of Interest is too large"):
        await _prepare_simple_project_data_extract(db=db, project_id=988)

    update_mock.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_resume_simple_project_tilepack_if_needed_updates_status(
    monkeypatch,
):
    """Resume helper should refresh status for already-selected STAC items."""
    from app.htmx.project_create.project_create_basemap_orchestration import (
        resume_simple_project_tilepack_if_needed,
    )

    db = Mock()
    db.commit = AsyncMock()

    project = SimpleNamespace(
        id=202,
        basemap_stac_item_id="item-202",
        basemap_url=None,
    )

    check_status_mock = AsyncMock(return_value=("generating", None))
    update_mock = AsyncMock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.check_tilepack_status",
        check_status_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.DbProject.update",
        update_mock,
    )

    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        create_task_mock,
    )

    resumed = await resume_simple_project_tilepack_if_needed(db, project)

    assert resumed is True
    check_status_mock.assert_awaited_once_with("item-202")
    update_mock.assert_awaited_once()
    update_payload = update_mock.await_args.args[2]
    assert update_payload.basemap_status == "generating"
    assert update_payload.basemap_attach_status == "pending_autostart"
    db.commit.assert_awaited_once()
    create_task_mock.assert_not_called()


async def test_resume_simple_project_tilepack_if_needed_starts_attach_when_ready(
    monkeypatch,
):
    """Resume helper should enqueue attach when tilepack is already ready."""
    from app.htmx.project_create.project_create_basemap_orchestration import (
        resume_simple_project_tilepack_if_needed,
    )

    db = Mock()
    db.commit = AsyncMock()

    project = SimpleNamespace(
        id=303,
        basemap_stac_item_id="item-303",
        basemap_url=None,
    )

    check_status_mock = AsyncMock(
        return_value=("ready", "https://tiles.example/item.mbtiles")
    )
    update_mock = AsyncMock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.check_tilepack_status",
        check_status_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.DbProject.update",
        update_mock,
    )

    async def fake_attach(project_id, basemap_url):
        return None

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.run_basemap_attach_background",
        fake_attach,
    )

    captured_attach_calls: list[tuple[int, str]] = []

    def fake_create_task(coro):
        captured_attach_calls.append(
            (
                coro.cr_frame.f_locals["project_id"],
                coro.cr_frame.f_locals["basemap_url"],
            )
        )
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_basemap_orchestration.asyncio.create_task",
        fake_create_task,
    )

    resumed = await resume_simple_project_tilepack_if_needed(db, project)

    assert resumed is True
    check_status_mock.assert_awaited_once_with("item-303")
    update_payload = update_mock.await_args.args[2]
    assert update_payload.basemap_status == "ready"
    assert update_payload.basemap_url == "https://tiles.example/item.mbtiles"
    assert update_payload.basemap_attach_status == "in_progress"
    db.commit.assert_awaited_once()
    assert captured_attach_calls == [(303, "https://tiles.example/item.mbtiles")]


async def test_resume_simple_project_tilepack_if_needed_ignores_blank_stac_item():
    """Resume helper should no-op when no STAC item id is set."""
    from app.htmx.project_create.project_create_basemap_orchestration import (
        resume_simple_project_tilepack_if_needed,
    )

    db = Mock()
    project = SimpleNamespace(id=404, basemap_stac_item_id="", basemap_url=None)

    resumed = await resume_simple_project_tilepack_if_needed(db, project)

    assert resumed is False


async def test_new_project_redirects_guests_to_login(monkeypatch):
    """The new-project page should redirect unauthenticated guests to login."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new"
    request.headers = {}

    response = await new_project_chooser.fn(request=request, auth_user=None)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/login?return_to=%2Fnew"


async def test_new_project_custom_redirects_guests_to_login(monkeypatch):
    """The custom-project page should redirect unauthenticated guests to login."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new/custom"
    request.headers = {}

    response = await new_project_custom.fn(request=request, auth_user=None)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/login?return_to=%2Fnew%2Fcustom"


async def test_new_project_simple_redirects_guests_to_login(monkeypatch):
    """The simple new-project page should redirect unauthenticated guests."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new/simple"
    request.headers = {}

    response = await new_project_simple.fn(
        request=request,
        auth_user=None,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/login?return_to=%2Fnew%2Fsimple"


async def test_new_project_htmx_redirects_guests_with_hx_redirect(monkeypatch):
    """HTMX requests should get 200 + HX-Redirect, not a 307 the browser follows."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new"
    request.headers = {"HX-Request": "true"}

    response = await new_project_chooser.fn(request=request, auth_user=None)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/login?return_to=%2Fnew"


async def test_new_project_simple_htmx_redirects_guests_with_hx_redirect(
    monkeypatch,
):
    """HTMX simple requests should use HX-Redirect with simple return path."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new/simple"
    request.headers = {"HX-Request": "true"}

    response = await new_project_simple.fn(
        request=request,
        auth_user=None,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/login?return_to=%2Fnew%2Fsimple"


async def test_new_project_page_renders_both_workflow_cards(client):
    """Chooser page should link to both the simple and custom workflows."""
    response = await client.get("/new", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert 'href="/new/simple"' in response.text
    assert 'href="/new/custom"' in response.text
    assert "Map buildings" in response.text
    assert "Something else" in response.text


async def test_new_project_custom_and_simple_share_map_ids(client):
    """Custom and simple project-create pages should expose shared map elements."""
    custom_response = await client.get("/new/custom", headers={"HX-Request": "true"})
    simple_response = await client.get("/new/simple", headers={"HX-Request": "true"})

    assert custom_response.status_code == status.HTTP_200_OK
    assert simple_response.status_code == status.HTTP_200_OK

    assert 'id="map"' in custom_response.text
    assert 'id="outline-geojson"' in custom_response.text
    assert 'id="map"' in simple_response.text
    assert 'id="outline-geojson"' in simple_response.text


def test_new_project_simple_template_has_submit_loading_indicator():
    """Simple template should include HTMX submit loading indicator markup."""
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.add_extension("jinja2.ext.i18n")
    env.install_gettext_callables(
        lambda message: message, lambda s, p, n: s if n == 1 else p
    )
    env.globals["current_locale"] = lambda: "en"
    env.globals["supported_locales"] = ["en", "fr", "es", "sw", "ar", "pt", "pt_br"]
    env.globals["locale_labels"] = {
        "en": "English",
        "fr": "Français",
        "es": "Español",
        "sw": "Kiswahili",
        "ar": "العربية",
        "pt": "Português",
        "pt_br": "Português (Brasil)",
    }
    env.globals["auth_enabled"] = False
    env.globals["current_dir"] = lambda: "ltr"

    rendered = env.get_template("new_project_simple.html").render()

    assert 'id="create-simple-project-form"' in rendered
    assert 'hx-indicator="#submit-indicator"' in rendered
    assert 'id="submit-indicator"' in rendered
    assert "<wa-spinner" in rendered
    assert "Creating project and preparing map" in rendered
    assert 'id="submit-btn"' in rendered
    assert "aria-busy" in rendered
    assert 'getResponseHeader("HX-Redirect")' in rendered
    assert 'startsWith("/projects/")' in rendered


def test_new_project_simple_template_uses_gettext_for_map_strings():
    """Simple template should route map-script strings through gettext."""
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.add_extension("jinja2.ext.i18n")

    translations = {
        "Create Project": "Crear proyecto",
        "Switch to Custom Project": "Cambiar a proyecto personalizado",
        "Creating project and preparing map...": (
            "Creando proyecto y preparando mapa..."
        ),
        "Area": "Superficie",
        "Invalid geometry": "Geometria invalida",
        "Undo last vertex": "Deshacer ultimo vertice",
        "My location": "Mi ubicacion",
        "Failed to validate GeoJSON": "No se pudo validar GeoJSON",
        "No GeoJSON returned from validation": "La validacion no devolvio GeoJSON",
    }
    env.install_gettext_callables(
        lambda message: translations.get(message, message),
        lambda singular, plural, n: singular if n == 1 else plural,
    )
    env.globals["current_locale"] = lambda: "es"
    env.globals["supported_locales"] = ["en", "es"]
    env.globals["locale_labels"] = {
        "en": "English",
        "es": "Español",
    }
    env.globals["auth_enabled"] = False
    env.globals["current_dir"] = lambda: "ltr"

    rendered = env.get_template("new_project_simple.html").render()

    assert "Crear proyecto" in rendered
    assert "Cambiar a proyecto personalizado" in rendered
    assert "Creando proyecto y preparando mapa..." in rendered
    assert '"Superficie"' in rendered
    assert '"Geometria invalida"' in rendered
    assert '"Deshacer ultimo vertice"' in rendered
    assert '"Mi ubicacion"' in rendered
    assert '"No se pudo validar GeoJSON"' in rendered
    assert '"La validacion no devolvio GeoJSON"' in rendered


async def test_upload_xlsform_htmx_passes_none_default_language_when_not_explicit(
    monkeypatch,
):
    """HTMX upload should pass None when language was auto-selected but not explicit."""
    captured: dict = {}

    async def fake_resolve_uploaded_xlsform_bytes(data, db):
        return BytesIO(b"fake-xls"), None

    async def fake_process_xlsform(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_xlsform_routes._resolve_uploaded_xlsform_bytes",
        fake_resolve_uploaded_xlsform_bytes,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_xlsform_routes.process_xlsform",
        fake_process_xlsform,
    )

    response = await upload_xlsform_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": SimpleNamespace(id=42)},
        auth_user=Mock(),
        data=SimpleNamespace(
            xlsform=None,
            template_form_id="1",
            need_verification_fields="true",
            include_photo_upload="true",
            mandatory_photo_upload="false",
            use_odk_collect="false",
            default_language_explicit="false",
            default_language="french",
        ),
        project_id=42,
    )

    assert response.status_code == status.HTTP_200_OK
    assert captured["default_language"] is None


async def test_upload_xlsform_htmx_passes_selected_default_language_when_explicit(
    monkeypatch,
):
    """HTMX upload should forward selected language when user explicitly changed it."""
    captured: dict = {}

    async def fake_resolve_uploaded_xlsform_bytes(data, db):
        return BytesIO(b"fake-xls"), None

    async def fake_process_xlsform(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.htmx.project_create.project_create_xlsform_routes._resolve_uploaded_xlsform_bytes",
        fake_resolve_uploaded_xlsform_bytes,
    )
    monkeypatch.setattr(
        "app.htmx.project_create.project_create_xlsform_routes.process_xlsform",
        fake_process_xlsform,
    )

    response = await upload_xlsform_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": SimpleNamespace(id=42)},
        auth_user=Mock(),
        data=SimpleNamespace(
            xlsform=None,
            template_form_id="1",
            need_verification_fields="true",
            include_photo_upload="true",
            mandatory_photo_upload="false",
            use_odk_collect="false",
            default_language_explicit="true",
            default_language="french",
        ),
        project_id=42,
    )

    assert response.status_code == status.HTTP_200_OK
    assert captured["default_language"] == "french"


def test_parse_outline_payload_accepts_feature_json_string():
    """Parse a drawn-map style single Feature JSON string."""
    outline = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.317028828, 27.7052522097],
                    [85.317028828, 27.7041424888],
                    [85.318844411, 27.7041424888],
                    [85.318844411, 27.7052522097],
                    [85.317028828, 27.7052522097],
                ]
            ],
        },
    }

    parsed = _parse_outline_payload(json.dumps(outline))
    assert parsed == outline


def test_parse_outline_payload_accepts_single_item_list_wrapper():
    """Parse list-wrapped form values from URL-encoded body parsers."""
    outline = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.317028828, 27.7052522097],
                    [85.317028828, 27.7041424888],
                    [85.318844411, 27.7041424888],
                    [85.318844411, 27.7052522097],
                    [85.317028828, 27.7052522097],
                ]
            ],
        },
    }

    parsed = _parse_outline_payload([json.dumps(outline)])
    assert parsed == outline


def test_parse_outline_payload_rejects_invalid_json():
    """Reject invalid outline strings with a clear validation error."""
    with pytest.raises(ValueError, match="Project area must be valid JSON"):
        _parse_outline_payload("not-valid-geojson")
