"""Tests for the standard GeoJSON export of ODK and QField projects."""

from unittest.mock import AsyncMock, patch

import pytest
from litestar import status_codes as status
from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.xlsforms import healthcare

from app.db.enums import FieldMappingApp
from app.db.models import DbProject
from app.errors import NotFoundError, ValidationError
from app.projects import project_services

ODK_RECORD = {
    "__id": "uuid:1",
    "__system": {"submissionDate": "2026-01-01T00:00:00Z"},
    "xlocation": "27.7 85.3 0 0",
    "task_id": "2",
    "status": "mapped",
}
QFIELD_SURVEY = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [85.3, 27.7]},
            "properties": {"uuid": "q1", "task_id": 2, "status": "mapped"},
        }
    ],
}


def _project(app: FieldMappingApp) -> DbProject:
    return DbProject(id=1, field_mapping_app=app, external_project_id=5)


async def test_export_odk_project():
    """ODK submissions are normalised to standard features."""
    with patch.object(
        project_services.central_crud,
        "get_submissions",
        AsyncMock(return_value=[ODK_RECORD]),
    ) as get_submissions:
        fc = await project_services.export_project_geojson(
            None, _project(FieldMappingApp.ODK)
        )

    get_submissions.assert_awaited_once()
    assert get_submissions.await_args.args[1] == 5
    props = fc["features"][0]["properties"]
    assert props["id"] == "uuid:1"
    assert props["task_id"] == 2
    assert fc["features"][0]["geometry"]["type"] == "Point"


async def test_export_qfield_project():
    """QField survey features get the same standard properties."""
    with patch.object(
        project_services,
        "export_qfield_project_geojson",
        AsyncMock(return_value=QFIELD_SURVEY),
    ):
        fc = await project_services.export_project_geojson(
            None, _project(FieldMappingApp.QFIELD)
        )

    props = fc["features"][0]["properties"]
    assert props["id"] == "q1"
    assert props["task_id"] == 2


async def test_export_uses_osm_keys_from_the_form():
    """Questions with an osm_key column export under their OSM tag."""
    project = _project(FieldMappingApp.ODK)
    project.xlsform_content = convert_to_xlsform(healthcare)
    record = {"__id": "x", "contact_number": "+221771", "healthcare": "clinic nurse"}
    with patch.object(
        project_services.central_crud,
        "get_submissions",
        AsyncMock(return_value=[record]),
    ):
        fc = await project_services.export_project_geojson(None, project)

    props = fc["features"][0]["properties"]
    assert props["contact:phone"] == "+221771"
    assert props["healthcare"] == "clinic;nurse"


async def test_export_odk_without_submissions_is_404():
    """An ODK project with no submissions reports 404."""
    with (
        patch.object(
            project_services.central_crud,
            "get_submissions",
            AsyncMock(return_value=[]),
        ),
        pytest.raises(NotFoundError) as exc,
    ):
        await project_services.export_project_geojson(
            None, _project(FieldMappingApp.ODK)
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


async def test_export_other_apps_rejected():
    """Apps without a sync server cannot be exported."""
    with pytest.raises(ValidationError) as exc:
        await project_services.export_project_geojson(
            None, _project(FieldMappingApp.CHATMAP)
        )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


async def test_export_route_odk(client, project):
    """The export button downloads standard GeoJSON for ODK projects."""
    with patch.object(
        project_services.central_crud,
        "get_submissions",
        AsyncMock(return_value=[ODK_RECORD]),
    ):
        response = await client.get(f"/projects/{project.id}/export/geojson")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("application/geo+json")
    assert response.json()["features"][0]["properties"]["id"] == "uuid:1"
