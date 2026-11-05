# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     osm-fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionality of update_form.py."""
import io
import re
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook, load_workbook, worksheet
from pyxform.xls2xform import convert as xform_convert

from osm_fieldwork.conversion_to_xlsform import convert_to_xlsform
from osm_fieldwork.enums import DbGeomType, NewPointCapture
from osm_fieldwork.form_components.translations import INCLUDED_LANGUAGES
from osm_fieldwork.update_xlsform import (
    GEOMETRY_QUESTION_TYPES,
    QFIELD_GEOMETRY_EXPRESSION,
    _configure_form_settings,
    get_processed_form_options,
    _normalize_language_token,
    append_field_mapping_fields,
    modify_form_for_qfield,
)
from osm_fieldwork.xlsforms import buildings, healthcare, xlsforms_path


async def test_merge_mandatory_fields(tmp_path):
    """Merge the mandatory fields XLSForm to a test survey form."""
    test_form = Path(__file__).parent / "test_data" / "test_form_for_mandatory_fields.xls"

    with open(test_form, "rb") as xlsform:
        form_bytes = BytesIO(xlsform.read())

    xformid, updated_form = await append_field_mapping_fields(form_bytes, "buildings")
    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))
    # Write merged xlsform to file for debugging
    (tmp_path / "merged_xlsform.xlsx").write_bytes(updated_form.getvalue())

    # remove duplicate field names in 'survey'
    survey = workbook["survey"]
    seen = set()
    for row in range(2, survey.max_row + 1):
        name = survey.cell(row=row, column=2).value
        if name in seen:
            survey.delete_rows(row, 1)
        else:
            seen.add(name)

    check_survey_sheet(workbook)
    check_entities_sheet(workbook)
    check_form_title(workbook)

    # Check it's still a valid xlsform by converting to XML
    xform_convert(updated_form)
    check_translation_fields(workbook)


def test_normalize_language_token_matches_base_language():
    """Region variants and bare codes should fall back to a supported base."""
    assert _normalize_language_token("es_MX") == "spanish(es)"
    assert _normalize_language_token("pt") == "portuguese(pt_br)"
    assert _normalize_language_token("pt-BR") == "portuguese(pt_br)"
    assert _normalize_language_token("am") is None


async def test_add_extra_select_from_file():
    """Append extra select_one_from_file questions based on Entity list names."""
    test_form = Path(__file__).parent / "test_data" / "test_form_for_mandatory_fields.xls"

    with open(test_form, "rb") as xlsform:
        form_bytes = BytesIO(xlsform.read())

    xformid, updated_form = await append_field_mapping_fields(form_bytes, "buildings", additional_entities=["roads", "waterpoints"])
    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))

    survey_sheet = workbook["survey"]
    name_column = [cell.value for cell in survey_sheet["B"]]

    assert "roads" in name_column, "The 'roads' field was not added to the survey sheet."
    assert "waterpoints" in name_column, "The 'waterpoints' field was not added to the survey sheet."


async def test_buildings_xlsform():
    """Merge and test if buildings form is a valid XLSForm."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(buildings)))
    xformid, updated_form = await append_field_mapping_fields(form_bytes, "buildings")
    # Check it's still a valid xlsform by converting to XML
    xform_convert(updated_form)

    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))
    check_translation_fields(workbook)


async def test_healthcare_xlsform():
    """Merge and test if buildings form is a valid XLSForm."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(healthcare)))
    xformid, updated_form = await append_field_mapping_fields(form_bytes, "healthcare")
    # Check it's still a valid xlsform by converting to XML
    xform_convert(updated_form)


BUNDLED_FORMS = sorted(Path(xlsforms_path).glob("*.yaml"))
GEOMETRY_TYPES = {"geopoint", "geotrace", "geoshape"}


