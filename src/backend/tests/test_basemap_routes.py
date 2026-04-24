"""Route-level tests for basemap HTMX endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.db.enums import FieldMappingApp, ProjectStatus
from app.htmx import basemap_routes


def _render_template(template_name: str, context: dict) -> str:
    """Render a backend template with minimal globals for route-level assertions."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.add_extension("jinja2.ext.i18n")
    env.install_gettext_callables(
        lambda message: message, lambda s, p, n: s if n == 1 else p
    )

    render_context = {
        "_": lambda message: message,
        "current_locale": lambda: "en",
        "supported_locales": ["en"],
        "locale_labels": {"en": "English"},
        "current_dir": lambda: "ltr",
        **context,
    }

    return env.get_template(template_name).render(**render_context)


def test_basemap_ready_fragment_hides_metadata_and_attach_for_odk_projects():
    """Ready fragment should keep ODK mode free of metadata and attach actions."""
    project = Mock(
        id=44,
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status="idle",
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_ready.html",
        {
            "project": project,
            "is_qfield": False,
            "is_odk": True,
            "basemap_metadata_url": "https://api.imagery.hotosm.org/browser/external/"
            "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-44",
            "basemap_size_display": "2.0 MB",
            "basemap_zoom_display": "9-17",
        },
    )

    assert "Download MBTiles" in html
    assert "View Metadata" not in html
    assert "Attach to QField Project" not in html


def test_basemap_progress_fragment_uses_manual_status_check_only():
    """Progress fragment should not auto-poll and must expose a manual check button."""
    project = Mock(
        id=55, basemap_stac_item_id="item-manual", basemap_status="generating"
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_progress.html",
        {
            "project": project,
            "progress_scope": None,
            "is_initially_processing": True,
            "basemap_size_bytes": 1048576,
            "basemap_minzoom": 10,
            "basemap_maxzoom": 16,
            "basemap_zoom_display": "10-16",
        },
    )

    assert "Status updates automatically every few seconds." not in html
    assert (
        "Basemap generation is in progress. "
        "Use the button below to check the latest status." in html
    )
    assert 'hx-trigger="load delay:3s"' not in html
    assert html.count('hx-get="/projects/55/basemap/status"') == 1
    assert 'hx-disabled-elt="this"' in html
    compact_html = " ".join(html.split())
    assert 'class="js-basemap-check-text"' in compact_html
    assert "Checking..." in compact_html
    assert 'js-basemap-spinner" style="display: inline-flex;' in compact_html


def test_basemap_attach_progress_fragment_shows_initial_processing_state():
    """Attach progress should render active processing markers on first load."""
    project = Mock(id=56, basemap_attach_status="in_progress")
    html = _render_template(
        "partials/project_details/fragments/basemap_progress.html",
        {
            "project": project,
            "progress_scope": "attach",
            "is_initially_processing": True,
        },
    )

    assert (
        "Basemap attach is in progress. "
        "Use the button below to check the latest status." in html
    )
    assert 'hx-trigger="load delay:3s"' not in html
    assert html.count('hx-get="/projects/56/basemap/attach-status"') == 1
    compact_html = " ".join(html.split())
    assert 'class="js-basemap-check-text"' in compact_html
    assert "Checking..." in compact_html
    assert 'js-basemap-spinner" style="display: inline-flex;' in compact_html


def test_basemap_attach_progress_fragment_shows_warning_and_retry_on_failed_attach():
    """Failed attach should be non-blocking with warning semantics and retry action."""
    project = Mock(
        id=57,
        basemap_attach_status="failed",
        basemap_attach_error=(
            "Basemap attach failed for now. "
            "Your project is ready to use. Please retry attach."
        ),
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_progress.html",
        {
            "project": project,
            "progress_scope": "attach",
            "is_initially_processing": False,
        },
    )

    assert 'variant="warning"' in html
    assert "Your project is ready to use" in html
    assert "Retry Attach" in html
    assert 'hx-post="/projects/57/basemap/attach"' in html


def test_attach_error_text_classifies_transient_network_failures():
    """Transient network failures should return retry-oriented non-blocking copy."""
    message = basemap_routes._attach_error_text(
        RuntimeError("Temporary failure in name resolution from remote host")
    )

    assert "temporary network issue" in message
    assert "Your project is ready to use" in message


