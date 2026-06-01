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
"""Unit tests for HTMX project detail routes."""

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from litestar import status_codes as status

from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.htmx import project_detail_routes


async def test_project_details_includes_form_templates_json(monkeypatch):
    """The HTMX page should inline form template options for step 1."""
    project = Mock(id=7, xlsform_content=None)
    forms = [{"id": 1, "title": "OSM Buildings"}]

    async def fake_one(_db, project_id):
        assert project_id == project.id
        return project

    async def fake_get_form_list(_db):
        return forms

    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_one)
    monkeypatch.setattr(
        project_detail_routes.central_crud,
        "get_form_list",
        fake_get_form_list,
    )

    response = await project_detail_routes.project_details.fn(
        request=Mock(),
        db=Mock(),
        project_id=project.id,
    )

    assert response.template_name == "project_details.html"
    assert response.context["project"] is project
    assert response.context["form_templates_json"] == json.dumps(forms)
    assert response.context["can_delete_project"] is False


async def test_project_details_allows_delete_for_project_creator(monkeypatch):
    """Project creator should get delete controls in HTMX context."""
    project = Mock(id=9, xlsform_content=b"sheet", created_by_sub="fieldtm|7")

    async def fake_one(_db, project_id):
        assert project_id == project.id
        return project

    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_one)

    response = await project_detail_routes.project_details.fn(
        request=Mock(),
        db=Mock(),
        project_id=project.id,
        auth_user=Mock(sub="fieldtm|7", is_admin=False),
    )

    assert response.context["can_delete_project"] is True


async def test_project_details_renders_location_and_manager_metadata(
    client, db, project
):
    """Project details route renders location without a legacy label."""
    await DbProject.update(
        db,
        project.id,
        DbProject(location_str="Nairobi, Kenya"),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    assert "📍 Nairobi, Kenya" in response.text
    assert "Location</h4>" not in response.text
    assert f'hx-delete="/projects/{project.id}"' in response.text


def test_can_delete_project_allows_creator():
    """Project creator should be allowed to delete from HTMX page."""
    project = Mock(created_by_sub="fieldtm|123")
    auth_user = Mock(sub="fieldtm|123", is_admin=False)
    assert project_detail_routes._can_delete_project(auth_user, project) is True


def test_can_delete_project_allows_admin():
    """Global admins should be allowed to delete any project."""
    project = Mock(created_by_sub="fieldtm|123")
    auth_user = Mock(sub="fieldtm|999", is_admin=True)
    assert project_detail_routes._can_delete_project(auth_user, project) is True


def test_can_delete_project_denies_non_manager():
    """Non-admin users who did not create the project cannot delete it."""
    project = Mock(created_by_sub="fieldtm|123")
    auth_user = Mock(sub="fieldtm|999", is_admin=False)
    assert project_detail_routes._can_delete_project(auth_user, project) is False


def test_parse_collaborator_usernames_handles_commas_and_dedupes():
    """Comma-separated input is parsed, stripped and de-duplicated."""
    result = project_detail_routes._parse_collaborator_usernames(
        " alice , bob,, charlie ,Alice"
    )
    assert result == ["alice", "bob", "charlie"]


def test_parse_collaborator_usernames_returns_empty_for_blank_input():
    """Blank input yields an empty list."""
    assert project_detail_routes._parse_collaborator_usernames("") == []
    assert project_detail_routes._parse_collaborator_usernames("   ,, , ") == []


def test_show_qfc_collaborator_form_requires_default_instance(monkeypatch):
    """The collaborator panel is only shown for default-instance QFC projects."""
    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )

    default_project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="qfc-1",
        external_project_instance_url="https://default-qfc.example.org/projects/1",
    )
    custom_project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="qfc-2",
        external_project_instance_url="https://custom-qfc.example.org/projects/2",
    )
    odk_project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.ODK,
        external_project_id="odk-1",
        external_project_instance_url="https://default-qfc.example.org/projects/3",
    )
    missing_id_project = SimpleNamespace(
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id=None,
        external_project_instance_url="https://default-qfc.example.org/projects/4",
    )

    assert project_detail_routes._show_qfc_collaborator_form(default_project) is True
    assert project_detail_routes._show_qfc_collaborator_form(custom_project) is False
    assert project_detail_routes._show_qfc_collaborator_form(odk_project) is False
    assert (
        project_detail_routes._show_qfc_collaborator_form(missing_id_project) is False
    )