def geometry_questions(form: bytes) -> list[str]:
    """Names of geometry questions in an XLSForm survey sheet."""
    survey = pd.read_excel(BytesIO(form), sheet_name="survey")
    return survey.loc[survey["type"].isin(GEOMETRY_TYPES), "name"].tolist()


@pytest.mark.parametrize("form", BUNDLED_FORMS, ids=lambda p: p.stem)
@pytest.mark.parametrize("use_odk_collect", [True, False])
@pytest.mark.parametrize("optional_fields", [True, False])
async def test_bundled_forms_valid_everywhere(form, use_odk_collect, optional_fields):
    """Bundled forms are valid standalone, after Field-TM processing, and for QField."""
    raw = convert_to_xlsform(str(form))
    xform_convert(BytesIO(raw))
    assert geometry_questions(raw) == ["new_feature"]

    _, updated_form = await append_field_mapping_fields(
        BytesIO(raw),
        form.stem,
        need_verification_fields=optional_fields,
        include_photo_upload=optional_fields,
        use_odk_collect=use_odk_collect,
    )
    xform_convert(BytesIO(updated_form.getvalue()))
    # The template geometry is replaced by the injected one (ODK) or map selection
    assert geometry_questions(updated_form.getvalue()) == (["new_feature"] if use_odk_collect else [])

    if not use_odk_collect:
        _, qfield_form = await modify_form_for_qfield(updated_form)
        assert geometry_questions(qfield_form.getvalue()) == ["feature"]
        xform_convert(qfield_form)


async def test_qfield_form_removes_odk_bookkeeping_fields():
    """QField-specific forms should not include ODK entity bookkeeping rows."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(buildings)))
    _, updated_form = await append_field_mapping_fields(form_bytes, "buildings")
    _, qfield_form = await modify_form_for_qfield(updated_form)

    workbook = load_workbook(filename=BytesIO(qfield_form.getvalue()))
    survey_sheet = workbook["survey"]
    name_col = [cell.value for cell in survey_sheet["B"]]

    assert "end_note" not in name_col
    assert "feature_exists" not in name_col
    assert "created_by" not in name_col
    assert "fill" not in name_col


async def test_qfield_form_preserves_photo_group_and_repeat_structure():
    """The QField photo tab should preserve the photo group and repeat."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(buildings)))
    _, updated_form = await append_field_mapping_fields(form_bytes, "buildings")
    _, qfield_form = await modify_form_for_qfield(updated_form)

    survey = pd.read_excel(
        BytesIO(qfield_form.getvalue()),
        sheet_name="survey",
        engine="calamine",
    )

    stack: list[str] = []
    expected_openers = {"end group": "begin group", "end repeat": "begin repeat"}
    for row in survey[["type", "name"]].itertuples(index=False):
        if row.type in {"begin group", "begin repeat"}:
            stack.append(row.type)
        elif row.type in expected_openers:
            assert stack, f"Unmatched {row.type} for {row.name}"
            assert stack.pop() == expected_openers[row.type]
    assert stack == []

    assert survey.loc[0, "type"] == "begin group"
    assert survey.loc[0, "name"] == "survey_questions"
    assert survey.loc[1, "name"] == "feature"

    photo_start = survey.index[
        (survey["type"] == "begin group") & (survey["name"] == "survey_photos")
    ][0]
    photo_rows = survey.loc[photo_start:photo_start + 4, ["type", "name"]]

    assert list(photo_rows["type"]) == [
        "begin group",
        "begin repeat",
        "image",
        "end repeat",
        "end group",
    ]
    assert list(photo_rows["name"].fillna("")) == [
        "survey_photos",
        "photos",
        "image",
        "photos",
        "",
    ]