def test_attach_error_text_keeps_generic_fallback_for_unknown_failures():
    """Unknown failures should keep a safe generic attach failure message."""
    message = basemap_routes._attach_error_text(RuntimeError("wrapper failure"))

    assert (
        message == "Basemap attach failed for now. Your project is ready to use. "
        "Please retry attach."
    )


async def test_basemap_search_requires_project_context():
    """Search should return 404 when the current project context is missing."""
    response = await basemap_routes.basemap_search_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": None},
        auth_user=Mock(),
        project_id=123,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_basemap_search_results_render_item_metadata_link():
    """Search results should render a metadata link for each imagery item."""
    html = _render_template(
        "partials/project_details/fragments/basemap_search_results.html",
        {
            "project": Mock(id=99),
            "items": [
                {
                    "id": "item-xyz",
                    "datetime": None,
                    "platform": None,
                    "cloud_cover": None,
                    "minzoom": None,
                    "maxzoom": None,
                    "mbtiles_size_bytes": None,
                }
            ],
            "metadata_url_template": basemap_routes.METADATA_BROWSER_URL_TEMPLATE,
        },
    )

    assert "Use this image" in html
    assert "View Metadata" in html
    assert (
        "https://api.imagery.hotosm.org/browser/external/"
        "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-xyz" in html
    )


def test_basemap_ready_fragment_shows_action_triad_when_not_attached():
    """Ready fragment should show download, metadata, and attach actions."""
    project = Mock(
        id=42,
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status="idle",
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_ready.html",
        {
            "project": project,
            "is_qfield": True,
            "is_odk": False,
            "basemap_metadata_url": "https://api.imagery.hotosm.org/browser/external/"
            "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-42",
            "basemap_size_display": "2.0 MB",
            "basemap_zoom_display": "9-17",
        },
    )

    assert "Download MBTiles" in html
    assert "View Metadata" in html
    assert "Attach to QField Project" in html
    compact_html = " ".join(html.split())
    assert "Basemap is ready. Not yet attached to QField project." in compact_html


def test_basemap_ready_fragment_shows_attach_in_progress_message_when_disabled():
    """Ready fragment should explain disabled attach button while attach is running."""
    project = Mock(
        id=44,
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status="in_progress",
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_ready.html",
        {
            "project": project,
            "is_qfield": True,
            "is_odk": False,
            "basemap_metadata_url": "https://api.imagery.hotosm.org/browser/external/"
            "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-44",
            "basemap_size_display": "2.0 MB",
            "basemap_zoom_display": "9-17",
        },
    )

    compact_html = " ".join(html.split())
    assert "Basemap is ready. Attaching to QField project in progress." in compact_html
    assert "Attach to QField Project" in html
    assert 'disabled="disabled"' in html


def test_basemap_ready_fragment_shows_download_only_when_attached():
    """Ready fragment should lock to download-only once attach is ready."""
    project = Mock(
        id=43,
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status="ready",
    )
    html = _render_template(
        "partials/project_details/fragments/basemap_ready.html",
        {
            "project": project,
            "is_qfield": True,
            "is_odk": False,
            "basemap_metadata_url": "https://api.imagery.hotosm.org/browser/external/"
            "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-43",
            "basemap_size_display": "2.0 MB",
            "basemap_zoom_display": "9-17",
        },
    )

    assert "Download MBTiles" in html
    assert "View Metadata" not in html
    assert "Attach to QField Project" not in html
    compact_html = " ".join(html.split())
    assert "Basemap attached to QField project." in compact_html
    assert "Basemap is ready." not in html


