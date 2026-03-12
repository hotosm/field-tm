"""Tests for ODK Central CRUD operations."""

import json
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from litestar.exceptions import HTTPException
from pyodk.errors import PyODKError
from requests import Response

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.config import encrypt_value
from app.db.models import DbProject

TEST_DATA_DIR = Path(__file__).parent / "test_data"

# ---------------------------------------------------------------------------
# Happy-path tests - use real ODK Central
# ---------------------------------------------------------------------------


async def test_create_odk_project(odk_project):
    """create_odk_project should return a dict with an integer id."""
    # odk_project fixture already created the project and will delete it on teardown
    assert isinstance(odk_project, int)
    assert odk_project > 0


async def test_delete_odk_project(odk_creds):
    """delete_odk_project should remove a project without raising."""
    proj = await central_crud.create_odk_project("ftm-delete-test", odk_creds)
    odk_id = proj["id"]
    result = await central_crud.delete_odk_project(odk_id)
    assert result is not None


async def test_create_odk_xform_from_xlsform_bytes(odk_project):
    """Uploading an XLSForm file to a real ODK project should succeed."""
    xlsform_bytes = (TEST_DATA_DIR / "buildings.xls").read_bytes()
    # Raw bundled forms need FTM fields appended before they can be converted
    _form_name, processed_io = await central_crud.append_fields_to_user_xlsform(
        BytesIO(xlsform_bytes)
    )
    xml_io = await central_crud.read_and_test_xform(processed_io)
    await central_crud.create_odk_xform(
        odk_id=odk_project,
        xform_data=xml_io,
        odk_credentials=None,
    )


async def test_create_odk_xform_duplicate_is_idempotent(odk_project):
    """Uploading the same form twice should not raise (409 treated as success)."""
    xlsform_bytes = (TEST_DATA_DIR / "buildings.xls").read_bytes()
    _form_name, processed_io = await central_crud.append_fields_to_user_xlsform(
        BytesIO(xlsform_bytes)
    )
    xml_io = await central_crud.read_and_test_xform(processed_io)
    xml_bytes = xml_io.read()

    await central_crud.create_odk_xform(
        odk_id=odk_project,
        xform_data=BytesIO(xml_bytes),
        odk_credentials=None,
    )
    # Second upload: ODK returns 409 - should be handled as success
    await central_crud.create_odk_xform(
        odk_id=odk_project,
        xform_data=BytesIO(xml_bytes),
        odk_credentials=None,
    )


async def test_create_project_manager_user_returns_credentials(odk_project):
    """create_project_manager_user should return a valid username and password."""
    username, password = await central_crud.create_project_manager_user(
        project_odk_id=odk_project,
        project_name="Integration Test Project",
        odk_credentials=None,
    )
    assert username.startswith("field-tm-manager-")
    assert username.endswith("@example.org")
    assert len(password) == 20
    assert password.isalnum()


async def test_create_entity_list_creates_and_extends_properties(odk_project):
    """create_entity_list should add new properties without failing on existing ones."""
    # First call: create entity list with two properties
    await central_crud.create_entity_list(
        odk_creds=None,
        odk_id=odk_project,
        properties=["geometry", "status"],
        dataset_name="features",
        entities_list=[],
    )
    # Second call: extend with a third property - existing ones must not cause a failure
    await central_crud.create_entity_list(
        odk_creds=None,
        odk_id=odk_project,
        properties=["geometry", "status", "task_id"],
        dataset_name="features",
        entities_list=[
            {
                "label": "Task 1",
                "data": {"geometry": "g", "status": "unmapped", "task_id": "1"},
            }
        ],
    )


async def test_create_entity_list_updates_existing_entity(odk_project):
    """create_entity_list should update an existing entity when data changes."""
    # Seed the entity list with one entity
    await central_crud.create_entity_list(
        odk_creds=None,
        odk_id=odk_project,
        properties=["geometry", "status", "task_id"],
        dataset_name="features",
        entities_list=[
            {
                "label": "Task 1",
                "data": {"geometry": "g", "status": "unmapped", "task_id": "1"},
            }
        ],
    )
    # Call again with the same label but a different status - should update, not fail
    await central_crud.create_entity_list(
        odk_creds=None,
        odk_id=odk_project,
        properties=["geometry", "status", "task_id"],
        dataset_name="features",
        entities_list=[
            {
                "label": "Task 1",
                "data": {"geometry": "g", "status": "ready", "task_id": "1"},
            }
        ],
    )


