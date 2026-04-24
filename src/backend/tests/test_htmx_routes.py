"""Tests for HTMX routes."""

import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from area_splitter import SplittingAlgorithm
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.config import AuthProvider, settings
from app.db.enums import FieldMappingApp, ProjectStatus
from app.db.models import DbProject
from app.htmx import setup_step_routes
from app.htmx.map_helpers import render_leaflet_map
from app.htmx.project_create_routes import (
    _parse_outline_payload,
    _prepare_simple_project_data_extract,
    create_simple_project_htmx,
    new_project,
    new_project_simple,
    reconcile_simple_project_basemap_autostarts,
    upload_xlsform_htmx,
)
from app.htmx.project_list_routes import project_listing
from app.htmx.setup_step_routes import (
    _build_finalize_error_html,
    _build_odk_finalize_success_html,
    _task_boundaries_layer,
    accept_data_extract_htmx,
    accept_split_htmx,
    download_osm_data_htmx,
    upload_geojson_htmx,
)
from app.projects.project_services import (
    ConflictError,
    ODKFinalizeResult,
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        fake_process_xlsform,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        fake_prepare_simple_project_data_extract,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature"}],
                }
            )
        ),
    )
    monkeypatch.setattr("app.htmx.project_create_routes.split_aoi", fake_split_aoi)
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas", fake_save_task_areas
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        fake_finalize_qfield_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        fake_autostart_basemap_for_simple_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
        AsyncMock(
            return_value=SimpleNamespace(
                data_extract_geojson={"type": "FeatureCollection", "features": []}
            )
        ),
    )
    split_aoi_mock = AsyncMock()
    monkeypatch.setattr("app.htmx.project_create_routes.split_aoi", split_aoi_mock)
    save_task_areas_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas", save_task_areas_mock
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/323")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
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
        "app.htmx.project_create_routes.split_aoi",
        AsyncMock(side_effect=SvcValidationError("Split failed for AOI")),
    )
    finalize_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        finalize_mock,
    )
    claim_generation_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        claim_generation_mock,
    )
    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        create_task_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
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
        "app.htmx.project_create_routes.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/322")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        fake_autostart_basemap_for_simple_project,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
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
        "app.htmx.project_create_routes.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/654")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        lambda coro: (coro.close(), Mock())[1],
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
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
        "app.htmx.project_create_routes.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/777")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        lambda coro: (coro.close(), Mock())[1],
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
        fake_derive_simple_project_metadata,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.create_project_stub",
        fake_create_project_stub,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._get_default_buildings_template_bytes",
        AsyncMock(return_value=b"xlsx-bytes"),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._prepare_simple_project_data_extract",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.DbProject.one",
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
        "app.htmx.project_create_routes.split_aoi",
        AsyncMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_task_areas",
        AsyncMock(return_value=0),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.finalize_qfield_project",
        AsyncMock(return_value=SimpleNamespace(qfield_url="https://example.com/p/333")),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        AsyncMock(return_value=False),
    )
    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        create_task_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.get_user_sub",
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
        "app.htmx.project_create_routes.derive_simple_project_metadata",
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
        "app.htmx.project_create_routes.download_osm_data",
        AsyncMock(
            side_effect=SvcValidationError(
                "No valid geometries found in OSM. "
                "Please continue with collect new data."
            )
        ),
    )
    save_data_extract_mock = AsyncMock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.save_data_extract", save_data_extract_mock
    )
    update_mock = AsyncMock()
    monkeypatch.setattr("app.htmx.project_create_routes.DbProject.update", update_mock)

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
        "app.htmx.project_create_routes.download_osm_data",
        AsyncMock(side_effect=SvcValidationError("Area of Interest is too large.")),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr("app.htmx.project_create_routes.DbProject.update", update_mock)

    with pytest.raises(SvcValidationError, match="Area of Interest is too large"):
        await _prepare_simple_project_data_extract(db=db, project_id=988)

    update_mock.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_reconcile_simple_project_basemap_autostarts_enqueues_eligible_rows(
    monkeypatch,
):
    """Startup reconciliation should enqueue stranded simple-flow basemap jobs."""
    rows = [
        {
            "id": 41,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        }
    ]

    execute_mock = AsyncMock()
    fetchall_mock = AsyncMock(return_value=rows)

    class FakeCursor:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def execute(self, *args, **kwargs):
            return await execute_mock(*args, **kwargs)

        async def fetchall(self):
            return await fetchall_mock()

    class FakeConnection:
        def cursor(self, *args, **kwargs):
            return FakeCursor()

    class FakeConnectionContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class FakePool:
        def connection(self):
            return FakeConnectionContext()

    server = SimpleNamespace(state=SimpleNamespace(db_pool=FakePool()))

    captured_project_ids: list[int] = []
    claim_calls: list[int] = []

    async def fake_claim_simple_project_basemap_generation(*, db, project_id):
        claim_calls.append(project_id)
        return True

    async def fake_autostart(project_id, outline):
        return None

    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        fake_autostart,
    )

    def fake_create_task(coro):
        captured_project_ids.append(coro.cr_frame.f_locals["project_id"])
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )

    await reconcile_simple_project_basemap_autostarts(server)

    execute_mock.assert_awaited_once()
    fetchall_mock.assert_awaited_once()
    assert claim_calls == [41]
    assert captured_project_ids == [41]


