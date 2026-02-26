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

from io import BytesIO

import pandas as pd
import pytest
from litestar.datastructures import UploadFile

from app.central.central_routes import detect_form_languages
from app.db.enums import XLSFormType


def _build_xlsform_bytes(
    survey: pd.DataFrame,
    settings: pd.DataFrame | None = None,
) -> bytes:
    """Build an in-memory XLSForm file for route tests."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        survey.to_excel(writer, sheet_name="survey", index=False)
        if settings is not None:
            settings.to_excel(writer, sheet_name="settings", index=False)
    output.seek(0)
    return output.getvalue()


async def test_list_forms(client):
    """Test get a list of all XLSForms available in Field-TM."""
    response = await client.get("/central/list-forms")
    assert response.status_code == 200

    forms_json = response.json()
    supported_form_categories = {xls_type.value for xls_type in XLSFormType}
    for form in forms_json:
        assert "id" in form
        assert form["title"] in supported_form_categories


async def test_detect_form_languages():
    """Detect translation columns and default language from XLSForm."""
    survey_df = pd.DataFrame(
        {
            "type": ["text"],
            "name": ["q1"],
            "label::english(en)": ["Question in English"],
            "hint::french(fr)": ["Indice en francais"],
            "required_message::spanish(es)": ["Mensaje requerido"],
        }
    )
    settings_df = pd.DataFrame({"default_language": ["english(en)"]})
    xlsform_bytes = _build_xlsform_bytes(survey=survey_df, settings=settings_df)

    response_data = await detect_form_languages.fn(
        data=UploadFile(
            filename="form.xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            file_data=xlsform_bytes,
        )
    )

    assert response_data["detected_languages"] == ["english", "french", "spanish"]
    assert response_data["default_language"] == ["english"]
    assert "english" in response_data["supported_languages"]


async def test_detect_form_languages_with_blank_default():
    """Blank/NaN settings default language should not break detection."""
    survey_df = pd.DataFrame(
        {
            "type": ["text"],
            "name": ["q1"],
            "label::french(fr)": ["Question en francais"],
        }
    )
    settings_df = pd.DataFrame({"default_language": [float("nan")]})
    xlsform_bytes = _build_xlsform_bytes(survey=survey_df, settings=settings_df)

    response_data = await detect_form_languages.fn(
        data=UploadFile(
            filename="form.xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            file_data=xlsform_bytes,
        )
    )

    assert response_data["detected_languages"] == ["french"]
    assert response_data["default_language"] == []


if __name__ == "__main__":
    """Main func if file invoked directly."""
    pytest.main()
