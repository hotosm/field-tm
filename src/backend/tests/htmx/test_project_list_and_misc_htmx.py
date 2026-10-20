"""Tests for HTMX routes."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import status_codes as status

from app.config import AuthProvider, settings
from app.db.enums import ProjectStatus
from app.db.models import DbProject
from app.htmx.landing_routes import _safe_return_path
from app.htmx.project_list_routes import project_listing

# We patch where project_crud is used/defined.
# htmx_routes imports `from app.projects import project_crud`
# so we patch `app.projects.project_crud.get_project_qr_data`


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
    # Mock get_project_qr_data to avoid calling ODK/QField
    with patch(
        "app.projects.project_crud.get_project_qr_data", new_callable=AsyncMock
    ) as mock_get_qrcode:
        mock_get_qrcode.return_value = "qfield://cloud?project=mocked"

        response = await client.get(
            f"/project-qrcode-htmx?project_id={project.id}",
            headers={"HX-Request": "true"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "<wa-qr-code" in response.text
        assert 'value="qfield://cloud?project=mocked"' in response.text
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
    # No Google Fonts: @hotosm/ui bundles the HOT fonts.
    assert "fonts.googleapis.com/css2" not in response.text
    assert "fonts.gstatic.com" not in response.text
    # The import map resolves webawesome-all.js's bare specifiers; without it every
    # wa-* element renders as bare markup. Raw dist URLs, never jsDelivr's /+esm -
    # see the comment in layout.html.
    assert '"@awesome.me/webawesome/dist/components/"' in response.text
    assert "@hotosm/ui@3.0.0/dist/webawesome-all.js" in response.text
    assert "webawesome-all.js/+esm" not in response.text


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
    assert "ftm-footer__social" in rendered
    assert "Need help or have a request?" in rendered
    assert 'href="https://roadmap.hotosm.org/#tech-request"' in rendered
    assert "Submit a tech request" in rendered
    assert "mailto:" not in rendered
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


@pytest.mark.parametrize(
    ("return_to", "expected"),
    [
        (None, "/"),
        ("", "/"),
        ("/new", "/new"),
        ("/projects/1?tab=map", "/projects/1?tab=map"),
        ("https://field.test/projects/1?x=1", "/projects/1?x=1"),
        ("https://evil.example/phish", "/"),
        ("//evil.example/phish", "/"),
        ("/\\evil.example", "/"),
        ("javascript:alert(1)", "/"),
    ],
)
def test_safe_return_path_only_allows_same_origin_paths(return_to, expected):
    """return_to must never redirect off-site after login."""
    assert _safe_return_path(return_to, "field.test") == expected


def _render_login_page(
    auth_provider: str, login_url: str = "https://login.hotosm.org/app"
) -> str:
    """Render login.html with the globals the app installs."""
    templates_dir = Path(__file__).resolve().parents[2] / "app" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.add_extension("jinja2.ext.i18n")
    env.install_gettext_callables(
        lambda message: message, lambda s, p, n: s if n == 1 else p
    )
    env.globals.update(
        current_locale=lambda: "en",
        current_dir=lambda: "ltr",
        supported_locales=["en"],
        locale_labels={"en": "English"},
        auth_enabled=True,
        auth_provider=auth_provider,
        hanko_public_url="https://login.field.test",
        login_url=login_url,
        frontend_url="https://field.test",
    )
    return env.get_template("login.html").render(return_to="/new")


def test_login_page_embeds_hanko_form_for_bundled_auth():
    """Bundled auth renders the login form instead of redirecting to itself."""
    rendered = _render_login_page("bundled")

    assert "show-profile" in rendered
    assert 'redirect-after-login="/new"' in rendered
    assert "window.location.replace" not in rendered


@pytest.mark.parametrize("login_url", ["/login", "https://field.test/login"])
def test_login_page_embeds_form_when_custom_login_url_is_this_page(login_url):
    """A custom LOGIN_URL pointing at this /login must not redirect to itself."""
    rendered = _render_login_page("custom", login_url)

    assert "show-profile" in rendered
    assert "window.location.replace" not in rendered


def test_login_page_redirects_for_external_login_app():
    """Non-bundled providers redirect to the external login app."""
    rendered = _render_login_page("hotosm")

    assert "show-profile" not in rendered
    assert "window.location.replace" in rendered


async def test_project_listing_paginates():
    """An extra row means there is a next page; page 2 links back."""
    projects = [Mock(id=i) for i in range(13)]
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_all:
        mock_all.return_value = projects
        response = await project_listing.fn(
            request=Mock(query_params={"page": "2", "search": "roads"}),
            db=Mock(),
            auth_user=Mock(),
        )

    assert mock_all.await_args.kwargs["skip"] == 12
    assert mock_all.await_args.kwargs["limit"] == 13
    assert len(response.context["projects"]) == 12
    assert response.context["prev_href"] == "/projects?search=roads&sort=newest"
    assert response.context["next_href"] == "/projects?search=roads&sort=newest&page=3"


@pytest.mark.parametrize("page", ["0", "-3", "abc"])
async def test_project_listing_invalid_page_falls_back_to_first(page):
    """Invalid page numbers show the first page without a previous link."""
    with patch(
        "app.htmx.project_list_routes.DbProject.all", new_callable=AsyncMock
    ) as mock_all:
        mock_all.return_value = []
        response = await project_listing.fn(
            request=Mock(query_params={"page": page}), db=Mock(), auth_user=Mock()
        )

    assert mock_all.await_args.kwargs["skip"] == 0
    assert response.context["prev_href"] is None
    assert response.context["next_href"] is None


async def test_project_list_cards_are_links_and_layout_has_footer(client, project):
    """Cards are keyboard-accessible links; the shared footer is on every page."""
    response = await client.get("/projects")

    assert response.status_code == status.HTTP_200_OK
    assert f'class="ftm-project-card-link" href="/projects/{project.id}"' in (
        response.text
    )
    assert "https://roadmap.hotosm.org/#tech-request" in response.text
    assert "user-scalable=no" not in response.text


async def test_landing_page_has_single_footer(client):
    """The landing page uses the shared layout footer only."""
    response = await client.get("/")

    assert response.text.count("<footer") == 1
    assert response.text.count("Submit a tech request") == 1
