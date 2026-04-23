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
"""Tests for qfield dependency URL resolution."""

from app.qfield.qfield_deps import _resolve_qfield_creds
from app.qfield.qfield_schemas import QFieldCloud


def test_resolve_qfield_creds_uses_internal_url_for_local_custom_hostname(monkeypatch):
    """Custom creds targeting local proxy hostname should resolve to backend URL."""
    monkeypatch.setattr(
        "app.qfield.qfield_deps.settings.QFIELDCLOUD_URL",
        "http://qfield-app:8000",
    )

    resolved = _resolve_qfield_creds(
        QFieldCloud(
            qfield_cloud_url="http://qfield.field.localhost:7050",
            qfield_cloud_user="svcftm",
            qfield_cloud_password="secret",
        )
    )

    assert resolved.qfield_cloud_url == "http://qfield-app:8000/api/v1/"
    assert resolved.qfield_cloud_user == "svcftm"
    assert resolved.qfield_cloud_password == "secret"


def test_resolve_qfield_creds_keeps_remote_custom_url(monkeypatch):
    """Remote custom creds should remain on the provided instance URL."""
    monkeypatch.setattr(
        "app.qfield.qfield_deps.settings.QFIELDCLOUD_URL",
        "http://qfield-app:8000/api/v1/",
    )

    resolved = _resolve_qfield_creds(
        QFieldCloud(
            qfield_cloud_url="https://app.qfield.cloud/a/draperc/",
            qfield_cloud_user="svcftm",
            qfield_cloud_password="secret",
        )
    )

    assert resolved.qfield_cloud_url == "https://app.qfield.cloud/api/v1/"
