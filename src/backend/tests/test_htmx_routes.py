"""Tests for HTMX routes."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.config import AuthProvider, settings
from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.htmx.project_create_routes import _parse_outline_payload, new_project
from app.htmx.project_list_routes import project_listing
from app.htmx.setup_step_routes import (
    _build_finalize_error_html,
    _build_odk_finalize_success_html,
)
from app.projects.project_services import ODKFinalizeResult

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


async def test_create_project_htmx_returns_inline_error_for_missing_mapping_app(
    client, stub_project_data
):
    """Missing required app should return 400 with an inline HTML error fragment."""
    payload = dict(stub_project_data)
    payload["field_mapping_app"] = ""

    response = await client.post(
        "/projects/create",
        data=payload,
        headers={"HX-Request": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Field Mapping App is required." in response.text


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


async def test_upload_geojson_htmx_accepts_multipolygon_with_utf8_tags(monkeypatch):
    """Upload should accept OSM-style GeoJSON properties including UTF-8 tags."""
    from app.htmx import setup_step_routes
    from app.htmx.setup_step_routes import upload_geojson_htmx

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
    assert "GeoJSON uploaded successfully! Found 1 features." in response.content
    assert "Accept Data Extract" in response.content
    assert captured["payload"] == uploaded_bytes
    assert captured["merge"] is False


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


def test_project_listing_template_renders_project_location():
    """Project cards should display the location text when available."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("home.html")

    html = template.render(
        projects=[
            {
                "id": 7,
                "project_name": "Road Mapping",
                "location_str": "Nairobi, Kenya",
                "status": None,
                "visibility": None,
                "field_mapping_app": None,
                "description": "",
                "hashtags": [],
                "created_at": None,
            }
        ],
        selected_status="",
        search_query="",
        selected_sort="newest",
        create_project_href="/new",
    )

    assert "Location: Nairobi, Kenya" in html


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


async def test_project_listing_renders_cards_and_component_bootstrap(client, project):
    """Project listing should render saved projects and register WA components."""
    response = await client.get("/projects", headers={"HX-Request": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert project.project_name in response.text
    assert f"/projects/{project.id}" in response.text
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


def test_project_listing_template_compiles():
    """Project listing template should compile without Jinja syntax errors."""
    templates_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("home.html")

    assert template.name == "home.html"


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
    """Test ODK finalize response includes manager credentials."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@example.org",
        manager_password="StrongPass123!",
    )

    html = _build_odk_finalize_success_html(result)

    assert "Manager Access (ODK Central UI)" in html
    assert "field-tm-manager@example.org" in html
    assert "StrongPass123!" in html
    assert "Save these credentials now." in html


def test_build_odk_finalize_success_html_does_not_render_qr_markup():
    """Finalize response should not include mapper QR code markup."""
    result = ODKFinalizeResult(
        odk_url="https://central.example.org/#/projects/17",
        manager_username="field-tm-manager@example.org",
        manager_password="StrongPass123!",
    )

    html = _build_odk_finalize_success_html(result)
    html_normalized = " ".join(html.split())

    assert "ODK Collect App User Access" not in html_normalized
    assert "Project QR Code" not in html_normalized


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
    """Plain-text errors should remain user-facing and include details toggle."""
    html = _build_finalize_error_html("Could not connect to ODK Central.")

    assert "Could not connect to ODK Central." in html
    assert "View technical details" in html


def test_build_finalize_error_html_uses_generic_text_for_json_payload():
    """Structured payloads should show a generic user-facing message."""
    html = _build_finalize_error_html('{"detail":"{"error":"invalid credentials"}"}')

    assert "Project finalisation failed." in html
    assert "View technical details" in html
    assert "&quot;detail&quot;" in html
