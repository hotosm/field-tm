# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Tests for qfield routes."""

import base64
from contextlib import asynccontextmanager
from io import BytesIO
from types import SimpleNamespace

import pytest

from app.qfield import qfield_crud
from app.qfield.qfield_crud import (
    _build_qfc_service_account_email,
    _create_qfc_user,
    _is_org_owned_project,
    _resolve_backend_qfc_url,
    _resolve_qfield_project_url,
    _sanitize_qfc_project_name,
    _should_open_in_edit_mode,
    _strip_feature_properties_for_qfield,
    clean_tags_for_qgis,
)
from app.qfield.qfield_routes import qfield_router
from app.qfield.qfield_schemas import QFieldCloud
from app.qfield.qfield_utils import normalise_qfc_url


async def test_qfield_creds_test_invalid_credentials_returns_400(client):
    """QField credential endpoint should reject invalid credentials."""
    response = await client.post(
        "/api/v1/qfield/test-credentials",
        json={
            "qfield_cloud_url": "https://app.qfield.cloud",
            "qfield_cloud_user": "invalid-user",
            "qfield_cloud_password": "invalid-password",
        },
    )

    assert response.status_code == 400


def test_legacy_qfield_add_collaborator_api_is_removed():
    """Collaborator management belongs to the token-based QFC admin HTMX flow."""
    route_paths = [route.path for route in qfield_router.routes]

    assert "/api/v1/qfield/test-credentials" in route_paths
    assert (
        "/api/v1/qfield/projects/{qfc_project_id:str}/collaborators" not in route_paths
    )


def test_clean_tags_for_qgis_stringifies_nested_properties():
    """Nested GeoJSON properties should be flattened before QGIS processing."""
    input_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "osm_id": 1,
                    "tags": {"building": "yes", "levels": "2"},
                    "members": ["a", "b"],
                    "meta": {"source": "osm"},
                },
            }
        ],
    }

    cleaned = clean_tags_for_qgis(input_geojson)

    assert cleaned["features"][0]["properties"]["tags"] == "building=yes;levels=2"
    assert cleaned["features"][0]["properties"]["members"] == '["a","b"]'
    assert cleaned["features"][0]["properties"]["meta"] == '{"source":"osm"}'
    assert input_geojson["features"][0]["properties"]["tags"] == {
        "building": "yes",
        "levels": "2",
    }


def test_resolve_qfield_project_url_prefers_absolute_api_url():
    """Use the API-provided project URL when QFieldCloud returns one."""
    url = _resolve_qfield_project_url(
        {
            "id": "123",
            "url": "http://qfield.field.localhost:7050/projects/123",
        },
        None,
    )

    assert url == "http://qfield.field.localhost:7050/projects/123"


def test_resolve_qfield_project_url_falls_back_to_instance_root():
    """Fallback should avoid guessing an internal route that redirects to admin."""
    url = _resolve_qfield_project_url(
        {"id": "123", "owner": "svcftm", "name": "demo"},
        QFieldCloud(
            qfield_cloud_url="http://qfield.field.localhost:7050/api/v1/",
            qfield_cloud_user="svcftm",
            qfield_cloud_password="password",
        ),
    )

    assert url == "http://qfield.field.localhost:7050"


def test_resolve_backend_qfc_url_prefers_internal_url_for_local_public_hostname(
    monkeypatch,
):
    """Backend QField clients should use the internal URL for local proxy hosts."""
    monkeypatch.setattr(
        "app.qfield.qfield_crud.settings.QFIELDCLOUD_URL",
        "http://qfield-app:8000",
    )

    resolved = _resolve_backend_qfc_url("http://qfield.field.localhost:7050")

    assert resolved == "http://qfield-app:8000/api/v1/"