async def test_basemap_search_requires_published_project():
    """Search should reject projects that have not been published yet."""
    project = Mock(id=7, status=ProjectStatus.DRAFT)

    response = await basemap_routes.basemap_search_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=7,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_search_success(monkeypatch):
    """Search should render matching imagery results for a published project."""
    project = Mock(
        id=11,
        status=ProjectStatus.PUBLISHED,
        outline={
            "type": "Polygon",
            "coordinates": [
                [
                    [85.0, 27.0],
                    [85.0, 28.0],
                    [86.0, 28.0],
                    [86.0, 27.0],
                    [85.0, 27.0],
                ]
            ],
        },
        field_mapping_app=FieldMappingApp.QFIELD,
    )
    refreshed_project = Mock(field_mapping_app=FieldMappingApp.QFIELD)
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes, "search_oam_imagery", AsyncMock(return_value=[{"id": "x"}])
    )
    update_mock = AsyncMock()
    one_mock = AsyncMock(return_value=refreshed_project)
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(basemap_routes.DbProject, "one", one_mock)

    response = await basemap_routes.basemap_search_htmx.fn(
        request=Mock(),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=11,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_search_results.html")
    assert response.context["items"] == [{"id": "x"}]
    assert (
        response.context["metadata_url_template"]
        == basemap_routes.METADATA_BROWSER_URL_TEMPLATE
    )
    update_mock.assert_awaited_once()
    db.commit.assert_awaited_once()


async def test_basemap_search_returns_sanitized_error_when_search_fails(monkeypatch):
    """Search failures should return a safe inline fragment, not raise NameError."""
    project = Mock(
        id=12,
        status=ProjectStatus.PUBLISHED,
        outline={
            "type": "Polygon",
            "coordinates": [
                [
                    [85.0, 27.0],
                    [85.0, 28.0],
                    [86.0, 28.0],
                    [86.0, 27.0],
                    [85.0, 27.0],
                ]
            ],
        },
        field_mapping_app=FieldMappingApp.QFIELD,
    )

    monkeypatch.setattr(
        basemap_routes,
        "search_oam_imagery",
        AsyncMock(side_effect=RuntimeError("imagery backend unavailable")),
    )

    response = await basemap_routes.basemap_search_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=12,
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to search imagery right now" in str(response.content)
    assert "imagery backend unavailable" not in str(response.content)


async def test_basemap_generate_returns_ready_fragment(monkeypatch):
    """Generation should return the ready fragment when tilepack is immediate."""
    project = Mock(id=14, basemap_stac_item_id=None, basemap_status=None)
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_stac_item_id="item-a",
        basemap_minzoom=None,
        basemap_maxzoom=None,
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "trigger_tilepack_generation",
        AsyncMock(return_value=("ready", "https://tiles/ready.mbtiles")),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    request = Mock(
        query_params={
            "mbtiles_size_bytes": "2097152",
            "mbtiles_minzoom": "9",
            "mbtiles_maxzoom": "17",
        }
    )

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=request,
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=14,
        stac_item_id="item-a",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_ready.html")
    assert response.context["basemap_size_display"] == "2.0 MB"
    assert response.context["basemap_zoom_display"] == "9-17"
    assert (
        response.context["basemap_metadata_url"]
        == "https://api.imagery.hotosm.org/browser/external/"
        "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item-a"
    )
    assert update_mock.await_count == 2


async def test_basemap_generate_returns_progress_fragment(monkeypatch):
    """Generation should return progress when the tilepack is still pending."""
    project = Mock(id=15, basemap_stac_item_id=None, basemap_status=None)
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=None,
        basemap_maxzoom=None,
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "trigger_tilepack_generation",
        AsyncMock(return_value=("generating", None)),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", AsyncMock())
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    request = Mock(
        query_params={
            "mbtiles_size_bytes": "5242880",
            "mbtiles_minzoom": "10",
            "mbtiles_maxzoom": "16",
        }
    )

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=request,
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=15,
        stac_item_id="item-b",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["basemap_size_bytes"] == 5242880
    assert response.context["basemap_zoom_display"] == "10-16"


async def test_basemap_generate_repeat_request_is_idempotent_when_generating(
    monkeypatch,
):
    """Generation retry should be idempotent while the same item is generating."""
    project = Mock(id=33, basemap_stac_item_id="item-z", basemap_status="generating")
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=11,
        basemap_maxzoom=15,
    )

    trigger_mock = AsyncMock()
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes, "trigger_tilepack_generation", trigger_mock)
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=Mock(query_params={"mbtiles_size_bytes": "1024"}),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=33,
        stac_item_id="item-z",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    trigger_mock.assert_not_awaited()
    update_mock.assert_not_awaited()