async def test_odk_collect_entity_task_selection():
    """Test that ODK Collect forms use entity-based task selection."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(buildings)))
    xformid, updated_form = await append_field_mapping_fields(
        form_bytes, "buildings", use_odk_collect=True
    )
    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))
    survey_sheet = workbook["survey"]

    # Extract column values
    type_col = [cell.value for cell in survey_sheet["A"]]
    name_col = [cell.value for cell in survey_sheet["B"]]

    # Check select_one_from_file tasks.csv is present
    assert "select_one_from_file tasks.csv" in type_col, (
        "select_one_from_file tasks.csv not found in survey types"
    )

    # Check the task field name is 'task' (not 'task_filter')
    task_type_idx = type_col.index("select_one_from_file tasks.csv")
    assert name_col[task_type_idx] == "task", (
        f"Expected field name 'task', got '{name_col[task_type_idx]}'"
    )

    # Check selected_task_id calculated field exists
    assert "selected_task_id" in name_col, (
        "selected_task_id calculated field not found"
    )

    # Check no task_ids in choices sheet
    choices_sheet = workbook["choices"]
    list_name_col = [cell.value for cell in choices_sheet["A"]]
    assert "task_ids" not in list_name_col, (
        "task_ids should not be in choices sheet"
    )

    # Check feature choice_filter references selected_task_id
    feature_idx = name_col.index("feature")
    # Find the choice_filter column
    header = [cell.value for cell in next(survey_sheet.iter_rows(min_row=1, max_row=1))]
    if "choice_filter" in header:
        cf_col_idx = header.index("choice_filter") + 1
        choice_filter_val = survey_sheet.cell(row=feature_idx + 1, column=cf_col_idx).value
        assert "${selected_task_id}" in choice_filter_val, (
            f"Feature choice_filter should reference ${{selected_task_id}}, got: {choice_filter_val}"
        )


async def test_status_values_are_text():
    """Test that status values use text instead of integers."""
    form_bytes = io.BytesIO(convert_to_xlsform(str(buildings)))
    xformid, updated_form = await append_field_mapping_fields(
        form_bytes, "buildings", use_odk_collect=True
    )
    workbook = load_workbook(filename=BytesIO(updated_form.getvalue()))
    survey_sheet = workbook["survey"]

    name_col = [cell.value for cell in survey_sheet["B"]]
    header = [cell.value for cell in next(survey_sheet.iter_rows(min_row=1, max_row=1))]

    # Find calculation column
    calc_col_idx = header.index("calculation") + 1

    # Check status field uses text values
    status_idx = name_col.index("status")
    status_calc = survey_sheet.cell(row=status_idx + 1, column=calc_col_idx).value
    assert "'mapped'" in status_calc, f"Status calculation should use 'mapped', got: {status_calc}"
    assert "'invalid'" in status_calc, f"Status calculation should use 'invalid', got: {status_calc}"

    # Check default is text
    if "default" in header:
        default_col_idx = header.index("default") + 1
        status_default = survey_sheet.cell(row=status_idx + 1, column=default_col_idx).value
        assert status_default == "mapped", f"Status default should be 'mapped', got: {status_default}"

    # Check color calculations use text status
    fill_idx = name_col.index("fill")
    fill_calc = survey_sheet.cell(row=fill_idx + 1, column=calc_col_idx).value
    assert "'unmapped'" in fill_calc, f"Fill calculation should reference 'unmapped', got: {fill_calc}"
    assert "'invalid'" in fill_calc, f"Fill calculation should reference 'invalid', got: {fill_calc}"


def _minimal_qfield_test_form(
    survey_columns: list[str],
    settings_default_language: str | None = None,
) -> BytesIO:
    """Build a minimal XLSForm workbook for QField language resolution tests."""
    survey_data = {
        "type": ["select_one_from_file features.csv", "text", "note"],
        "name": ["feature", "name", "notes"],
    }
    for col in survey_columns:
        survey_data[col] = ["Feature", "Name", "Notes"]

    survey_df = pd.DataFrame(survey_data)
    settings_df = pd.DataFrame([{"form_id": "demo-form"}])
    if settings_default_language is not None:
        settings_df["default_language"] = settings_default_language

    xls_bytes = BytesIO()
    with pd.ExcelWriter(xls_bytes, engine="openpyxl") as writer:
        survey_df.to_excel(writer, sheet_name="survey", index=False)
        settings_df.to_excel(writer, sheet_name="settings", index=False)
    xls_bytes.seek(0)
    return xls_bytes


async def test_modify_form_for_qfield_prefers_explicit_language_over_settings_and_survey():
    """Explicit user-selected language must win over settings and survey order."""
    xlsform = _minimal_qfield_test_form(
        survey_columns=["label::english(en)", "label::french(fr)"],
        settings_default_language="french(fr)",
    )

    resolved_language, _ = await modify_form_for_qfield(
        xlsform,
        default_language="english",
    )

    assert resolved_language == "english(en)"


async def test_modify_form_for_qfield_uses_settings_default_language_when_explicit_missing():
    """Settings default_language should be used when no explicit language is provided."""
    xlsform = _minimal_qfield_test_form(
        survey_columns=["label::english(en)", "label::french(fr)"],
        settings_default_language="french",
    )

    resolved_language, _ = await modify_form_for_qfield(xlsform)

    assert resolved_language == "french(fr)"


async def test_modify_form_for_qfield_falls_back_to_first_survey_language_when_settings_invalid():
    """When settings language is invalid, fall back to first survey translation column."""
    xlsform = _minimal_qfield_test_form(
        survey_columns=["label::english(en)", "label::french(fr)"],
        settings_default_language="klingon",
    )

    resolved_language, _ = await modify_form_for_qfield(xlsform)

    assert resolved_language == "english(en)"


def test_configure_form_settings_keeps_default_language_as_scalar_string():
    """Settings default_language should remain a scalar string, not a tuple."""
    custom_sheets = {
        "survey": pd.DataFrame(
            {
                "type": ["text"],
                "name": ["name"],
                "label::english(en)": ["Name"],
            }
        ),
        "settings": pd.DataFrame([{"form_id": "demo-form", "default_language": "english"}]),
    }

    xform_id = _configure_form_settings(custom_sheets, "Demo Form", None)

    assert xform_id == "demo-form"
    default_language_value = custom_sheets["settings"]["default_language"].iloc[0]
    assert isinstance(default_language_value, str)
    assert default_language_value == "english(en)"


def _buildings_form() -> BytesIO:
    return BytesIO(convert_to_xlsform(str(buildings)))


def _form_settings(form: bytes) -> pd.Series:
    return pd.read_excel(BytesIO(form), sheet_name="settings", engine="calamine").iloc[0]


async def test_form_id_override_replaces_uploaded_form_id():
    """A new form version keeps the published xFormId, not the uploaded one."""
    xform_id, form = await append_field_mapping_fields(
        _buildings_form(),
        form_name="FTM_Project_1",
        use_odk_collect=True,
        form_id="published-form-id",
    )

    assert xform_id == "published-form-id"
    assert _form_settings(form.getvalue())["form_id"] == "published-form-id"
    assert 'id="published-form-id"' in xform_convert(form).xform


@pytest.mark.parametrize(
    "options",
    [
        {
            "need_verification_fields": True,
            "include_photo_upload": True,
            "mandatory_photo_upload": False,
            "new_point_capture": NewPointCapture.MAP,
        },
        {
            "need_verification_fields": False,
            "include_photo_upload": True,
            "mandatory_photo_upload": True,
            "new_point_capture": NewPointCapture.GPS,
        },
        {
            "need_verification_fields": False,
            "include_photo_upload": False,
            "mandatory_photo_upload": False,
            "new_point_capture": NewPointCapture.MAP,
        },
    ],
)
async def test_processed_form_options_round_trip(options):
    """Rebuilding a form with the recovered options keeps the same choices."""
    xform_id, form = await append_field_mapping_fields(
        _buildings_form(),
        form_name="FTM_Project_1",
        use_odk_collect=True,
        default_language="spanish",
        form_id="published-form-id",
        **options,
    )

    recovered = get_processed_form_options(form.getvalue())
    assert recovered == {
        **options,
        "form_id": xform_id,
        "default_language": "spanish(es)",
    }

    _, rebuilt = await append_field_mapping_fields(
        _buildings_form(), use_odk_collect=True, **recovered
    )
    assert get_processed_form_options(rebuilt.getvalue()) == recovered


@pytest.mark.parametrize(
    ("capture", "appearance"),
    [(NewPointCapture.MAP, "placement-map"), (NewPointCapture.GPS, "")],
)
async def test_new_point_capture_sets_appearance(capture, appearance):
    """The capture method sets a valid new_feature appearance that can be recovered."""
    _, form = await append_field_mapping_fields(
        _buildings_form(), use_odk_collect=True, new_point_capture=capture
    )
    xform_convert(BytesIO(form.getvalue()))

    survey = pd.read_excel(BytesIO(form.getvalue()), sheet_name="survey").fillna("")
    new_feature = survey[survey["name"] == "new_feature"].iloc[0]
    assert new_feature["type"] == "geopoint"
    assert new_feature["appearance"] == appearance
    assert get_processed_form_options(form.getvalue())["new_point_capture"] == capture


def _user_form(*questions: list) -> BytesIO:
    """An XLSForm with the given [type, name, label, relevant] survey rows."""
    workbook = Workbook()
    survey = workbook.active
    survey.title = "survey"
    survey.append(["type", "name", "label", "hint", "relevant"])
    for question in questions:
        survey.append(question)
    workbook.create_sheet("settings").append(["form_id", "form_title"])
    workbook["settings"].append(["user_form", "User form"])
    form = BytesIO()
    workbook.save(form)
    form.seek(0)
    return form


async def _merged_survey(form: BytesIO, **options) -> pd.DataFrame:
    """Build an ODK form, check it converts, and return its survey sheet."""
    _, updated = await append_field_mapping_fields(form, use_odk_collect=True, **options)
    xform_convert(BytesIO(updated.getvalue()))
    return pd.read_excel(BytesIO(updated.getvalue()), sheet_name="survey").fillna("")


def geometry_questions_in(survey: pd.DataFrame) -> list[str]:
    """Names of the questions collecting geometry, including pyxform aliases."""
    return survey.loc[survey["type"].isin(GEOMETRY_QUESTION_TYPES), "name"].tolist()


TAP_QUESTION = ["text", "tap_name", "Tap name", "", ""]


@pytest.mark.parametrize("question_type", ["geopoint", "gps", "location", "add location prompt"])
@pytest.mark.parametrize(
    ("capture", "appearance"),
    [(NewPointCapture.MAP, "placement-map"), (NewPointCapture.GPS, "")],
)
async def test_user_geopoint_merges_into_new_feature(question_type, capture, appearance):
    """A user's own point question merges, whichever capture method was selected."""
    survey = await _merged_survey(
        _user_form(
            [question_type, "tap_location", "Where is the tap?", "Stand beside it", ""],
            ["text", "tap_name", "Tap name", "", "${tap_location} != ''"],
        ),
        new_point_capture=capture,
    )

    assert "tap_location" not in set(survey["name"])
    assert geometry_questions_in(survey) == ["new_feature"]
    new_feature = survey[survey["name"] == "new_feature"].iloc[0]
    assert new_feature["type"] == "geopoint"
    assert new_feature["appearance"] == appearance
    assert new_feature.filter(like="label").eq("Where is the tap?").any()
    assert new_feature.filter(like="hint").eq("Stand beside it").any()
    assert survey[survey["name"] == "tap_name"].iloc[0]["relevant"] == "${new_feature} != ''"