def test_resolve_backend_qfc_url_prefers_internal_for_dev_test_hostname(monkeypatch):
    """Backend QField clients should rewrite local test domains to internal host."""
    monkeypatch.setattr(
        "app.qfield.qfield_crud.settings.QFIELDCLOUD_URL",
        "http://qfield-app:8000/api/v1/",
    )

    resolved = _resolve_backend_qfc_url("https://qfield.field-tm.dev.test")

    assert resolved == "http://qfield-app:8000/api/v1/"


def test_resolve_backend_qfc_url_keeps_remote_custom_url(monkeypatch):
    """A real remote custom QField URL should remain unchanged."""
    monkeypatch.setattr(
        "app.qfield.qfield_crud.settings.QFIELDCLOUD_URL",
        "http://qfield-app:8000/api/v1/",
    )

    resolved = _resolve_backend_qfc_url("https://app.qfield.cloud")

    assert resolved == "https://app.qfield.cloud/api/v1/"


def test_normalise_qfc_url_strips_project_path_segments():
    """QFieldCloud URLs should be reduced to the instance origin before API path."""
    assert (
        normalise_qfc_url("https://app.qfield.cloud/a/draperc/")
        == "https://app.qfield.cloud/api/v1/"
    )


def test_qfield_cloud_schema_normalises_project_url_to_instance_root():
    """Schema validation should accept a pasted project URL and canonicalize it."""
    creds = QFieldCloud(
        qfield_cloud_url="https://app.qfield.cloud/a/draperc/",
        qfield_cloud_user="svcftm",
        qfield_cloud_password="password",
    )

    assert creds.qfield_cloud_url == "https://app.qfield.cloud/api/v1/"


def test_existing_features_disable_initial_edit_mode():
    """Projects seeded with existing geometries should open out of edit mode."""
    assert (
        _should_open_in_edit_mode(
            {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "geometry": None, "properties": {}}],
            }
        )
        is False
    )
    assert (
        _should_open_in_edit_mode({"type": "FeatureCollection", "features": []}) is True
    )


def test_sanitize_qfc_project_name_removes_invalid_characters():
    """QFieldCloud project names must use only letters, numbers, _, -, or ."""
    raw = "FieldTM-qfield ijdshguijrg-3159991724"

    sanitized = _sanitize_qfc_project_name(raw)

    assert sanitized == "FieldTM-qfield-ijdshguijrg-3159991724"


def test_sanitize_qfc_project_name_handles_unicode_and_symbols():
    """Unicode and symbols should be normalized to API-safe separators."""
    raw = "  FieldTM-प्रोजेक्ट @ Kathmandu #1  "

    sanitized = _sanitize_qfc_project_name(raw)

    assert sanitized == "FieldTM-Kathmandu-1"


def test_build_qfc_service_account_email_uses_fieldtm_domain():
    """Provisioned QField users should always get a non-empty email."""
    email = _build_qfc_service_account_email("ftm_manager_14")

    assert email == "ftm_manager_14@fieldtm.org"


def test_build_qfc_service_account_email_sanitizes_local_part():
    """Usernames should be normalized into valid email local parts."""
    email = _build_qfc_service_account_email("ftm mapper 14")

    assert email == "ftm-mapper-14@fieldtm.org"


@pytest.mark.asyncio
async def test_create_qfc_user_passes_generated_email_to_sdk():
    """User creation should send a concrete email to QFieldCloud."""

    class FakeClient:
        def __init__(self):
            self.calls = []

        def create_user(self, username, password, email="", exist_ok=False):
            self.calls.append(
                {
                    "username": username,
                    "password": password,
                    "email": email,
                    "exist_ok": exist_ok,
                }
            )
            return {"username": username}

    client = FakeClient()

    created = await _create_qfc_user("ftm_mapper_14", "secret", client)

    assert created is True
    assert client.calls == [
        {
            "username": "ftm_mapper_14",
            "password": "secret",
            "email": "ftm_mapper_14@fieldtm.org",
            "exist_ok": True,
        }
    ]