async def test_basemap_generate_repeat_request_is_idempotent_when_ready(monkeypatch):
    """Generation retry should be idempotent after the same item is ready."""
    project = Mock(id=34, basemap_stac_item_id="item-r", basemap_status="ready")
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=8,
        basemap_maxzoom=17,
    )

    trigger_mock = AsyncMock()
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes, "trigger_tilepack_generation", trigger_mock)
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=Mock(query_params={"mbtiles_size_bytes": "2048"}),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=34,
        stac_item_id="item-r",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_ready.html")
    trigger_mock.assert_not_awaited()
    update_mock.assert_not_awaited()


async def test_basemap_generate_new_item_clears_stale_fields(monkeypatch):
    """Generation should clear stale basemap state when selecting a new item."""
    project = Mock(id=35, basemap_stac_item_id="item-old", basemap_status="ready")
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=None,
        basemap_maxzoom=None,
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "trigger_tilepack_generation",
        AsyncMock(return_value=("generating", None)),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=Mock(query_params={}),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=35,
        stac_item_id="item-new",
    )

    assert response.status_code == status.HTTP_200_OK
    first_update = update_mock.await_args_list[0].args[2]
    assert first_update.basemap_stac_item_id == "item-new"
    assert first_update.basemap_url is None
    assert first_update.basemap_status == "generating"
    assert first_update.basemap_minzoom is None
    assert first_update.basemap_maxzoom is None
    assert first_update.basemap_attach_status == "idle"
    assert first_update.basemap_attach_error is None
    assert first_update.basemap_attach_updated_at is None