@pytest.mark.parametrize(
    "questions",
    [
        [["geopoint", "spot", "Where?", "", ""]],
        [
            ["begin group", "outer", "Outer", "", ""],
            ["begin group", "inner", "Inner", "", ""],
            ["geopoint", "spot", "Where?", "", ""],
            ["end group", "", "", "", ""],
            ["end group", "", "", "", ""],
            TAP_QUESTION,
        ],
    ],
    ids=["only-question-in-form", "only-question-in-nested-groups"],
)
async def test_merging_the_only_question_of_a_group_keeps_the_form_valid(questions):
    """Groups emptied by the merge are removed, as pyxform rejects empty groups."""
    survey = await _merged_survey(_user_form(*questions))

    assert geometry_questions_in(survey) == ["new_feature"]
    assert not {"outer", "inner"} & set(survey["name"])


async def test_merge_keeps_user_constraint_and_parameters():
    """Validation and accuracy settings pass on, but required and relevant stay ours."""
    workbook = load_workbook(_user_form(["geopoint", "spot", "Where?", "", "1 = 1"], TAP_QUESTION))
    survey_sheet = workbook["survey"]
    for column, heading, value in [
        ("F", "constraint", "selected-at(${spot}, 3) < 50"),
        ("G", "constraint_message", "Too inaccurate"),
        ("H", "parameters", "capture-accuracy=5"),
        ("I", "required", "no"),
    ]:
        survey_sheet[f"{column}1"] = heading
        survey_sheet[f"{column}2"] = value
    form = BytesIO()
    workbook.save(form)
    form.seek(0)

    survey = await _merged_survey(form)

    new_feature = survey[survey["name"] == "new_feature"].iloc[0]
    assert new_feature["constraint"] == "selected-at(${new_feature}, 3) < 50"
    assert new_feature.filter(like="constraint_message").eq("Too inaccurate").any()
    assert new_feature["parameters"] == "capture-accuracy=5"
    assert new_feature["required"] == "yes"
    assert new_feature["relevant"] == "${mapping_mode} = 'new'"