async def test_add_qfc_collaborators_adds_multiple_users(monkeypatch):
    """Comma-separated input adds each user as EDITOR and reports success."""
    project = SimpleNamespace(
        id=42,
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="qfc-project-42",
        external_project_instance_url="https://default-qfc.example.org/projects/42",
    )
    captured: list[tuple[str, str, str]] = []

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    @asynccontextmanager
    async def fake_qfield_client():
        yield object()

    async def fake_add_collaborator(_client, qfc_project_id, username, role):
        captured.append((qfc_project_id, username, role.value))

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_detail_routes, "qfield_client", fake_qfield_client)
    monkeypatch.setattr(
        project_detail_routes,
        "add_qfc_project_collaborator",
        fake_add_collaborator,
    )

    response = await project_detail_routes.add_qfc_collaborators_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_usernames": "alice, bob, charlie"},
    )

    body = str(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert [(c[1], c[2]) for c in captured] == [
        ("alice", "editor"),
        ("bob", "editor"),
        ("charlie", "editor"),
    ]
    assert "alice, bob, charlie" in body


async def test_add_qfc_collaborators_reports_per_user_failures(monkeypatch):
    """Per-user failures are reported alongside successes; submitted HTML is escaped."""
    from litestar.exceptions import HTTPException

    project = SimpleNamespace(
        id=43,
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="qfc-project-43",
        external_project_instance_url="https://default-qfc.example.org/projects/43",
    )

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    @asynccontextmanager
    async def fake_qfield_client():
        yield object()

    async def fake_add_collaborator(_client, _qfc_project_id, username, _role):
        if username == "bad":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QFC user '<script>x</script>' not found.",
            )

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(project_detail_routes, "qfield_client", fake_qfield_client)
    monkeypatch.setattr(
        project_detail_routes,
        "add_qfc_project_collaborator",
        fake_add_collaborator,
    )

    response = await project_detail_routes.add_qfc_collaborators_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_usernames": "alice, bad"},
    )

    body = str(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert "alice" in body
    assert "Could not add &#x27;bad&#x27;" in body
    assert "<script>x</script>" not in body
    assert "&lt;script&gt;x&lt;/script&gt;" in body


async def test_add_qfc_collaborators_blocks_custom_instance(monkeypatch):
    """Custom QFC instance projects must not target the default credentials."""
    project = SimpleNamespace(
        id=44,
        field_mapping_app=FieldMappingApp.QFIELD,
        external_project_id="qfc-project-44",
        external_project_instance_url="https://custom-qfc.example.org/projects/44",
    )
    add_collaborator = Mock()

    async def fake_project_one(_db, project_id):
        assert project_id == project.id
        return project

    monkeypatch.setattr(
        "app.qfield.qfield_utils.settings.QFIELDCLOUD_URL",
        "https://default-qfc.example.org/api/v1/",
    )
    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_project_one)
    monkeypatch.setattr(
        project_detail_routes,
        "add_qfc_project_collaborator",
        add_collaborator,
    )

    response = await project_detail_routes.add_qfc_collaborators_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_usernames": "alice"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "custom QFieldCloud instance" in str(response.content)
    add_collaborator.assert_not_called()


async def test_add_qfc_collaborators_requires_input():
    """Blank input re-renders the form with an error message."""
    project = SimpleNamespace(id=45)

    response = await project_detail_routes.add_qfc_collaborators_htmx.fn(
        request=Mock(),
        db=Mock(),
        current_user={"project": project},
        auth_user=Mock(),
        project_id=project.id,
        data={"qfc_usernames": ""},
    )

    body = str(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert "at least one" in body.lower()


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
