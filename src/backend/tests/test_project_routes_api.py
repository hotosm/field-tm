"""Tests for the read-only project API."""

from litestar import status_codes as status


async def _set_visibility(db, project_id: int, visibility: str) -> None:
    async with db.cursor() as cur:
        await cur.execute(
            "UPDATE projects SET visibility = %(v)s WHERE id = %(id)s",
            {"v": visibility, "id": project_id},
        )
    await db.commit()


async def test_project_detail_public(client, project, login_as):
    """Guests can read a public project's summary."""
    await login_as(None)

    response = await client.get(f"/api/v1/projects/{project.id}")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == project.id
    assert body["name"] == project.project_name
    assert body["field_mapping_app"] == "ODK"
    assert body["centroid"]["type"] == "Point"


async def test_project_detail_private_needs_role(client, db, project, login_as):
    """Private projects need login (401) and a project role (403)."""
    await _set_visibility(db, project.id, "PRIVATE")
    url = f"/api/v1/projects/{project.id}"

    await login_as(None)
    assert (await client.get(url)).status_code == status.HTTP_401_UNAUTHORIZED
    await login_as("stranger")
    assert (await client.get(url)).status_code == status.HTTP_403_FORBIDDEN


async def test_project_detail_missing_is_404(client):
    """Unknown projects are 404."""
    response = await client.get("/api/v1/projects/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_my_projects_requires_login(client, login_as):
    """Anonymous users get 401."""
    await login_as(None)
    response = await client.get("/api/v1/projects/mine")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_my_projects_includes_role_projects(client, db, project, login_as):
    """Projects where the user has a role are listed; others are not."""
    user = await login_as("mapper")
    url = "/api/v1/projects/mine"
    assert (await client.get(url)).json() == []

    async with db.cursor() as cur:
        await cur.execute(
            "INSERT INTO user_roles (user_sub, project_id, role) "
            "VALUES (%(sub)s, %(id)s, 'MAPPER')",
            {"sub": user.sub, "id": project.id},
        )
    await db.commit()

    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert [p["id"] for p in response.json()] == [project.id]


async def test_my_projects_includes_created(client, project):
    """The creator (local admin, auth disabled) sees their project."""
    response = await client.get("/api/v1/projects/mine")
    assert project.id in [p["id"] for p in response.json()]