async def test_reconcile_simple_project_basemap_autostarts_filters_and_continues(
    monkeypatch,
):
    """Ineligible or malformed rows should be skipped without blocking valid rows."""
    rows = [
        {
            "id": 101,
            "field_mapping_app": FieldMappingApp.ODK.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        },
        {
            "id": 102,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.DRAFT.value,
            "outline": {"type": "Polygon", "coordinates": []},
        },
        {
            "id": 103,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": None,
        },
        {
            "id": "oops",
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        },
        {
            "id": 104,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        },
        {
            "id": 105,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        },
    ]

    class FakeCursor:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def execute(self, *_args, **_kwargs):
            return None

        async def fetchall(self):
            return rows

    class FakeConnection:
        def cursor(self, *args, **kwargs):
            return FakeCursor()

    class FakeConnectionContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class FakePool:
        def connection(self):
            return FakeConnectionContext()

    server = SimpleNamespace(state=SimpleNamespace(db_pool=FakePool()))

    async def fake_claim_simple_project_basemap_generation(*, db, project_id):
        if project_id == 104:
            raise RuntimeError("claim failed")
        return project_id == 105

    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        fake_claim_simple_project_basemap_generation,
    )

    async def fake_autostart(project_id, outline):
        return None

    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        fake_autostart,
    )

    captured_project_ids: list[int] = []

    def fake_create_task(coro):
        captured_project_ids.append(coro.cr_frame.f_locals["project_id"])
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )

    await reconcile_simple_project_basemap_autostarts(server)

    assert captured_project_ids == [105]


async def test_reconcile_simple_project_basemap_autostarts_skips_unclaimed_rows(
    monkeypatch,
):
    """Rows that fail atomic claim should not be enqueued."""
    rows = [
        {
            "id": 77,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "outline": {"type": "Polygon", "coordinates": []},
        }
    ]

    class FakeCursor:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def execute(self, *_args, **_kwargs):
            return None

        async def fetchall(self):
            return rows

    class FakeConnection:
        def cursor(self, *args, **kwargs):
            return FakeCursor()

    class FakeConnectionContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class FakePool:
        def connection(self):
            return FakeConnectionContext()

    server = SimpleNamespace(state=SimpleNamespace(db_pool=FakePool()))

    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        AsyncMock(return_value=False),
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        AsyncMock(return_value=None),
    )

    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        create_task_mock,
    )

    await reconcile_simple_project_basemap_autostarts(server)

    create_task_mock.assert_not_called()