async def test_user_appearance_does_not_override_selected_capture():
    """The selected capture method wins over the appearance in the user's form."""
    workbook = load_workbook(_user_form(["geopoint", "spot", "Where?", "", ""], TAP_QUESTION))
    workbook["survey"]["F1"] = "appearance"
    workbook["survey"]["F2"] = "placement-map"
    form = BytesIO()
    workbook.save(form)
    form.seek(0)

    survey = await _merged_survey(form, new_point_capture=NewPointCapture.GPS)

    assert survey[survey["name"] == "new_feature"].iloc[0]["appearance"] == ""


@pytest.mark.parametrize(
    ("question_type", "new_geom_type", "injected_type"),
    [("geoshape", DbGeomType.POLYGON, "geoshape"), ("geotrace", DbGeomType.LINESTRING, "geotrace")],
)
async def test_user_shape_and_trace_merge_into_matching_new_feature(
    question_type, new_geom_type, injected_type
):
    """Geoshape and geotrace questions merge when that is the geometry being collected."""
    survey = await _merged_survey(
        _user_form([question_type, "outline", "Trace it", "", ""], TAP_QUESTION),
        new_geom_type=new_geom_type,
    )

    assert geometry_questions_in(survey) == ["new_feature"]
    assert survey[survey["name"] == "new_feature"].iloc[0]["type"] == injected_type