@pytest.mark.asyncio
async def test_add_qfc_project_collaborator_user_not_found_in_org():
    """404 from add_organization_member should surface as a clean user-not-found."""
    from unittest.mock import MagicMock

    from litestar.exceptions import HTTPException
    from qfieldcloud_sdk.interfaces import QfcRequestException
    from qfieldcloud_sdk.sdk import ProjectCollaboratorRole

    from app.qfield.qfield_crud import add_qfc_project_collaborator

    response = MagicMock()
    response.status_code = 404
    response.url = "http://qfield-app:8000/api/v1/members/HOTOSM/?limit=20&offset=0"
    response.reason = "Not Found"
    response.json.return_value = {
        "code": "object_not_found",
        "message": "Object not found",
    }
    response.content = b'{"detail": "User matching query does not exist."}'

    class FakeClient:
        username = "svcftm"

        def get_project(self, _project_id):
            return {"owner": "HOTOSM"}

        def get_organization_members(self, _organization):
            return []

        def add_organization_member(self, *_args, **_kwargs):
            raise QfcRequestException(response)

    with pytest.raises(HTTPException) as excinfo:
        await add_qfc_project_collaborator(
            FakeClient(),
            "qfc-project-7",
            "spwoodcock",
            ProjectCollaboratorRole.EDITOR,
        )

    assert excinfo.value.status_code == 404
    assert "spwoodcock" in str(excinfo.value.detail)
    assert "does not exist" in str(excinfo.value.detail)
    # Make sure the noisy "Could not add ... to the organization: ..." wrapper
    # did not get re-applied on top of the friendly message.
    assert "Could not add" not in str(excinfo.value.detail)


def test_strip_feature_properties_for_qfield_removes_seed_attributes():
    """Seed geometries should not leak raw source attributes into the QField layer."""
    stripped = _strip_feature_properties_for_qfield(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "abc",
                    "geometry": {"type": "Point", "coordinates": [1, 2]},
                    "properties": {"created_by": "svcftm", "fill": "#00ff00"},
                }
            ],
        }
    )

    assert stripped["features"][0]["id"] == "abc"
    assert stripped["features"][0]["geometry"] == {
        "type": "Point",
        "coordinates": [1, 2],
    }
    assert stripped["features"][0]["properties"] == {}


def test_org_owned_project_detection_only_triggers_for_different_owner():
    """Only org-owned projects need organization membership before sharing."""
    assert _is_org_owned_project("HOTOSM", "svcftm") is True
    assert _is_org_owned_project("svcftm", "svcftm") is False


@pytest.mark.asyncio
async def test_attach_basemap_to_qfield_project_inserts_job_with_basemap_url(
    monkeypatch,
):
    """Basemap attach should enqueue qgis job using basemap_url transport."""

    class DummyDb:
        async def commit(self):
            return None

    inserted_calls = []
    deleted_calls = []

    async def fake_insert_qgis_job(
        db,
        job_id,
        xlsform,
        features,
        tasks,
        operation="field",
        project_id=None,
        basemap_url=None,
    ):
        inserted_calls.append(
            {
                "db": db,
                "job_id": job_id,
                "xlsform": xlsform,
                "features": features,
                "tasks": tasks,
                "operation": operation,
                "project_id": project_id,
                "basemap_url": basemap_url,
            }
        )

    async def fake_call_qgis_wrapper(**kwargs):
        assert kwargs["endpoint"] == "/basemap"

    async def fake_read_qgis_job_outputs(db, job_id):
        return {
            "project.qgz": base64.b64encode(b"qgz-bytes").decode("ascii"),
        }

    async def fake_delete_qgis_job(db, job_id):
        deleted_calls.append(job_id)

    downloaded_basemaps = []

    async def fake_download_file_for_qfield_upload(url, destination):
        downloaded_basemaps.append((url, destination.name))
        destination.write_bytes(b"mbtiles-bytes")

    @asynccontextmanager
    async def fake_qfield_client(_creds=None):
        class FakeClient:
            def upload_files(self, **kwargs):
                return None

        yield FakeClient()

    monkeypatch.setattr(qfield_crud, "_insert_qgis_job", fake_insert_qgis_job)
    monkeypatch.setattr(qfield_crud, "_call_qgis_wrapper", fake_call_qgis_wrapper)
    monkeypatch.setattr(
        qfield_crud, "_read_qgis_job_outputs", fake_read_qgis_job_outputs
    )
    monkeypatch.setattr(
        qfield_crud,
        "_download_file_for_qfield_upload",
        fake_download_file_for_qfield_upload,
    )
    monkeypatch.setattr(qfield_crud, "_delete_qgis_job", fake_delete_qgis_job)
    monkeypatch.setattr(qfield_crud, "qfield_client", fake_qfield_client)

    project = SimpleNamespace(
        id=7,
        external_project_id="qfc-123",
        project_name="demo",
        external_project_instance_url=None,
        external_project_username=None,
        external_project_password_encrypted=None,
    )

    await qfield_crud.attach_basemap_to_qfield_project(
        DummyDb(),
        project,
        "https://tiles.example.com/basemap.mbtiles",
    )

    assert len(inserted_calls) == 1
    inserted = inserted_calls[0]
    assert inserted["operation"] == "basemap"
    assert inserted["project_id"] == "qfc-123"
    assert inserted["basemap_url"] == "https://tiles.example.com/basemap.mbtiles"
    assert deleted_calls
    assert downloaded_basemaps == [
        ("https://tiles.example.com/basemap.mbtiles", "basemap.mbtiles")
    ]


