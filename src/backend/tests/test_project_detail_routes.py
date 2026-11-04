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
from io import BytesIO
from unittest.mock import AsyncMock, Mock

import pytest
from litestar import status_codes as status
from litestar.exceptions import HTTPException

from app.db.enums import FieldMappingApp, ProjectStatus, ProjectVisibility
from app.db.models import DbProject
from app.errors import ServiceError
from app.htmx import project_detail_routes
from app.htmx.htmx_schemas import XLSFormUploadData


async def test_project_details_includes_form_templates_json(monkeypatch):
    """The HTMX page should inline form template options for step 1."""
    project = Mock(id=7, xlsform_content=None, visibility=ProjectVisibility.PUBLIC)
    forms = [{"id": 1, "title": "OSM Buildings"}]

    async def fake_is_manager(*_args):
        return True

    monkeypatch.setattr(project_detail_routes, "_is_project_manager", fake_is_manager)

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
    project = Mock(
        id=9,
        xlsform_content=b"sheet",
        created_by_sub="fieldtm|7",
        visibility=ProjectVisibility.PUBLIC,
    )

    async def fake_one(_db, project_id):
        assert project_id == project.id
        return project

    async def fake_is_manager(*_args):
        return True

    monkeypatch.setattr(project_detail_routes.DbProject, "one", fake_one)
    monkeypatch.setattr(project_detail_routes, "_is_project_manager", fake_is_manager)

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
    # The local admin (auth disabled) may delete, so the control is shown.
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


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()


def _published_odk_project(**overrides) -> Mock:
    fields = {
        "id": 9,
        "created_by_sub": "fieldtm|7",
        "field_mapping_app": FieldMappingApp.ODK,
        "status": ProjectStatus.PUBLISHED,
    }
    return Mock(**(fields | overrides))


async def _post_form(monkeypatch, project, auth_user=None, update_form=None):
    """Call the route with a stub upload, returning the response and service mock."""
    update_form = update_form or AsyncMock()
    monkeypatch.setattr(
        project_detail_routes.DbProject, "one", AsyncMock(return_value=project)
    )
    monkeypatch.setattr(
        project_detail_routes,
        "resolve_uploaded_xlsform_bytes",
        AsyncMock(return_value=(BytesIO(b"form"), None)),
    )
    monkeypatch.setattr(project_detail_routes, "update_odk_project_form", update_form)
    response = await project_detail_routes.update_project_form_htmx.fn(
        db=Mock(),
        project_id=project.id,
        auth_user=auth_user or Mock(sub="fieldtm|7", is_admin=False),
        data=XLSFormUploadData(),
    )
    return response, update_form


async def test_update_form_publishes_for_project_creator(monkeypatch):
    """The project creator can update a published ODK form."""
    project = _published_odk_project()

    response, update_form = await _post_form(monkeypatch, project)

    assert response.status_code == status.HTTP_200_OK
    update_form.assert_awaited_once()
    assert update_form.await_args.args[1] is project


async def test_update_form_denies_other_managers(monkeypatch):
    """Only those who can delete the project can update its form."""
    with pytest.raises(HTTPException) as exc_info:
        await _post_form(
            monkeypatch,
            _published_odk_project(),
            Mock(sub="fieldtm|8", is_admin=False),
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "overrides",
    [
        {"field_mapping_app": FieldMappingApp.QFIELD},
        {"status": ProjectStatus.DRAFT},
    ],
)
async def test_update_form_rejects_unsupported_projects(monkeypatch, overrides):
    """QField and unpublished projects have no ODK form to update."""
    response, update_form = await _post_form(
        monkeypatch, _published_odk_project(**overrides)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    update_form.assert_not_awaited()


async def test_update_form_shows_service_errors(monkeypatch):
    """Failures reach the user with the service error's status."""
    response, _ = await _post_form(
        monkeypatch,
        _published_odk_project(),
        update_form=AsyncMock(side_effect=ServiceError("Central said no")),
    )

    assert response.status_code == ServiceError.status_code
    assert "Central said no" in response.content


@pytest.mark.parametrize(
    ("mapping_app", "shows_upload", "shows_warning"),
    [(FieldMappingApp.ODK, True, False), (FieldMappingApp.QFIELD, False, True)],
)
async def test_published_project_form_controls(
    client, db, project, mapping_app, shows_upload, shows_warning
):
    """ODK projects get the form upload, QField projects get the QGIS warning."""
    await DbProject.update(
        db,
        project.id,
        DbProject(field_mapping_app=mapping_app, status=ProjectStatus.PUBLISHED),
    )
    await db.commit()

    response = await client.get(
        f"/projects/{project.id}",
        headers={"HX-Request": "true"},
    )

    assert (f'hx-post="/projects/{project.id}/form"' in response.text) is shows_upload
    assert ("sync the" in response.text and "QGIS" in response.text) is shows_warning
