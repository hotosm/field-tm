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
"""Tests for helper routes."""

HELPERS_PREFIX = "/api/v1/helpers"

# ---------------------------------------------------------------------------
# GET /download-template-xlsform
# ---------------------------------------------------------------------------


async def test_download_template_xlsform_success(client):
    """A bundled XLSForm template should download as a valid XLSX file."""
    response = await client.get(
        f"{HELPERS_PREFIX}/download-template-xlsform",
        params={"form_type": "OSM Buildings"},
    )

    assert response.status_code == 200
    assert (
        response.headers["content-disposition"] == "attachment; filename=buildings.xlsx"
    )
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # XLSX files are zip archives, which always start with the PK magic bytes
    assert response.content[:2] == b"PK"


async def test_download_template_xlsform_invalid_form_type(client):
    """An unknown form_type should be rejected by enum validation."""
    response = await client.get(
        f"{HELPERS_PREFIX}/download-template-xlsform",
        params={"form_type": "not-a-real-form"},
    )

    assert response.status_code == 422
