"""Tests for ODK Central CRUD operations."""

import json
from contextlib import asynccontextmanager
from io import BytesIO
from unittest.mock import patch

import pytest
from litestar.exceptions import HTTPException
from pyodk.errors import PyODKError
from requests import Response

from app.central import central_crud
from app.central.central_schemas import ODKCentral
from app.config import encrypt_value
from app.db.models import DbProject


class DummyResponse:
    """Fake HTTP response for testing."""

    def __init__(self, payload: dict | list):
        """Initialize with a JSON payload."""
        self._payload = payload

    def json(self):
        """Return the stored payload."""
        return self._payload

    def raise_for_status(self):
        """No-op status check."""
        return None


class DummySession:
    """Fake HTTP session recording calls."""

    def __init__(self):
        """Initialize with empty call log."""
        self.post_calls = []
        self.patch_calls = []

    def get(self, path: str):
        """Handle GET requests with canned responses."""
        if path == "roles":
            return DummyResponse([{"id": 7, "name": "Project Manager"}])
        raise AssertionError(f"Unexpected GET path: {path}")

    def post(self, path: str, json: dict | None = None):
        """Handle POST requests with canned responses."""
        self.post_calls.append((path, json))
        if path == "users":
            return DummyResponse({"id": 1234})
        if path == "projects/17/assignments/7/1234":
            return DummyResponse({"success": True})
        if path == "projects/1/assignments/7/1234":
            return DummyResponse({"success": True})
        raise AssertionError(f"Unexpected POST path: {path}")

    def patch(self, path: str, json: dict | None = None):
        """Handle PATCH requests with canned responses."""
        self.patch_calls.append((path, json))
        if path == "users/1234":
            return DummyResponse({"success": True})
        raise AssertionError(f"Unexpected PATCH path: {path}")


class DummyClient:
    """Fake ODK client wrapping a DummySession."""

    def __init__(self):
        """Initialize with a DummySession."""
        self.session = DummySession()


@pytest.mark.asyncio
async def test_get_appuser_token_prefers_public_url_for_returned_link():
    """Use public ODK URL for returned app-user link when using env credentials."""

    class AppUserSession:
        def post(self, path: str, json: dict | None = None):
            if path == "projects/17/app-users":
                return DummyResponse({"token": "app-token", "id": "app-sub"})
            if path == "projects/17/forms/sample-form/assignments/2/app-sub":
                return DummyResponse({"success": True})
            raise AssertionError(f"Unexpected POST path: {path}")

    class AppUserClient:
        def __init__(self):
            self.session = AppUserSession()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield AppUserClient()

    with (
        patch("app.central.central_deps.pyodk_client", fake_pyodk_client),
        patch("app.central.central_crud.settings") as mock_settings,
    ):
        mock_settings.ODK_CENTRAL_URL = "http://central:8383"
        mock_settings.ODK_CENTRAL_PUBLIC_URL = "http://odk.fmtm.localhost:7050"

        token_link = await central_crud.get_appuser_token(
            xform_id="sample-form",
            project_odk_id=17,
            odk_credentials=None,
        )

    assert token_link == "http://odk.fmtm.localhost:7050/v1/key/app-token/projects/17"


@pytest.mark.asyncio
async def test_create_project_manager_user_success():
    """Create a project manager user and assign it to one project."""
    fake_client = DummyClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    creds = ODKCentral(
        external_project_instance_url="https://central.example.org",
        external_project_username="admin@hotosm.org",
        external_project_password="password",
    )

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=17,
            project_name="My Test Project",
            odk_credentials=creds,
        )

    assert username == "fmtm-manager-17@example.org"
    assert len(password) == 20
    assert fake_client.session.post_calls[0][0] == "users"
    assert fake_client.session.post_calls[0][1] == {
        "email": "fmtm-manager-17@example.org",
        "password": password,
    }
    assert fake_client.session.patch_calls[0][0] == "users/1234"
    assert fake_client.session.post_calls[1][0] == "projects/17/assignments/7/1234"


