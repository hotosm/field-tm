"""Tests for HTMX routes."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.config import AuthProvider, settings
from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.htmx.map_helpers import render_leaflet_map
from app.htmx.project_list_routes import project_listing

# We patch where project_crud is used/defined.
# htmx_routes imports `from app.projects import project_crud`
# so we patch `app.projects.project_crud.get_project_qrcode`


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


async def test_metrics_partial_counts_project_countries(client, db, project):
    """Countries covered should be derived from project locations."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT id, location_str
            FROM projects
            WHERE location_str IS NOT NULL;
            """
        )
        original_project_locations = await cur.fetchall()
        await cur.execute(
            """
            SELECT sub, country
            FROM users
            WHERE country IS NOT NULL;
            """
        )
        original_user_countries = await cur.fetchall()
        await cur.execute("UPDATE projects SET location_str = NULL;")
        await cur.execute("UPDATE users SET country = NULL;")
        await cur.execute(
            """
            UPDATE projects
            SET location_str = %(location_str)s
            WHERE id = %(project_id)s;
            """,
            {"project_id": project.id, "location_str": "Nairobi, Kenya"},
        )
        await cur.execute(
            """
            INSERT INTO projects (project_name, location_str)
            VALUES
                (%(duplicate_project_name)s, %(duplicate_location_str)s),
                (%(other_project_name)s, %(other_location_str)s)
            RETURNING id;
            """,
            {
                "duplicate_project_name": "metrics country duplicate",
                "duplicate_location_str": "Mombasa, Kenya",
                "other_project_name": "metrics country other",
                "other_location_str": "Kathmandu, Nepal",
            },
        )
        inserted_project_ids = [row[0] for row in await cur.fetchall()]
    await db.commit()

    try:
        response = await client.get("/metrics", headers={"HX-Request": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert (
            '<p class="landing-metric-value">2</p>\n'
            '      <p class="landing-metric-label">Countries Covered</p>'
        ) in response.text
    finally:
        async with db.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM projects
                WHERE id = ANY(%(project_ids)s);
                """,
                {"project_ids": inserted_project_ids},
            )
            await cur.execute("UPDATE projects SET location_str = NULL;")
            for project_id, location_str in original_project_locations:
                await cur.execute(
                    """
                    UPDATE projects
                    SET location_str = %(location_str)s
                    WHERE id = %(project_id)s;
                    """,
                    {"project_id": project_id, "location_str": location_str},
                )
            await cur.execute("UPDATE users SET country = NULL;")
            for user_sub, country in original_user_countries:
                await cur.execute(
                    """
                    UPDATE users
                    SET country = %(country)s
                    WHERE sub = %(user_sub)s;
                    """,
                    {"user_sub": user_sub, "country": country},
                )
        await db.commit()


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


def test_layout_template_renders_locale_selector_in_header():
    """Layout template should render the locale selector in the hot-header lang slot."""
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

    template = env.get_template("landing.html")
    rendered = template.render(create_project_href="/new")

    assert 'slot="lang"' in rendered
    assert 'data-locale-switch="en"' in rendered
    assert 'data-locale-switch="pt"' in rendered
    assert 'data-locale-switch="pt_br"' in rendered
    assert "ftm-header-lang-menu" in rendered
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


async def test_static_landing_image_served(client):
    """Test static landing JPG assets are served."""
    response = await client.get("/static/images/landing-bg.jpg")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-type", "").startswith("image/jpeg")


async def test_static_image_rejects_unsupported_extension(client):
    """Test static image route blocks unsupported extensions."""
    response = await client.get("/static/images/not-allowed.gif")
    assert response.status_code == status.HTTP_403_FORBIDDEN