async def test_reconcile_simple_project_basemap_autostarts_claims_resume_rows(
    monkeypatch,
):
    """Rows with an existing STAC item should use resume-claim before enqueueing."""
    rows = [
        {
            "id": 88,
            "field_mapping_app": FieldMappingApp.QFIELD.value,
            "status": ProjectStatus.PUBLISHED.value,
            "basemap_stac_item_id": "item-88",
            "outline": {"type": "Polygon", "coordinates": []},
        }
    ]

    class FakeCursor:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def execute(self, *_args, **_kwargs):
            return None

        async def fetchall(self):
            return rows

    class FakeConnection:
        def cursor(self, *args, **kwargs):
            return FakeCursor()

    class FakeConnectionContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class FakePool:
        def connection(self):
            return FakeConnectionContext()

    server = SimpleNamespace(state=SimpleNamespace(db_pool=FakePool()))

    claim_generation_mock = AsyncMock(return_value=False)
    claim_resume_mock = AsyncMock(return_value=True)

    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_generation",
        claim_generation_mock,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.claim_simple_project_basemap_resume",
        claim_resume_mock,
    )

    async def fake_autostart(project_id, outline):
        return None

    monkeypatch.setattr(
        "app.htmx.project_create_routes._autostart_basemap_for_simple_project",
        fake_autostart,
    )

    captured_project_ids: list[int] = []

    def fake_create_task(coro):
        captured_project_ids.append(coro.cr_frame.f_locals["project_id"])
        coro.close()
        return Mock()

    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )

    await reconcile_simple_project_basemap_autostarts(server)

    claim_generation_mock.assert_not_awaited()
    claim_resume_mock.assert_awaited_once()
    assert captured_project_ids == [88]


async def test_resume_simple_project_tilepack_if_needed_updates_status(
    monkeypatch,
):
    """Resume helper should refresh status for already-selected STAC items."""
    from app.htmx.project_create_routes import _resume_simple_project_tilepack_if_needed

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
        "app.htmx.project_create_routes.check_tilepack_status",
        check_status_mock,
    )
    monkeypatch.setattr("app.htmx.project_create_routes.DbProject.update", update_mock)

    create_task_mock = Mock()
    monkeypatch.setattr(
        "app.htmx.project_create_routes.asyncio.create_task",
        create_task_mock,
    )

    resumed = await _resume_simple_project_tilepack_if_needed(db, project)

    assert resumed is True
    check_status_mock.assert_awaited_once_with("item-202")
    update_mock.assert_awaited_once()
    update_payload = update_mock.await_args.args[2]
    assert update_payload.basemap_status == "generating"
    assert update_payload.basemap_attach_status == "idle"
    db.commit.assert_awaited_once()
    create_task_mock.assert_not_called()


async def test_resume_simple_project_tilepack_if_needed_starts_attach_when_ready(
    monkeypatch,
):
    """Resume helper should enqueue attach when tilepack is already ready."""
    from app.htmx.project_create_routes import _resume_simple_project_tilepack_if_needed

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
        "app.htmx.project_create_routes.check_tilepack_status",
        check_status_mock,
    )
    monkeypatch.setattr("app.htmx.project_create_routes.DbProject.update", update_mock)

    async def fake_attach(project_id, basemap_url):
        return None

    monkeypatch.setattr(
        "app.htmx.basemap_routes._run_basemap_attach_background",
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
        "app.htmx.project_create_routes.asyncio.create_task",
        fake_create_task,
    )

    resumed = await _resume_simple_project_tilepack_if_needed(db, project)

    assert resumed is True
    check_status_mock.assert_awaited_once_with("item-303")
    update_payload = update_mock.await_args.args[2]
    assert update_payload.basemap_status == "ready"
    assert update_payload.basemap_url == "https://tiles.example/item.mbtiles"
    assert update_payload.basemap_attach_status == "in_progress"
    db.commit.assert_awaited_once()
    assert captured_attach_calls == [(303, "https://tiles.example/item.mbtiles")]


