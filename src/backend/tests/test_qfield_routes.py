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

from app.qfield.qfield_crud import (
    _can_manage_qfc_users_locally,
    _is_org_owned_project,
    _resolve_qfield_project_url,
    _sanitize_qfc_project_name,
    _should_open_in_edit_mode,
    _strip_feature_properties_for_qfield,
    clean_tags_for_qgis,
)
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


def test_remote_qfield_instances_skip_local_user_management_sidecar():
    """Externally hosted QFieldCloud cannot use the local ORM sidecar."""
    assert (
        _can_manage_qfc_users_locally(
            QFieldCloud(
                qfield_cloud_url="https://app.qfield.cloud/api/v1/",
                qfield_cloud_user="demo-user",
                qfield_cloud_password="Password1234",
            )
        )
        is False
    )


def test_local_qfield_instances_still_use_local_user_management_sidecar():
    """Locally hosted QFieldCloud should continue using the sidecar."""
    assert (
        _can_manage_qfc_users_locally(
            QFieldCloud(
                qfield_cloud_url="http://qfield.field.localhost:7050/api/v1/",
                qfield_cloud_user="svcftm",
                qfield_cloud_password="password",
            )
        )
        is True
    )


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


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
