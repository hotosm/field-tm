"""Authorisation tests with auth enabled (non-admin users)."""

from unittest.mock import AsyncMock, patch

import pytest
from litestar import status_codes as status

from app.config import encrypt_value

MANAGER_ONLY_ROUTES = [
    ("PUT", "/api/v1/projects/{id}/task-plan"),
    ("POST", "/projects/{id}/task-plan/whole-area"),
    ("POST", "/projects/{id}/task-plan/upload"),
    ("POST", "/projects/{id}/task-plan/sync"),
    ("POST", "/download-osm-data-htmx?project_id={id}"),
    ("POST", "/upload-geojson-htmx?project_id={id}"),
    ("POST", "/collect-new-data-only-htmx?project_id={id}"),
    ("POST", "/submit-geojson-data-extract-htmx?project_id={id}"),
    ("POST", "/accept-data-extract-htmx?project_id={id}"),
    ("POST", "/discard-data-extract-htmx?project_id={id}"),
    ("POST", "/upload-xlsform-htmx?project_id={id}"),
    ("GET", "/projects/{id}/export/geojson"),
]


@pytest.mark.parametrize(("method", "path"), MANAGER_ONLY_ROUTES)
async def test_manager_routes_forbid_other_users(
    client, project, login_as, method, path
):
    """A logged-in user without a manager role cannot change a public project."""
    await login_as("mapper")
    response = await client.request(method, path.format(id=project.id))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(("method", "path"), MANAGER_ONLY_ROUTES[:3])