async def test_basemap_autostart_skipped_for_generating_with_existing_stac_item():
    """Generating projects with a selected STAC item should skip duplicate autostart."""
    from app.htmx.project_create_routes import _basemap_autostart_skipped

    project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.QFIELD,
        status=ProjectStatus.PUBLISHED,
        basemap_status="generating",
        basemap_stac_item_id="item-123",
    )

    assert _basemap_autostart_skipped(project) is True


async def test_basemap_autostart_not_skipped_for_generating_without_stac_item():
    """Initial generating state without selected imagery should continue autostart."""
    from app.htmx.project_create_routes import _basemap_autostart_skipped

    project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.QFIELD,
        status=ProjectStatus.PUBLISHED,
        basemap_status="generating",
        basemap_stac_item_id=None,
    )

    assert _basemap_autostart_skipped(project) is False


async def test_project_setup_shows_step1_advanced_config_toggle(client, stub_project):
    """Draft setup should show a basic-first Step 1 with advanced config."""
    response = await client.get(
        f"/projects/{stub_project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Choose Survey Type:" in response.text
    assert "Use Selected Survey Type" not in response.text
    assert "Continue" in response.text
    assert "Advanced Config" in response.text
    assert response.text.index("Default Language:") < response.text.index(
        "Form Options:"
    )


async def test_project_setup_shows_step2_advanced_config_options(client, db, project):
    """Step 2 should expose custom data paths only under advanced config."""
    await DbProject.update(
        db,
        project.id,
        DbProject(xlsform_content=b"test xlsform"),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Download OSM Data" in response.text
    assert "Collect New Data Only" in response.text
    assert "Upload Custom GeoJSON" in response.text
    assert response.text.index("data-advanced-config-toggle") < response.text.index(
        'id="osm-data-status"'
    )


async def test_project_setup_hides_step2_actions_when_data_extract_is_complete(
    client, db, project
):
    """Completed Step 2 should collapse actions and focus user on Step 3."""
    await DbProject.update(
        db,
        project.id,
        DbProject(
            xlsform_content=b"test xlsform",
            data_extract_geojson={"type": "FeatureCollection", "features": []},
        ),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "✓ OSM data extract ready" in response.text
    assert 'id="download-osm-data-btn"' not in response.text
    assert 'id="collect-new-data-btn"' not in response.text
    assert 'id="upload-geojson-btn"' not in response.text
    assert 'id="preview-data-extract-btn"' not in response.text


async def test_collect_new_data_only_htmx_sets_empty_feature_collection(
    client, db, project
):
    """Collect-new-data option should persist an empty FeatureCollection."""
    response = await client.post(
        f"/collect-new-data-only-htmx?project_id={project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("HX-Refresh") == "true"
    assert "Collect-new-data mode selected" in response.text
    assert "Task splitting is skipped" in response.text

    updated_project = await DbProject.one(db, project.id)
    assert updated_project.data_extract_geojson == {
        "type": "FeatureCollection",
        "features": [],
    }
    assert updated_project.task_areas_geojson == {}


async def test_download_osm_data_htmx_returns_requested_no_data_message(monkeypatch):
    """No-feature validation errors should surface the requested OSM no-data copy."""
    project = Mock(id=42)

    async def fake_download_osm_data(**_kwargs):
        raise SvcValidationError(
            "No data found in OSM. Please continue with the Collect New "
            "Data Only option."
        )

    monkeypatch.setattr(
        setup_step_routes,
        "download_osm_data",
        fake_download_osm_data,
    )

    response = await download_osm_data_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "No data found in OSM. Please continue with the Collect New Data Only option."
        in str(response.content)
    )


async def test_upload_geojson_htmx_accepts_multipolygon_with_utf8_tags(monkeypatch):
    """Upload should accept OSM-style GeoJSON properties including UTF-8 tags."""
    uploaded_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [85.3000, 27.7140],
                                [85.3000, 27.7130],
                                [85.3010, 27.7130],
                                [85.3010, 27.7140],
                                [85.3000, 27.7140],
                            ]
                        ]
                    ],
                },
                "properties": {
                    "osm_id": 24691221,
                    "tags": {
                        "name": "पुष्पलाल पथ ;स्वयम्भु मार्ग",
                        "name:en": "Pushpalal Path;Swoyambhu Marg",
                    },
                },
            }
        ],
    }
    uploaded_bytes = json.dumps(uploaded_geojson, ensure_ascii=False).encode("utf-8")
    captured: dict = {}
    project = Mock(id=42)

    def fake_parse_aoi(_db_url, input_geojson, merge=True):
        captured["payload"] = input_geojson
        captured["merge"] = merge
        return uploaded_geojson

    async def fake_check_crs(_featcol):
        return None

    class FakeUploadFile:
        filename = "osm-export.geojson"

        async def read(self):
            return uploaded_bytes

    monkeypatch.setattr(setup_step_routes, "parse_aoi", fake_parse_aoi)
    monkeypatch.setattr(setup_step_routes, "check_crs", fake_check_crs)

    response = await upload_geojson_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        data=FakeUploadFile(),
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("data_extract_preview.html")
    assert response.context["status_variant"] == "success"
    assert (
        "GeoJSON uploaded successfully! Found 1 features."
        in response.context["status_message"]
    )
    assert "Accept Data Extract" in response.context["preview_message"]
    assert captured["payload"] == uploaded_bytes
    assert captured["merge"] is False