@pytest.mark.asyncio
async def test_create_qfield_project_passes_resolved_language_to_qgis_wrapper(
    monkeypatch,
):
    """create_qfield_project should pass resolved form language to QGIS wrapper."""

    class DummyDb:
        async def commit(self):
            return None

    captured: dict = {}

    async def fake_modify_form_for_qfield(*args, **kwargs):
        return "french(fr)", BytesIO(b"updated-xlsform")

    async def fake_db_update(*args, **kwargs):
        return None

    async def fake_insert_qgis_job(*args, **kwargs):
        return None

    async def fake_call_qgis_wrapper(**kwargs):
        captured["language"] = kwargs["language"]

    async def fake_read_qgis_job_outputs(*args, **kwargs):
        return {
            "project.qgz": base64.b64encode(b"qgz-bytes").decode("ascii"),
        }

    async def fake_delete_qgis_job(*args, **kwargs):
        return None

    async def fake_upload_to_qfieldcloud(**kwargs):
        return qfield_crud.QFieldProjectResult(
            qfield_url="https://app.qfield.cloud/project/demo",
            manager_username=None,
            manager_password=None,
            mapper_username=None,
            mapper_password=None,
        )

    monkeypatch.setattr(
        qfield_crud, "modify_form_for_qfield", fake_modify_form_for_qfield
    )
    monkeypatch.setattr(qfield_crud.DbProject, "update", fake_db_update)
    monkeypatch.setattr(qfield_crud, "_insert_qgis_job", fake_insert_qgis_job)
    monkeypatch.setattr(qfield_crud, "_call_qgis_wrapper", fake_call_qgis_wrapper)
    monkeypatch.setattr(
        qfield_crud, "_read_qgis_job_outputs", fake_read_qgis_job_outputs
    )
    monkeypatch.setattr(qfield_crud, "_delete_qgis_job", fake_delete_qgis_job)
    monkeypatch.setattr(
        qfield_crud, "_upload_to_qfieldcloud", fake_upload_to_qfieldcloud
    )

    project = SimpleNamespace(
        id=11,
        project_name="demo",
        outline={
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [85.3, 27.7]},
            "properties": {},
        },
        xlsform_content=b"original-xlsform",
        data_extract_geojson={"type": "FeatureCollection", "features": []},
        task_areas_geojson={},
        external_project_id=None,
    )

    await qfield_crud.create_qfield_project(
        DummyDb(),
        project,
        default_language="english",
    )

    assert captured["language"] == "french(fr)"


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