async def test_manager_routes_require_login(client, project, login_as, method, path):
    """Anonymous requests are rejected before any project access."""
    await login_as(None)
    response = await client.request(method, path.format(id=project.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_project_creator_can_use_manager_routes(client, db, project, login_as):
    """The creator of a project is its manager."""
    user = await login_as("creator")
    async with db.cursor() as cur:
        await cur.execute(
            "UPDATE projects SET created_by_sub = %(sub)s WHERE id = %(id)s",
            {"sub": user.sub, "id": project.id},
        )
    await db.commit()

    response = await client.post(f"/accept-data-extract-htmx?project_id={project.id}")
    assert response.status_code != status.HTTP_403_FORBIDDEN


async def test_project_admin_role_can_use_manager_routes(client, db, project, login_as):
    """A PROJECT_MANAGER role grants manager access."""
    user = await login_as("manager")
    async with db.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO user_roles (user_sub, project_id, role)
            VALUES (%(sub)s, %(id)s, 'PROJECT_MANAGER')
            """,
            {"sub": user.sub, "id": project.id},
        )
    await db.commit()

    response = await client.post(f"/accept-data-extract-htmx?project_id={project.id}")
    assert response.status_code != status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "path", ["/api/v1/central/test-credentials", "/api/v1/qfield/test-credentials"]
)
async def test_credential_tests_require_login(client, login_as, path):
    """Credential test endpoints must not be usable anonymously."""
    await login_as(None)
    response = await client.post(path, json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_odk_credential_test_reads_json_body(client, login_as):
    """ODK credentials are sent in the body, never the query string."""
    await login_as("mapper")
    with patch(
        "app.central.central_routes.central_crud.odk_credentials_test",
        new_callable=AsyncMock,
    ) as mock_test:
        response = await client.post(
            "/api/v1/central/test-credentials",
            json={
                "external_project_instance_url": "https://central.example.org",
                "external_project_username": "user@example.org",
                "external_project_password": "secret",  # gitleaks:allow
            },
        )

    assert response.status_code == status.HTTP_200_OK
    creds = mock_test.await_args.args[0]
    assert creds.external_project_username == "user@example.org"
    assert creds.external_project_password == "secret"


async def _make_qfield_project_with_creds(db, project_id):
    async with db.cursor() as cur:
        await cur.execute(
            """
            UPDATE projects
            SET field_mapping_app = 'QField',
                external_project_id = 'qfc-abc',
                external_project_instance_url = 'https://app.qfield.cloud/a/HOTOSM/demo',
                external_project_username = '<b>manager</b>',
                external_project_password_encrypted = %(pw)s
            WHERE id = %(id)s
            """,
            {"pw": encrypt_value("<script>pw</script>"), "id": project_id},
        )
    await db.commit()


async def _get_qr_panel(client, project_id):
    with patch(
        "app.projects.project_crud.get_project_qr_data", new_callable=AsyncMock
    ) as mock_qr:
        mock_qr.return_value = "qfield://cloud?project=abc"
        return await client.get(
            f"/project-qrcode-htmx?project_id={project_id}",
            headers={"HX-Request": "true"},
        )


@pytest.mark.parametrize("user", [None, "stranger", "local_admin"])
async def test_qr_panel_never_shows_stored_qfc_credentials(
    client, db, project, login_as, user
):
    """Stored QFieldCloud credentials stay server-side; mappers use own accounts."""
    await _make_qfield_project_with_creds(db, project.id)
    if user != "local_admin":
        await login_as(user)

    response = await _get_qr_panel(client, project.id)

    assert response.status_code == status.HTTP_200_OK
    assert "pw" not in response.text
    assert "&lt;b&gt;manager" not in response.text
    assert "<b>manager" not in response.text
    assert "https://app.qfield.cloud/accounts/signup/" in response.text


async def test_project_page_hides_setup_from_non_managers(client, project, login_as):
    """Only managers see the draft setup steps."""
    await login_as("stranger")

    response = await client.get(f"/projects/{project.id}")

    assert response.status_code == status.HTTP_200_OK
    assert "Project Setup" not in response.text
    assert "not ready for mapping yet" in response.text


async def test_project_page_shows_setup_to_managers(client, project):
    """Managers (here the local admin) see the setup steps."""
    response = await client.get(f"/projects/{project.id}")

    assert "Project Setup" in response.text


async def test_project_page_shows_failed_creation_status(client, db, project):
    """A failed background creation is surfaced with its error."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            UPDATE projects
            SET creation_status = 'failed', creation_error = 'Boom <b>'
            WHERE id = %(id)s
            """,
            {"id": project.id},
        )
    await db.commit()

    response = await client.get(f"/projects/{project.id}")

    assert "Project creation failed." in response.text
    assert "Boom &lt;b&gt;" in response.text


async def test_delete_project_requires_login(client, project, login_as):
    """Anonymous users can't delete projects."""
    await login_as(None)
    response = await client.delete(f"/projects/{project.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_project_forbidden_for_non_owner(client, project, login_as):
    """Only the project creator (or a global admin) can delete it."""
    await login_as("someone-else")
    response = await client.delete(f"/projects/{project.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_project_owner_can_delete(client, db, project, login_as):
    """The creator sees the delete control and can delete the project."""
    user = await login_as("owner")
    async with db.cursor() as cur:
        await cur.execute(
            "UPDATE projects SET created_by_sub = %(sub)s WHERE id = %(id)s",
            {"sub": user.sub, "id": project.id},
        )
    await db.commit()

    page = await client.get(f"/projects/{project.id}")
    assert f'hx-delete="/projects/{project.id}"' in page.text

    with patch(
        "app.htmx.project_detail_routes.delete_project_with_downstream",
        new_callable=AsyncMock,
    ) as mock_delete:
        response = await client.delete(
            f"/projects/{project.id}", headers={"HX-Request": "true"}
        )
    assert response.status_code == status.HTTP_200_OK
    mock_delete.assert_awaited_once()


async def test_non_owner_does_not_see_delete(client, project, login_as):
    """The delete control is hidden from other users."""
    await login_as("viewer")
    page = await client.get(f"/projects/{project.id}")
    assert f'hx-delete="/projects/{project.id}"' not in page.text