async def test_accept_data_extract_htmx_decodes_html_escaped_geojson(monkeypatch):
    """Accept-data route should tolerate HTML-escaped JSON form values."""
    saved: dict = {}
    project = Mock(id=42)
    escaped_geojson = (
        '{&quot;type&quot;: "FeatureCollection", '
        '&quot;features&quot;: [{&quot;type&quot;: "Feature", '
        "&quot;geometry&quot;: null, &quot;properties&quot;: {}}]}"
    )
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": None, "properties": {}}],
    }

    async def fake_save_data_extract(*, db, project_id, geojson_data):
        saved["db"] = db
        saved["project_id"] = project_id
        saved["geojson_data"] = geojson_data
        return len(geojson_data["features"])

    monkeypatch.setattr(
        "app.htmx.setup_step_routes.save_data_extract", fake_save_data_extract
    )

    response = await accept_data_extract_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        data={"data_extract_geojson": escaped_geojson},
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("HX-Refresh") == "true"
    assert saved["project_id"] == project.id
    assert saved["geojson_data"] == feature_collection


async def test_accept_split_htmx_decodes_html_escaped_geojson(monkeypatch):
    """Accept-split route should tolerate HTML-escaped JSON form values."""
    saved: dict = {}
    project = Mock(id=42)
    escaped_geojson = (
        '{&quot;type&quot;: "FeatureCollection", '
        '&quot;features&quot;: [{&quot;type&quot;: "Feature", '
        "&quot;geometry&quot;: null, &quot;properties&quot;: {}}]}"
    )
    tasks_geojson = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": None, "properties": {}}],
    }

    async def fake_save_task_areas(*, db, project_id, tasks_geojson):
        saved["db"] = db
        saved["project_id"] = project_id
        saved["tasks_geojson"] = tasks_geojson
        return len(tasks_geojson["features"])

    monkeypatch.setattr(
        "app.htmx.setup_step_routes.save_task_areas", fake_save_task_areas
    )

    response = await accept_split_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        data={"tasks_geojson": escaped_geojson},
        project_id=project.id,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("HX-Refresh") == "true"
    assert saved["project_id"] == project.id
    assert saved["tasks_geojson"] == tasks_geojson