async def test_basemap_status_requires_active_stac_item():
    """Status polling should reject requests when no item is being tracked."""
    project = Mock(id=16, basemap_stac_item_id=None)

    response = await basemap_routes.basemap_status_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=16,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_generate_marks_failed_on_exception(monkeypatch):
    """Generation should mark the basemap as failed after an unexpected error."""
    project = Mock(id=36, basemap_stac_item_id=None, basemap_status=None)
    db = Mock()
    db.commit = AsyncMock()
    update_mock = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "trigger_tilepack_generation",
        AsyncMock(side_effect=RuntimeError("backend boom")),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    response = await basemap_routes.basemap_generate_htmx.fn(
        request=Mock(query_params={}),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=36,
        stac_item_id="item-fail",
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "backend boom" not in str(response.content)
    assert update_mock.await_count == 2
    assert update_mock.await_args_list[-1].args[2].basemap_status == "failed"
    db.commit.assert_awaited_once()


async def test_basemap_status_transitions_to_ready(monkeypatch):
    """Status polling should transition the project to a ready basemap."""
    project = Mock(id=17, basemap_stac_item_id="item", basemap_url=None)
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_stac_item_id="item",
        basemap_minzoom=None,
        basemap_maxzoom=None,
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "check_tilepack_status",
        AsyncMock(return_value=("ready", "https://tiles/ready.mbtiles")),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", AsyncMock())
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    request = Mock(
        query_params={
            "mbtiles_size_bytes": "3145728",
            "mbtiles_minzoom": "11",
            "mbtiles_maxzoom": "18",
        }
    )

    response = await basemap_routes.basemap_status_htmx.fn(
        request=request,
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=17,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_ready.html")
    assert response.context["basemap_size_display"] == "3.0 MB"
    assert response.context["basemap_zoom_display"] == "11-18"
    assert (
        response.context["basemap_metadata_url"]
        == "https://api.imagery.hotosm.org/browser/external/"
        "api.imagery.hotosm.org/stac/collections/openaerialmap/items/item"
    )


async def test_basemap_status_progress_preserves_size_context(monkeypatch):
    """Status polling should preserve size and zoom context while generating."""
    project = Mock(id=19, basemap_stac_item_id="item", basemap_url=None)
    refreshed_project = Mock(
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=None,
        basemap_maxzoom=None,
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "check_tilepack_status",
        AsyncMock(return_value=("generating", None)),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", AsyncMock())
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_status_htmx.fn(
        request=Mock(
            query_params={
                "mbtiles_size_bytes": "1048576",
                "mbtiles_minzoom": "12",
                "mbtiles_maxzoom": "15",
            }
        ),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=19,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["basemap_size_bytes"] == 1048576
    assert response.context["basemap_zoom_display"] == "12-15"


async def test_basemap_status_marks_failed_on_exception(monkeypatch):
    """Status polling should return a clean error for non-generating failures."""
    project = Mock(
        id=18,
        basemap_stac_item_id="item",
        basemap_url=None,
        basemap_status="ready",
    )
    db = Mock()
    db.commit = AsyncMock()
    update_mock = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "check_tilepack_status",
        AsyncMock(side_effect=RuntimeError("upstream failed")),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    response = await basemap_routes.basemap_status_htmx.fn(
        request=Mock(),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=18,
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "upstream failed" not in str(response.content)
    update_mock.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_basemap_status_preserves_generating_state_on_status_refresh_failure(
    monkeypatch,
):
    """Status refresh failures should keep generating UI/state for in-progress items."""
    project = Mock(
        id=181,
        basemap_stac_item_id="item",
        basemap_url=None,
        basemap_status="generating",
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_minzoom=12,
        basemap_maxzoom=15,
    )
    db = Mock()
    db.commit = AsyncMock()
    update_mock = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "check_tilepack_status",
        AsyncMock(side_effect=RuntimeError("bad upstream payload")),
    )
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    response = await basemap_routes.basemap_status_htmx.fn(
        request=Mock(query_params={"mbtiles_size_bytes": "1048576"}),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=181,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["is_initially_processing"] is True
    assert response.context["basemap_size_bytes"] == 1048576
    update_mock.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_basemap_attach_requires_published_project():
    """Attach should reject projects that are not published."""
    project = Mock(
        id=21,
        status=ProjectStatus.DRAFT,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="ready",
        basemap_url="https://tiles/ready.mbtiles",
    )

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=21,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_attach_requires_qfield_project():
    """Attach should reject projects that are not QField-based."""
    project = Mock(
        id=22,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.ODK,
        basemap_status="ready",
        basemap_url="https://tiles/ready.mbtiles",
    )

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=22,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_attach_requires_ready_status():
    """Attach should reject basemaps that have not finished generating."""
    project = Mock(
        id=23,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="generating",
        basemap_url="https://tiles/pending.mbtiles",
    )

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=23,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_attach_requires_download_url():
    """Attach should reject ready basemaps that do not have a download URL."""
    project = Mock(
        id=24,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="ready",
        basemap_url=None,
    )

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=24,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_basemap_attach_missing_config_returns_clean_error(monkeypatch):
    """Attach should return a sanitized error when deployment config is missing."""
    project = Mock(
        id=25,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="ready",
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status=None,
    )

    monkeypatch.setattr(
        basemap_routes,
        "get_missing_basemap_attach_config",
        Mock(return_value=["QFIELDCLOUD_URL"]),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=25,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "QFIELDCLOUD_URL" in str(response.content)
    update_mock.assert_not_awaited()


async def test_basemap_attach_first_click_returns_in_progress(monkeypatch):
    """Attach should enqueue background work and return progress on first click."""
    project = Mock(
        id=26,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="ready",
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status=None,
    )
    refreshed_project = Mock(
        id=26,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_attach_status="in_progress",
    )
    db = Mock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        basemap_routes,
        "get_missing_basemap_attach_config",
        Mock(return_value=[]),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    captured_coro = None

    def _capture_task(coro):
        nonlocal captured_coro
        captured_coro = coro
        coro.close()
        return Mock()

    monkeypatch.setattr(basemap_routes.asyncio, "create_task", _capture_task)

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=db,
        current_user={"project": project},
        auth_user=Mock(),
        project_id=26,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["progress_scope"] == "attach"
    assert captured_coro is not None
    assert update_mock.await_count == 1
    db.commit.assert_awaited_once()


async def test_basemap_attach_repeat_click_is_idempotent_in_progress(monkeypatch):
    """Attach retry should be idempotent while a background job is in progress."""
    project = Mock(
        id=27,
        status=ProjectStatus.PUBLISHED,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_status="ready",
        basemap_url="https://tiles/ready.mbtiles",
        basemap_attach_status="in_progress",
    )

    monkeypatch.setattr(
        basemap_routes,
        "get_missing_basemap_attach_config",
        Mock(return_value=[]),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)
    create_task_mock = Mock()
    monkeypatch.setattr(basemap_routes.asyncio, "create_task", create_task_mock)

    response = await basemap_routes.basemap_attach_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=27,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["progress_scope"] == "attach"
    update_mock.assert_not_awaited()
    create_task_mock.assert_not_called()


async def test_basemap_attach_status_returns_progress_when_in_progress(monkeypatch):
    """Attach status should render progress while the background job runs."""
    project = Mock(id=28)
    refreshed_project = Mock(
        id=28,
        field_mapping_app=FieldMappingApp.QFIELD,
        basemap_attach_status="in_progress",
    )

    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_attach_status_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=28,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.template_name.endswith("basemap_progress.html")
    assert response.context["progress_scope"] == "attach"


async def test_basemap_attach_status_returns_success_when_ready(monkeypatch):
    """Attach status should render success after the basemap is attached."""
    project = Mock(id=29)
    refreshed_project = Mock(id=29, basemap_attach_status="ready")

    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=refreshed_project)
    )

    response = await basemap_routes.basemap_attach_status_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=29,
    )

    assert response.status_code == status.HTTP_200_OK
    assert "successfully" in str(response.content)


async def test_run_basemap_attach_background_marks_ready(monkeypatch):
    """Background attach should persist the ready state after success."""
    project = Mock(id=30)
    db = Mock()
    db.commit = AsyncMock()

    class _ConnCtx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _connect(_):
        return _ConnCtx()

    monkeypatch.setattr(basemap_routes.AsyncConnection, "connect", _connect)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS", 0)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS", 1)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=project)
    )
    attach_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes, "attach_basemap_to_qfield_project", attach_mock)
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    await basemap_routes._run_basemap_attach_background(
        30, "https://tiles/ready.mbtiles"
    )

    attach_mock.assert_awaited_once_with(db, project, "https://tiles/ready.mbtiles")
    assert update_mock.await_count == 1
    project_update = update_mock.await_args.args[2]
    assert project_update.basemap_attach_status == "ready"
    assert project_update.basemap_attach_error is None
    db.commit.assert_awaited_once()


