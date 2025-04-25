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
"""Tests for central routes."""

import pytest

from app.db.enums import XLSFormType


async def test_list_forms(client):
    """Test get a list of all XLSForms available in Field-TM."""
    response = await client.get("/central/list-forms")
    assert response.status_code == 200

    forms_json = response.json()
    supported_form_categories = {xls_type.value for xls_type in XLSFormType}
    for form in forms_json:
        assert "id" in form
        assert form["title"] in supported_form_categories


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