def test_task_boundaries_layer_uses_translated_popup_labels():
    """Task boundary popups should show translated labels without layer name."""
    layer = _task_boundaries_layer(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {"task_id": 3, "building_count": 14},
                }
            ],
        }
    )

    assert layer["popup_options"]["showLayerName"] is False
    assert layer["popup_options"]["propertyLabels"] == {
        "task_id": "Task ID",
        "building_count": "Building Count",
    }
    assert layer["popup_options"]["propertyOrder"] == ["task_id", "building_count"]


def test_render_leaflet_map_serializes_popup_options():
    """Leaflet helper should pass popup configuration through to the frontend."""
    html = render_leaflet_map(
        map_id="leaflet-map-test",
        geojson_layers=[
            {
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": None,
                            "properties": {"task_id": 3, "building_count": 14},
                        }
                    ],
                },
                "name": "Task Boundaries (1 tasks)",
                "popup_options": {
                    "showLayerName": False,
                    "propertyLabels": {
                        "task_id": "Task ID",
                        "building_count": "Building Count",
                    },
                    "propertyOrder": ["task_id", "building_count"],
                },
            }
        ],
    )

    assert '"showLayerName": false' in html
    assert '"task_id": "Task ID"' in html
    assert '"building_count": "Building Count"' in html
    assert '"propertyOrder": ["task_id", "building_count"]' in html