async def test_run_basemap_attach_background_retries_once_for_transient_failure(
    monkeypatch,
):
    """Background attach should retry once for transient failures then succeed."""
    project = Mock(id=32)
    db = Mock()
    db.commit = AsyncMock()

    class _ConnCtx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _connect(_):
        return _ConnCtx()

    attach_mock = AsyncMock(
        side_effect=[RuntimeError("Connection reset by peer"), None]
    )

    monkeypatch.setattr(basemap_routes.AsyncConnection, "connect", _connect)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS", 0)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS", 1)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=project)
    )
    monkeypatch.setattr(basemap_routes, "attach_basemap_to_qfield_project", attach_mock)
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    await basemap_routes._run_basemap_attach_background(
        32, "https://tiles/ready.mbtiles"
    )

    assert attach_mock.await_count == 2
    assert update_mock.await_count == 1
    project_update = update_mock.await_args.args[2]
    assert project_update.basemap_attach_status == "ready"
    assert project_update.basemap_attach_error is None
    db.commit.assert_awaited_once()


async def test_run_basemap_attach_background_marks_failed_with_error(monkeypatch):
    """Background attach should persist a sanitized failure message on error."""
    project = Mock(id=31)
    db = Mock()
    db.commit = AsyncMock()

    class _ConnCtx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _connect(_):
        return _ConnCtx()

    monkeypatch.setattr(basemap_routes.AsyncConnection, "connect", _connect)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_INITIAL_DELAY_SECONDS", 0)
    monkeypatch.setattr(basemap_routes, "AUTOSTART_ATTACH_MAX_RETRY_ATTEMPTS", 1)
    monkeypatch.setattr(
        basemap_routes.DbProject, "one", AsyncMock(return_value=project)
    )
    attach_mock = AsyncMock(side_effect=RuntimeError("wrapper failure"))
    monkeypatch.setattr(
        basemap_routes,
        "attach_basemap_to_qfield_project",
        attach_mock,
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(basemap_routes.DbProject, "update", update_mock)

    await basemap_routes._run_basemap_attach_background(
        31, "https://tiles/ready.mbtiles"
    )

    attach_mock.assert_awaited_once_with(db, project, "https://tiles/ready.mbtiles")
    assert update_mock.await_count == 1
    project_update = update_mock.await_args.args[2]
    assert project_update.basemap_attach_status == "failed"
    assert project_update.basemap_attach_error == (
        "Basemap attach failed for now. Your project is ready to use. "
        "Please retry attach."
    )
    db.commit.assert_awaited_once()
