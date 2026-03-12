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
from pathlib import Path
from unittest.mock import Mock

import pytest

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


def test_project_details_template_includes_location_display():
    """Project details template should render a dedicated location line."""
    template_path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "templates"
        / "project_details.html"
    )
    content = template_path.read_text()
    assert "📍 {{ project.location_str }}" in content


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