# ---------------------------------------------------------------------------
# Static / DB-only tests - no ODK connection needed
# ---------------------------------------------------------------------------


def test_get_odk_credentials_requires_complete_fields():
    """Project credentials should only resolve when all fields are present."""
    project = DbProject(external_project_instance_url="https://central.example.org")
    assert project.get_odk_credentials() is None

    project = DbProject(
        external_project_instance_url="https://central.example.org",
        external_project_username="manager@hotosm.org",
        external_project_password_encrypted=encrypt_value("password"),
    )
    creds = project.get_odk_credentials()
    assert creds is not None
    assert creds.external_project_username == "manager@hotosm.org"


# ---------------------------------------------------------------------------
# Error-path tests - kept as unit tests because specific failure conditions
# cannot be reliably triggered against a real ODK Central instance
# ---------------------------------------------------------------------------


class DummyResponse:
    """Fake HTTP response for error-path testing."""

    def __init__(self, payload: dict | list, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else ""

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"{self.status_code} error")


class DummySession:
    """Fake HTTP session recording calls."""

    def __init__(self):
        self.post_calls = []
        self.patch_calls = []

    def get(self, path: str):
        if path == "roles":
            return DummyResponse([{"id": 7, "name": "Project Manager"}])
        raise AssertionError(f"Unexpected GET path: {path}")

    def post(self, path: str, json: dict | None = None):
        self.post_calls.append((path, json))
        if path == "users":
            return DummyResponse({"id": 1234})
        if path in ("projects/17/assignments/7/1234", "projects/1/assignments/7/1234"):
            return DummyResponse({"success": True})
        raise AssertionError(f"Unexpected POST path: {path}")

    def patch(self, path: str, json: dict | None = None):
        self.patch_calls.append((path, json))
        if path == "users/1234":
            return DummyResponse({"success": True})
        raise AssertionError(f"Unexpected PATCH path: {path}")


class DummyClient:
    def __init__(self):
        self.session = DummySession()


@asynccontextmanager
async def _fake_pyodk(client):
    yield client


async def test_get_appuser_token_prefers_public_url_for_returned_link():
    """Use public ODK URL for returned app-user link when using env credentials."""

    class AppUserSession:
        def post(self, path: str, json: dict | None = None):
            if path == "projects/17/app-users":
                return DummyResponse({"token": "app-token", "id": "app-sub"})
            if path in (
                "projects/17/assignments/2/app-sub",
                "projects/17/forms/sample-form/assignments/2/app-sub",
            ):
                return DummyResponse({"success": True})
            raise AssertionError(f"Unexpected POST path: {path}")

    class AppUserClient:
        def __init__(self):
            self.session = AppUserSession()

    with (
        patch(
            "app.central.central_deps.pyodk_client",
            lambda _: _fake_pyodk(AppUserClient()),
        ),
        patch("app.central.central_crud.settings") as mock_settings,
    ):
        mock_settings.ODK_CENTRAL_URL = "http://central:8383"
        mock_settings.ODK_CENTRAL_PUBLIC_URL = "http://odk.field.localhost:7050"

        token_link = await central_crud.get_appuser_token(
            xform_id="sample-form",
            project_odk_id=17,
            odk_credentials=None,
        )

    assert token_link == "http://odk.field.localhost:7050/v1/key/app-token/projects/17"


async def test_create_project_manager_user_fallback_email_on_conflict():
    """Retry with a fallback email when default manager email already exists."""

    class ExistingUserSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []
            self.user_create_calls = 0

        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                self.user_create_calls += 1
                if self.user_create_calls == 1:
                    return DummyResponse(
                        {"code": 409.2, "message": "Already exists"}, status_code=409
                    )
                return DummyResponse({"id": 999})
            if path == "projects/17/assignments/7/999":
                return DummyResponse({"success": True})
            raise AssertionError(f"Unexpected POST: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            if path == "users/999":
                return DummyResponse({"success": True})
            raise AssertionError(f"Unexpected PATCH: {path}")

    class ExistingUserClient:
        def __init__(self):
            self.session = ExistingUserSession()

    fake_client = ExistingUserClient()

    with patch(
        "app.central.central_deps.pyodk_client",
        lambda _: _fake_pyodk(fake_client),
    ):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=17,
            project_name="My Test Project",
            odk_credentials=None,
        )

    assert username.startswith("field-tm-manager-17")
    assert username.endswith("@example.org")
    assert username != "field-tm-manager-17@example.org"
    assert len(password) == 20
    assert fake_client.session.post_calls[0][0] == "users"
    assert fake_client.session.post_calls[0][1]["email"] == "field-tm-manager-17@example.org"
    assert fake_client.session.post_calls[1][0] == "users"
    assert fake_client.session.post_calls[2][0] == "projects/17/assignments/7/999"
    assert fake_client.session.patch_calls[0][0] == "users/999"