async def test_template_geometry_question_is_still_replaced_by_name():
    """A question named new_feature is the duplicate, so other geopoints stay."""
    survey = await _merged_survey(
        _user_form(
            ["geopoint", "new_feature", "Where?", "", ""],
            ["geopoint", "entrance", "Entrance", "", ""],
        )
    )

    assert geometry_questions_in(survey) == ["new_feature", "entrance"]


@pytest.mark.parametrize(
    ("questions", "kept"),
    [
        ([["geoshape", "outline", "Outline", "", ""]], "outline"),
        ([["start-geopoint", "user_start", "", "", ""]], "user_start"),
        (
            [
                ["begin repeat", "taps", "Taps", "", ""],
                ["geopoint", "tap_location", "Tap", "", ""],
                ["end repeat", "taps", "", "", ""],
            ],
            "tap_location",
        ),
    ],
    ids=["other-geometry", "passive-metadata", "repeated"],
)
async def test_questions_collecting_separate_data_are_not_merged(questions, kept):
    """Only a question that really duplicates new_feature is merged."""
    survey = await _merged_survey(_user_form(*questions, TAP_QUESTION))

    assert kept in set(survey["name"])
    assert "new_feature" in set(survey["name"])


async def test_only_first_user_geopoint_merges():
    """A second point question is separate data, such as the end of a route."""
    survey = await _merged_survey(
        _user_form(
            ["geopoint", "route_start", "Start", "", ""],
            ["geopoint", "route_end", "End", "", ""],
        )
    )

    assert geometry_questions_in(survey) == ["new_feature", "route_end"]


