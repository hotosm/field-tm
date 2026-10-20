"""Tests for DB model helpers."""

from unittest.mock import Mock

import pytest

from app.db.models import DbProject
from app.projects.project_schemas import ProjectUpdate

FEATCOL = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [85.3, 27.7]},
            "properties": {},
        }
    ],
}


async def test_project_update_set_null_clears_column(stub_project, db):
    """set_null writes NULL, which a None value in the update model can't."""
    await DbProject.update(
        db, stub_project.id, ProjectUpdate(task_areas_geojson=FEATCOL)
    )
    updated = await DbProject.update(
        db,
        stub_project.id,
        ProjectUpdate(data_extract_geojson=FEATCOL, task_areas_geojson=None),
        set_null=frozenset({"task_areas_geojson"}),
    )

    assert updated.task_areas_geojson is None
    assert updated.data_extract_geojson == FEATCOL


async def test_project_update_rejects_unknown_set_null_column():
    """Only real project columns can be cleared."""
    with pytest.raises(ValueError, match="Unknown project columns"):
        await DbProject.update(Mock(), 1, ProjectUpdate(), set_null=frozenset({"nope"}))