async def test_create_project_manager_user_missing_role():
    """Fail when ODK does not return a Project Manager role."""

    class MissingRoleSession(DummySession):
        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 3, "name": "Project Viewer"}])
            raise AssertionError(f"Unexpected GET: {path}")

    class MissingRoleClient:
        def __init__(self):
            self.session = MissingRoleSession()

    with patch(
        "app.central.central_deps.pyodk_client",
        lambda _: _fake_pyodk(MissingRoleClient()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await central_crud.create_project_manager_user(
                project_odk_id=17,
                project_name="My Test Project",
                odk_credentials=None,
            )

    assert exc_info.value.status_code == 500
    assert "Project Manager" in str(exc_info.value.detail)


async def test_create_project_manager_user_all_candidates_exhausted():
    """Fail with 500 when every email candidate is rejected (conflict)."""

    class AlwaysFailSession:
        def __init__(self):
            self.post_calls = []

        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return DummyResponse(
                    {"code": 409.2, "message": "Already exists"}, status_code=409
                )
            raise AssertionError(f"Unexpected POST: {path}")

        def patch(self, path: str, json: dict | None = None):
            return DummyResponse({"success": True})

    class AlwaysFailClient:
        def __init__(self):
            self.session = AlwaysFailSession()

    fake_client = AlwaysFailClient()

    with patch(
        "app.central.central_deps.pyodk_client",
        lambda _: _fake_pyodk(fake_client),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await central_crud.create_project_manager_user(
                project_odk_id=17,
                project_name="My Test Project",
                odk_credentials=None,
            )

    assert exc_info.value.status_code == 500
    assert "Could not create" in str(exc_info.value.detail)
    user_posts = [c for c in fake_client.session.post_calls if c[0] == "users"]
    assert len(user_posts) == 2


async def test_create_project_manager_user_display_name_failure_non_fatal():
    """Display name PATCH failure should not block finalization."""

    class DisplayNameFailSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []

        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return DummyResponse({"id": 555})
            if path.startswith("projects/"):
                return DummyResponse({"success": True})
            raise AssertionError(f"Unexpected POST: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            return DummyResponse({"message": "Not supported"}, status_code=400)

    class DisplayNameFailClient:
        def __init__(self):
            self.session = DisplayNameFailSession()

    fake_client = DisplayNameFailClient()

    with patch(
        "app.central.central_deps.pyodk_client",
        lambda _: _fake_pyodk(fake_client),
    ):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=25,
            project_name="Display Name Fail Project",
            odk_credentials=None,
        )

    assert username == "field-tm-manager-25@example.org"
    assert len(password) == 20
    assert len(fake_client.session.patch_calls) == 1
    assert fake_client.session.patch_calls[0][0] == "users/555"
    assert fake_client.session.post_calls[1][0] == "projects/25/assignments/7/555"


async def test_create_project_manager_user_assignment_conflict_idempotent():
    """Assignment 409 (already assigned) should be treated as success."""

    class ConflictAssignSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []

        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return DummyResponse({"id": 333})
            if path.startswith("projects/"):
                return DummyResponse({"message": "Already assigned"}, status_code=409)
            raise AssertionError(f"Unexpected POST: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            return DummyResponse({"success": True})

    class ConflictAssignClient:
        def __init__(self):
            self.session = ConflictAssignSession()

    fake_client = ConflictAssignClient()

    with patch(
        "app.central.central_deps.pyodk_client",
        lambda _: _fake_pyodk(fake_client),
    ):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=42,
            project_name="Idempotent Project",
            odk_credentials=None,
        )

    assert username == "field-tm-manager-42@example.org"
    assert len(password) == 20
    assert fake_client.session.post_calls[1][0] == "projects/42/assignments/7/333"