async def _qfield_survey(form: BytesIO) -> pd.DataFrame:
    """The survey sheet sent to xlsform2qgis for a user's form."""
    _, updated = await append_field_mapping_fields(form)
    _, qfield_form = await modify_form_for_qfield(updated)
    return pd.read_excel(BytesIO(qfield_form.getvalue()), sheet_name="survey").fillna("")


async def test_qfield_form_keeps_one_geometry_question():
    """QField layers have one geometry, so other questions merge into it."""
    survey = await _qfield_survey(
        _user_form(
            ["geopoint", "route_start", "Start", "", ""],
            ["gps", "route_end", "End", "", ""],
            ["geoshape", "outline", "Outline", "", ""],
            ["text", "tap_name", "Tap name", "", "${route_start} != '' and ${route_endpoint} = ''"],
        )
    )

    assert geometry_questions_in(survey) == ["feature"]
    assert survey[survey["name"] == "tap_name"].iloc[0]["relevant"] == (
        f"{QFIELD_GEOMETRY_EXPRESSION} != '' and ${{route_endpoint}} = ''"
    )


async def test_qfield_form_keeps_repeated_geometry_questions():
    """Repeats become child layers in QField, each with its own geometry."""
    survey = await _qfield_survey(
        _user_form(
            ["begin repeat", "taps", "Taps", "", ""],
            ["geopoint", "tap_location", "Tap", "", ""],
            ["end repeat", "taps", "", "", ""],
        )
    )

    assert geometry_questions_in(survey) == ["feature", "tap_location"]


async def test_qfield_form_drops_group_emptied_by_merge():
    """A group holding only a merged geometry question goes with it."""
    survey = await _qfield_survey(
        _user_form(
            ["begin group", "location", "Location", "", ""],
            ["geopoint", "spot", "Where?", "", ""],
            ["end group", "", "", "", ""],
            TAP_QUESTION,
        )
    )

    assert "location" not in set(survey["name"])
    assert "tap_name" in set(survey["name"])


def test_processed_form_options_from_older_form():
    """Forms stored before default_language and the photos repeat still work."""
    workbook = Workbook()
    survey = workbook.active
    survey.title = "survey"
    survey.append(["type", "name", "required"])
    survey.append(["image", "image", "yes"])
    workbook.create_sheet("settings").append(["form_id"])
    workbook["settings"].append(["stored-form-id"])
    form = BytesIO()
    workbook.save(form)

    assert get_processed_form_options(form.getvalue()) == {
        "form_id": "stored-form-id",
        "default_language": None,
        "need_verification_fields": False,
        "include_photo_upload": True,
        "mandatory_photo_upload": True,
        "new_point_capture": NewPointCapture.MAP,
    }