async def test_project_details_shows_odk_media_upload_guidance(client, db, project):
    """Published ODK projects should show guidance for form media uploads."""
    await DbProject.update(
        db,
        project.id,
        DbProject(
            status=ProjectStatus.PUBLISHED,
            external_project_instance_url="https://central.example.org",
            external_project_id=17,
        ),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "View Project in ODK Central" in response.text
    assert (
        "If you need to upload additional media files to this project" in response.text
    )
    assert "log into ODK Central and upload them in the form settings." in response.text


async def test_project_qrcode_htmx(client, project):
    """Test QR code generation via HTMX."""
    # Mock get_project_qrcode to avoid calling ODK/QField
    with patch(
        "app.projects.project_crud.get_project_qrcode", new_callable=AsyncMock
    ) as mock_get_qrcode:
        mock_get_qrcode.return_value = "data:image/png;base64,mocked_qr_code"

        response = await client.get(
            f"/project-qrcode-htmx?project_id={project.id}",
            headers={"HX-Request": "true"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "data:image/png;base64,mocked_qr_code" in response.text
        assert "Scan QR Code" in response.text

        mock_get_qrcode.assert_called_once()
        # Simple call check is a good start for integration test


async def test_project_qrcode_htmx_not_found(client):
    """Test QR code generation for non-existent project."""
    response = await client.get(
        "/project-qrcode-htmx?project_id=999999", headers={"HX-Request": "true"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_metrics_partial(client):
    """Test landing metrics partial route."""
    response = await client.get("/metrics", headers={"HX-Request": "true"})
    assert response.status_code == status.HTTP_200_OK
    assert "Projects Created" in response.text
    assert "Features Surveyed" in response.text


async def test_project_listing_renders_cards_and_component_bootstrap(
    client, db, project
):
    """Project listing renders saved projects, location, and WA components."""
    await DbProject.update(
        db,
        project.id,
        DbProject(location_str="Nairobi, Kenya"),
    )
    await db.commit()

    response = await client.get("/projects", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert project.project_name in response.text
    assert f"/projects/{project.id}" in response.text
    assert "Location: Nairobi, Kenya" in response.text
    assert "Project Status" in response.text
    assert "Sort By" in response.text
    assert 'id="projects-search"' in response.text
    assert (
        'rel="stylesheet"\n      href="https://fonts.googleapis.com/css2?family=Archivo'
    ) in response.text
    assert "@awesome.me/webawesome/dist/components/card/card.js" in response.text


async def test_project_listing_shows_empty_state_when_no_projects(client):
    """Project listing should show the empty-state copy when no projects exist."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_projects:
        mock_projects.return_value = []

        response = await client.get("/projects", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert (
        "No projects found. Create your first project to get started!" in response.text
    )


def test_landing_template_renders_locale_selector():
    """Landing template should render the locale selector in the existing footer."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
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

    template = env.get_template("landing.html")
    rendered = template.render(create_project_href="/new")

    assert 'data-locale-switch="en"' in rendered
    assert 'data-locale-switch="pt"' in rendered
    assert 'data-locale-switch="pt_br"' in rendered
    assert "<wa-dropdown>" in rendered
    assert "landing-footer-social" in rendered
    assert "Field Tasking Manager" in rendered
    assert "FIELD TASKING MANAGER" not in rendered


async def test_project_listing_filters_by_status():
    """Project listing should pass a valid status filter through to the data layer."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_projects:
        mock_projects.return_value = []

        response = await project_listing.fn(
            request=Mock(query_params={"status": "COMPLETED"}),
            db=Mock(),
            auth_user=Mock(),
        )

    assert response.template_name == "home.html"
    mock_projects.assert_awaited_once()
    assert mock_projects.await_args.kwargs["status"] == ProjectStatus.COMPLETED


async def test_project_listing_passes_search_and_sort_filters():
    """Project listing should pass search and sort choices through to the data layer."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_projects:
        mock_projects.return_value = []

        response = await project_listing.fn(
            request=Mock(
                query_params={
                    "status": "COMPLETED",
                    "sort": "name_asc",
                    "search": "health",
                }
            ),
            db=Mock(),
            auth_user=Mock(),
        )

    assert response.template_name == "home.html"
    mock_projects.assert_awaited_once()
    assert mock_projects.await_args.kwargs["status"] == ProjectStatus.COMPLETED
    assert mock_projects.await_args.kwargs["sort_by"] == "name_asc"
    assert mock_projects.await_args.kwargs["search"] == "health"


async def test_project_listing_preserves_search_and_sort_selection():
    """Project listing should keep selected toolbar values in template context."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_projects:
        mock_projects.return_value = []

        response = await project_listing.fn(
            request=Mock(query_params={"sort": "name_desc", "search": "roads"}),
            db=Mock(),
            auth_user=Mock(),
        )

    assert response.template_name == "home.html"
    assert response.context["selected_sort"] == "name_desc"
    assert response.context["search_query"] == "roads"


async def test_project_listing_guests_get_login_create_href(monkeypatch):
    """Guests should be prompted to log in before entering project creation."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_projects:
        mock_projects.return_value = []
        response = await project_listing.fn(
            request=Mock(query_params={}),
            db=Mock(),
            auth_user=None,
        )

    assert response.context["create_project_href"] == "/login?return_to=%2Fnew"


async def test_new_project_redirects_guests_to_login(monkeypatch):
    """The new-project page should redirect unauthenticated guests to login."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new"
    request.headers = {}

    response = await new_project.fn(request=request, db=Mock(), auth_user=None)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == "/login?return_to=%2Fnew"


async def test_new_project_simple_redirects_guests_to_login(monkeypatch):
    """The simple new-project page should redirect unauthenticated guests."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "AUTH_PROVIDER", AuthProvider.BUNDLED)

    request = Mock()
    request.url.path = "/new/simple"
    request.headers = {}

    response = await new_project_simple.fn(
        request=request,
        db=Mock(),
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

    response = await new_project.fn(request=request, db=Mock(), auth_user=None)

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
        db=Mock(),
        auth_user=None,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["HX-Redirect"] == "/login?return_to=%2Fnew%2Fsimple"


async def test_new_project_page_renders_simple_cta(client):
    """Standard create page should link directly to simple page."""
    response = await client.get("/new", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert 'href="/new/simple"' in response.text
    assert "Create Project" in response.text


async def test_new_project_and_simple_share_map_ids(client):
    """Both new-project pages should expose shared map element contracts."""
    standard_response = await client.get("/new", headers={"HX-Request": "true"})
    simple_response = await client.get("/new/simple", headers={"HX-Request": "true"})

    assert standard_response.status_code == status.HTTP_200_OK
    assert simple_response.status_code == status.HTTP_200_OK

    assert 'id="map"' in standard_response.text
    assert 'id="outline-geojson"' in standard_response.text
    assert 'id="map"' in simple_response.text
    assert 'id="outline-geojson"' in simple_response.text


def test_new_project_simple_template_has_submit_loading_indicator():
    """Simple template should include HTMX submit loading indicator markup."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
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


def test_new_project_simple_template_uses_gettext_for_map_strings():
    """Simple template should route map-script strings through gettext."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.add_extension("jinja2.ext.i18n")

    translations = {
        "Create Project": "Crear proyecto",
        "Back to Standard Form": "Volver al formulario estandar",
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
    assert "Volver al formulario estandar" in rendered
    assert "Creando proyecto y preparando mapa..." in rendered
    assert '"Superficie"' in rendered
    assert '"Geometria invalida"' in rendered
    assert '"Deshacer ultimo vertice"' in rendered
    assert '"Mi ubicacion"' in rendered
    assert '"No se pudo validar GeoJSON"' in rendered
    assert '"La validacion no devolvio GeoJSON"' in rendered


async def test_static_landing_image_served(client):
    """Test static landing JPG assets are served."""
    response = await client.get("/static/images/landing-bg.jpg")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-type", "").startswith("image/jpeg")


async def test_static_image_rejects_unsupported_extension(client):
    """Test static image route blocks unsupported extensions."""
    response = await client.get("/static/images/not-allowed.gif")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_build_odk_finalize_success_html_includes_manager_credentials():
    """ODK finalize helper should return template context with manager credentials."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@example.org",
        manager_password="StrongPass123!",
    )

    response_template = _build_odk_finalize_success_html(result)

    assert response_template.template_name.endswith("finalize_success_odk.html")
    assert response_template.context["result"].manager_username == (
        "field-tm-manager@example.org"
    )
    assert response_template.context["result"].manager_password == "StrongPass123!"


def test_build_odk_finalize_success_html_does_not_render_qr_markup():
    """ODK finalize helper should use ODK success fragment, not QField QR fragment."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@example.org",
        manager_password="StrongPass123!",
    )

    response_template = _build_odk_finalize_success_html(result)

    assert response_template.template_name.endswith("finalize_success_odk.html")
    assert not response_template.template_name.endswith("finalize_success_qfield.html")


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
        "app.htmx.project_create_routes._resolve_uploaded_xlsform_bytes",
        fake_resolve_uploaded_xlsform_bytes,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
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
        "app.htmx.project_create_routes._resolve_uploaded_xlsform_bytes",
        fake_resolve_uploaded_xlsform_bytes,
    )
    monkeypatch.setattr(
        "app.htmx.project_create_routes.process_xlsform",
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


def test_build_finalize_error_html_prefers_friendly_text_for_plain_errors():
    """Plain-text errors should remain user-facing and include raw details."""
    response_template = _build_finalize_error_html("Could not connect to ODK Central.")

    assert response_template.template_name.endswith("finalize_error.html")
    assert (
        response_template.context["user_message"] == "Could not connect to ODK Central."
    )
    assert (
        response_template.context["technical_details"]
        == "Could not connect to ODK Central."
    )


def test_build_finalize_error_html_uses_generic_text_for_json_payload():
    """Structured payloads should show a generic user-facing message."""
    response_template = _build_finalize_error_html(
        '{"detail":"{"error":"invalid credentials"}"}'
    )

    assert response_template.template_name.endswith("finalize_error.html")
    assert "Project finalisation failed." in response_template.context["user_message"]
    assert '"detail"' in response_template.context["technical_details"]