@pytest.mark.asyncio
async def test_create_project_manager_user_fallback_email_on_conflict():
    """Retry with a fallback email when default manager email already exists."""

    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else ""

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"{self.status_code} error")

    class ExistingUserSession:
        def __init__(self):
            self.post_calls = []
            self.get_calls = []
            self.patch_calls = []
            self.user_create_calls = 0

        def get(self, path: str):
            self.get_calls.append(path)
            if path == "roles":
                return Resp([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET path: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                self.user_create_calls += 1
                if self.user_create_calls == 1:
                    return Resp(
                        {"code": 409.2, "message": "Already exists"},
                        status_code=409,
                    )
                return Resp({"id": 999})
            if path == "projects/17/assignments/7/999":
                return Resp({"success": True})
            raise AssertionError(f"Unexpected POST path: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            if path == "users/999":
                return Resp({"success": True})
            raise AssertionError(f"Unexpected PATCH path: {path}")

    class ExistingUserClient:
        def __init__(self):
            self.session = ExistingUserSession()

    fake_client = ExistingUserClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=17,
            project_name="My Test Project",
            odk_credentials=None,
        )

    assert username.startswith("fmtm-manager-17")
    assert username.endswith("@example.org")
    assert username != "fmtm-manager-17@example.org"
    assert len(password) == 20
    first_payload = fake_client.session.post_calls[0][1]
    assert fake_client.session.post_calls[0][0] == "users"
    assert first_payload["email"] == "fmtm-manager-17@example.org"
    assert len(first_payload["password"]) == 20
    assert fake_client.session.post_calls[1][0] == "users"
    assert fake_client.session.post_calls[2][0] == "projects/17/assignments/7/999"
    assert fake_client.session.patch_calls[0][0] == "users/999"


@pytest.mark.asyncio
async def test_create_project_manager_user_missing_role():
    """Fail when ODK does not return a Project Manager role."""

    class MissingRoleSession(DummySession):
        def get(self, path: str):
            if path == "roles":
                return DummyResponse([{"id": 3, "name": "Project Viewer"}])
            raise AssertionError(f"Unexpected GET path: {path}")

    class MissingRoleClient(DummyClient):
        def __init__(self):
            self.session = MissingRoleSession()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield MissingRoleClient()

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        with pytest.raises(HTTPException) as exc_info:
            await central_crud.create_project_manager_user(
                project_odk_id=17,
                project_name="My Test Project",
                odk_credentials=None,
            )

    assert exc_info.value.status_code == 500
    assert "Project Manager" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_project_manager_user_all_candidates_exhausted():
    """Fail with 500 when every email candidate is rejected (conflict)."""

    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else ""

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"{self.status_code} error")

    class AlwaysFailSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []

        def get(self, path: str):
            if path == "roles":
                return Resp([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET path: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return Resp(
                    {"code": 409.2, "message": "Already exists"},
                    status_code=409,
                )
            raise AssertionError(f"Unexpected POST path: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            return Resp({"success": True})

    class AlwaysFailClient:
        def __init__(self):
            self.session = AlwaysFailSession()

    fake_client = AlwaysFailClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        with pytest.raises(HTTPException) as exc_info:
            await central_crud.create_project_manager_user(
                project_odk_id=17,
                project_name="My Test Project",
                odk_credentials=None,
            )

    assert exc_info.value.status_code == 500
    assert "Could not create" in str(exc_info.value.detail)
    # Both candidates (primary + 1 randomised fallback) should have been tried
    user_posts = [c for c in fake_client.session.post_calls if c[0] == "users"]
    assert len(user_posts) == 2


@pytest.mark.asyncio
async def test_create_project_manager_user_display_name_failure_non_fatal():
    """Display name PATCH failure should not block finalization."""

    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else ""

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"{self.status_code} error")

    class DisplayNameFailSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []

        def get(self, path: str):
            if path == "roles":
                return Resp([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET path: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return Resp({"id": 555})
            if path.startswith("projects/"):
                return Resp({"success": True})
            raise AssertionError(f"Unexpected POST path: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            return Resp({"message": "Not supported"}, status_code=400)

    class DisplayNameFailClient:
        def __init__(self):
            self.session = DisplayNameFailSession()

    fake_client = DisplayNameFailClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=25,
            project_name="Display Name Fail Project",
            odk_credentials=None,
        )

    # Should still succeed despite display name failure
    assert username == "fmtm-manager-25@example.org"
    assert len(password) == 20
    # PATCH was attempted
    assert len(fake_client.session.patch_calls) == 1
    assert fake_client.session.patch_calls[0][0] == "users/555"
    # Assignment was still made
    assert fake_client.session.post_calls[1][0] == "projects/25/assignments/7/555"


@pytest.mark.asyncio
async def test_create_project_manager_user_assignment_conflict_idempotent():
    """Assignment 409 (already assigned) should be treated as success."""

    class Resp:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code
            self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else ""

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"{self.status_code} error")

    class ConflictAssignSession:
        def __init__(self):
            self.post_calls = []
            self.patch_calls = []

        def get(self, path: str):
            if path == "roles":
                return Resp([{"id": 7, "name": "Project Manager"}])
            raise AssertionError(f"Unexpected GET path: {path}")

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            if path == "users":
                return Resp({"id": 333})
            if path.startswith("projects/"):
                return Resp({"message": "Already assigned"}, status_code=409)
            raise AssertionError(f"Unexpected POST path: {path}")

        def patch(self, path: str, json: dict | None = None):
            self.patch_calls.append((path, json))
            return Resp({"success": True})

    class ConflictAssignClient:
        def __init__(self):
            self.session = ConflictAssignSession()

    fake_client = ConflictAssignClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        username, password = await central_crud.create_project_manager_user(
            project_odk_id=42,
            project_name="Idempotent Project",
            odk_credentials=None,
        )

    # Should succeed even with 409 on assignment
    assert username == "fmtm-manager-42@example.org"
    assert len(password) == 20
    assert fake_client.session.post_calls[1][0] == "projects/42/assignments/7/333"


@pytest.mark.asyncio
async def test_create_project_manager_user_password_is_alphanumeric():
    """Generated password should be 20 chars of letters + digits only."""
    fake_client = DummyClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        _username, password = await central_crud.create_project_manager_user(
            project_odk_id=1,
            project_name="Password Test",
            odk_credentials=None,
        )

    assert len(password) == 20
    assert password.isalnum()


@pytest.mark.asyncio
async def test_create_project_manager_user_display_name_set():
    """Display name should include project name for Central UI readability."""
    fake_client = DummyClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        await central_crud.create_project_manager_user(
            project_odk_id=17,
            project_name="Riverside Survey",
            odk_credentials=None,
        )

    assert len(fake_client.session.patch_calls) == 1
    patch_payload = fake_client.session.patch_calls[0][1]
    assert patch_payload == {"displayName": "FMTM Manager - Riverside Survey"}


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


@pytest.mark.asyncio
async def test_create_odk_project_uses_relative_projects_path():
    """Create project should post to relative 'projects' path (no duplicated /v1)."""

    class CreateSession:
        def __init__(self):
            self.post_calls = []

        def post(self, path: str, json: dict | None = None):
            self.post_calls.append((path, json))
            response = DummyResponse({"id": 77, "name": "Field-TM Test"})
            response.ok = True
            response.text = ""
            return response

    class CreateClient:
        def __init__(self):
            self.session = CreateSession()

    fake_client = CreateClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        result = await central_crud.create_odk_project("Test")

    assert result["id"] == 77
    assert fake_client.session.post_calls[0][0] == "projects"
    assert fake_client.session.post_calls[0][1] == {"name": "Field-TM Test"}


@pytest.mark.asyncio
async def test_delete_odk_project_uses_relative_projects_path():
    """Delete project should use relative 'projects/{id}' path."""

    class DeleteResponse:
        def raise_for_status(self):
            return None

    class DeleteSession:
        def __init__(self):
            self.delete_calls = []

        def delete(self, path: str):
            self.delete_calls.append(path)
            return DeleteResponse()

    class DeleteClient:
        def __init__(self):
            self.session = DeleteSession()

    fake_client = DeleteClient()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        response = await central_crud.delete_odk_project(42)

    assert fake_client.session.delete_calls == ["projects/42"]
    assert response is not None


@pytest.mark.asyncio
async def test_create_odk_xform_passes_xml_text_definition():
    """Upload XML XForm as string so pyodk accepts the file type."""

    class FormsClient:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

    class Client:
        def __init__(self):
            self.forms = FormsClient()

    fake_client = Client()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<h:html xmlns:h="http://www.w3.org/1999/xhtml" '
        'xmlns="http://www.w3.org/2002/xforms"></h:html>'
    )

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        await central_crud.create_odk_xform(
            odk_id=7,
            xform_data=BytesIO(xml.encode("utf-8")),
            odk_credentials=None,
        )

    assert len(fake_client.forms.calls) == 1
    payload = fake_client.forms.calls[0]
    assert isinstance(payload["definition"], str)
    assert "http://www.w3.org/2002/xforms" in payload["definition"]
    assert payload["project_id"] == 7
    assert payload["ignore_warnings"] is True


@pytest.mark.asyncio
async def test_create_odk_xform_keeps_binary_payload_for_xlsx():
    """Keep bytes payload for non-UTF8/binary form definitions."""

    class FormsClient:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

    class Client:
        def __init__(self):
            self.forms = FormsClient()

    fake_client = Client()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    binary_xlsx_like = b"\x50\x4b\x03\x04\x00\xff\xfe\xfd\xfc"

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        await central_crud.create_odk_xform(
            odk_id=9,
            xform_data=BytesIO(binary_xlsx_like),
            odk_credentials=None,
        )

    assert len(fake_client.forms.calls) == 1
    payload = fake_client.forms.calls[0]
    assert isinstance(payload["definition"], bytes)
    assert payload["definition"] == binary_xlsx_like
    assert payload["project_id"] == 9


@pytest.mark.asyncio
async def test_create_odk_xform_treats_duplicate_form_conflict_as_success():
    """Duplicate xmlFormId conflict should be treated as idempotent success."""

    class FormsClient:
        def create(self, **kwargs):
            response = Response()
            response.status_code = 409
            response._content = json.dumps(
                {
                    "message": (
                        "A resource already exists with projectId,xmlFormId "
                        "value(s) of 1,buildings."
                    ),
                    "code": 409.3,
                    "details": {
                        "fields": ["projectId", "xmlFormId"],
                        "values": ["1", "buildings"],
                        "table": "forms",
                    },
                }
            ).encode("utf-8")
            response.headers["Content-Type"] = "application/json"
            raise PyODKError("duplicate form", response)

    class Client:
        def __init__(self):
            self.forms = FormsClient()

    fake_client = Client()

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<h:html xmlns:h="http://www.w3.org/1999/xhtml" '
        'xmlns="http://www.w3.org/2002/xforms"></h:html>'
    )

    with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
        # Should not raise even though pyodk raises duplicate conflict.
        await central_crud.create_odk_xform(
            odk_id=1,
            xform_data=BytesIO(xml.encode("utf-8")),
            odk_credentials=None,
        )


class DatasetResponse:
    """Fake HTTP response for dataset property APIs."""

    def __init__(
        self,
        status_code: int,
        payload: dict | list | None = None,
        text: str = "",
    ):
        """Initialize a response object with status and payload."""
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        """Return JSON payload."""
        return self._payload

    def raise_for_status(self):
        """Raise requests-like error when status is not OK."""
        if self.status_code >= 400:
            raise Exception(
                f"{self.status_code} Client Error: error for dataset properties"
            )


class FakeEntities:
    """Minimal fake pyodk entities endpoint wrapper."""

    def __init__(self):
        """Initialize call tracking containers."""
        self.create_many_calls = []
        self.update_calls = []

    def get_table(self, entity_list_name: str, project_id: int):
        """Return an empty table so new entities get inserted."""
        return {"value": []}

    def update(self, **kwargs):
        """Record update calls."""
        self.update_calls.append(kwargs)

    def create_many(self, **kwargs):
        """Record bulk insert calls."""
        self.create_many_calls.append(kwargs)


class FakePropertySession:
    """Fake pyodk session handling dataset property requests."""

    def __init__(self):
        """Initialize call tracking containers."""
        self.get_calls = []
        self.post_calls = []

    def get(self, path: str):
        """Return existing properties for dataset."""
        self.get_calls.append(path)
        return DatasetResponse(
            status_code=200,
            payload=[{"name": "geometry"}, {"name": "status"}],
        )

    def post(self, path: str, json: dict | None = None):
        """Record and accept property creation calls."""
        self.post_calls.append((path, json))
        return DatasetResponse(status_code=201, payload={"name": json.get("name")})


class FakeConflictPropertySession(FakePropertySession):
    """Fake session returning 404 on list and 409 on property creation."""

    def get(self, path: str):
        """Simulate property listing unsupported / unavailable."""
        self.get_calls.append(path)
        return DatasetResponse(status_code=404, payload={})

    def post(self, path: str, json: dict | None = None):
        """Always simulate existing property conflict."""
        self.post_calls.append((path, json))
        return DatasetResponse(status_code=409, payload={"code": 409})


class FakePyODKClient:
    """Minimal pyodk client with session + entities endpoints."""

    def __init__(self, session):
        """Initialize fake client."""
        self.session = session
        self.entities = FakeEntities()


class FakeOdkDataset:
    """Minimal async dataset helper for create_entity_list tests."""

    def __init__(self):
        """Initialize with call tracking."""
        self.create_dataset_calls = []

    async def listDatasets(self, odk_id: int):
        """Return existing dataset names."""
        return [{"name": "features"}]

    async def createDataset(
        self,
        odk_id: int,
        datasetName: str,
        properties: list[str],
    ):
        """Record unexpected create calls."""
        self.create_dataset_calls.append((odk_id, datasetName, properties))


@pytest.mark.asyncio
async def test_create_entity_list_skips_existing_dataset_properties():
    """Only missing dataset properties should be created."""
    fake_dataset = FakeOdkDataset()
    fake_client = FakePyODKClient(FakePropertySession())

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        yield fake_dataset

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.get_odk_dataset", fake_get_odk_dataset):
        with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
            await central_crud.create_entity_list(
                odk_creds=None,
                odk_id=1,
                properties=["geometry", "status", "task_id"],
                dataset_name="features",
                entities_list=[
                    {
                        "label": "Task 1",
                        "data": {"geometry": "g", "status": "ready", "task_id": "1"},
                    }
                ],
            )

    # Existing geometry/status should not be re-created.
    created_property_names = [
        payload.get("name")
        for _path, payload in fake_client.session.post_calls
        if isinstance(payload, dict)
    ]
    assert "task_id" in created_property_names
    assert "geometry" not in created_property_names
    assert "status" not in created_property_names
    assert len(fake_client.entities.create_many_calls) == 1


@pytest.mark.asyncio
async def test_create_entity_list_ignores_409_property_conflicts():
    """Property creation conflicts should not fail ODK finalization."""
    fake_dataset = FakeOdkDataset()
    fake_client = FakePyODKClient(FakeConflictPropertySession())

    @asynccontextmanager
    async def fake_get_odk_dataset(_):
        yield fake_dataset

    @asynccontextmanager
    async def fake_pyodk_client(_):
        yield fake_client

    with patch("app.central.central_deps.get_odk_dataset", fake_get_odk_dataset):
        with patch("app.central.central_deps.pyodk_client", fake_pyodk_client):
            await central_crud.create_entity_list(
                odk_creds=None,
                odk_id=1,
                properties=["geometry"],
                dataset_name="features",
                entities_list=[
                    {
                        "label": "Task 1",
                        "data": {"geometry": "g", "status": "ready"},
                    }
                ],
            )

    # 409 property conflict should be tolerated and entity upload should proceed.
    assert len(fake_client.session.post_calls) >= 1
    assert len(fake_client.entities.create_many_calls) == 1