def check_survey_sheet(workbook: Workbook) -> None:
    """Check the 'survey' sheet values and ensure no duplicates in 'name' column."""
    survey_sheet = get_sheet(workbook, "survey")
    name_col_index = get_column_index(survey_sheet, "name")
    calculation_col_index = get_column_index(survey_sheet, "calculation")
    check_for_duplicates(survey_sheet, name_col_index)


def check_entities_sheet(workbook: Workbook) -> None:
    """Check the 'entities' sheet values."""
    entities_sheet = get_sheet(workbook, "entities")
    label_col_index = get_column_index(entities_sheet, "label")

    test_label_present = any(
        row[0].value == "test label"
        for row in entities_sheet.iter_rows(min_col=label_col_index, max_col=label_col_index, min_row=2)
    )
    assert not test_label_present, "'test label' found in the 'label' column of 'entities' sheet."


def check_form_title(workbook: Workbook) -> None:
    """Check if the form_title is set correctly in the 'settings' sheet."""
    settings_sheet = get_sheet(workbook, "settings")
    form_title_col_index = get_column_index(settings_sheet, "form_title")

    form_title_value = settings_sheet.cell(row=2, column=form_title_col_index).value
    # NOTE previously we would strip 's' from plurals, but we no longer do this
    assert form_title_value == "buildings", "form_title field is not set to 'building'"


def check_translation_fields(workbook: Workbook):
    """Check if translation fields for all included languages were correctly matched."""
    survey_sheet = workbook["survey"]
    header = [cell.value for cell in next(survey_sheet.iter_rows(min_row=1, max_row=1))]

    if "label" in header: # Allow bare 'label' column without translations
        return

    found_langs = set()
    for col in header:
        if not col or not col.startswith("label::"):
            continue

        match = re.match(r"label::([^(]+)(?:\(([^)]+)\))?", col)
        if not match:
            continue

        lang_key = match.group(1).strip().lower()
        lang_code = match.group(2) or INCLUDED_LANGUAGES.get(lang_key)
        if lang_key in INCLUDED_LANGUAGES and lang_code == INCLUDED_LANGUAGES[lang_key]:
            found_langs.add(lang_key)

    assert found_langs.issubset(INCLUDED_LANGUAGES.keys()), (
        f"Unexpected translation columns: {found_langs - INCLUDED_LANGUAGES.keys()}"
    )


def get_sheet(workbook: Workbook, sheet_name: str) -> worksheet.worksheet.Worksheet:
    """Helper function to get a sheet or raise an error."""
    if sheet_name not in workbook.sheetnames:
        raise ValueError(f"The '{sheet_name}' sheet was not found in the workbook")
    return workbook[sheet_name]


def check_for_duplicates(sheet: worksheet.worksheet.Worksheet, col_index: int) -> None:
    """Check for any duplicate values in a specific column of a sheet, ignoring None values."""
    seen_values = set()
    for row in sheet.iter_rows(min_col=col_index, max_col=col_index, min_row=2):
        value = row[0].value
        if value is None:
            # Skip None values, allowing them to appear multiple times
            continue
        if value in seen_values:
            raise AssertionError(f"Duplicate value '{value}' found in column '{col_index}' of sheet '{sheet.title}'.")
        seen_values.add(value)


def get_column_index(sheet: worksheet.worksheet.Worksheet, column_name: str) -> int:
    """Get the column index for the given column name."""
    for col_idx, col in enumerate(sheet.iter_cols(1, sheet.max_column), start=1):
        if col[0].value == column_name:
            return col_idx
    raise ValueError(f"Column '{column_name}' not found.")


def get_row_index(sheet: worksheet.worksheet.Worksheet, column_index: int, value: str) -> int:
    """Get the row index where the given column has the specified value."""
    for row_idx, row in enumerate(sheet.iter_rows(min_col=column_index, max_col=column_index), start=1):
        if row[0].value == value:
            return row_idx
    raise ValueError(f"Value '{value}' not found in column {column_index}.")
