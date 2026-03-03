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

from unittest.mock import AsyncMock, patch

import pytest

from app.qfield.qfield_crud import clean_tags_for_qgis
from app.qfield.qfield_routes import qfc_creds_test
from app.qfield.qfield_schemas import QFieldCloud


async def test_qfield_creds_test():
    """The surviving QField JSON route should still validate credentials."""
    with patch(
        "app.qfield.qfield_routes.qfc_credentials_test", new_callable=AsyncMock
    ) as mock_test_qfc:
        await qfc_creds_test.fn(
            qfc_creds=QFieldCloud(
                qfield_cloud_url="https://app.qfield.cloud",
                qfield_cloud_user="demo-user",
                qfield_cloud_password="Password1234",
            )
        )

    mock_test_qfc.assert_awaited_once()


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


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
