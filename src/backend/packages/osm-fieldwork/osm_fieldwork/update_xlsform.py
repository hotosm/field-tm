#!/usr/bin/python3

# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

"""Update an existing XLSForm with additional fields useful for field mapping."""

import argparse
import asyncio
import logging
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pandas as pd
from python_calamine.pandas import pandas_monkeypatch

from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.form_components.choice_fields import get_choice_fields, generate_task_id_choices
from osm_fieldwork.form_components.mandatory_fields import (
    meta_df,
    create_survey_df,
    get_photo_collection_field,
    create_entity_df,
)
from osm_fieldwork.form_components.digitisation_fields import (
    digitisation_fields,
    digitisation_choices, 
)
from osm_fieldwork.form_components.translations import INCLUDED_LANGUAGES, add_label_translations
from osm_fieldwork.xlsforms import xlsforms_path

log = logging.getLogger(__name__)

# Monkeypatch pandas to add calamine driver
pandas_monkeypatch()

# Constants
FEATURE_COLUMN = "feature"
NAME_COLUMN = "name"
TYPE_COLUMN = "type"

def standardize_xlsform_sheets(xlsform: dict):
    """Standardizes column headers in both the 'survey' and 'choices' sheets of an XLSForm.

    - Strips spaces and lowercases all column headers.
    - Fixes formatting for columns with '::' (e.g., multilingual labels).

    Args:
        xlsform (dict): A dictionary with keys 'survey' and 'choices', each containing a DataFrame.

    Returns:
        dict: The updated XLSForm dictionary with standardized column headers.
    """

    def standardize_language_columns(df):
        """Standardize existing language columns.

        :param df: Original DataFrame with existing translations.
        :param DEFAULT_LANGAUGES: List of DEFAULT_LANGAUGES with their short codes, e.g., {"english": "en", "french": "fr"}.
        :param base_columns: List of base columns to check (e.g., 'label', 'hint', 'required_message').
        :return: Updated DataFrame with standardized and complete language columns.
        """
        base_columns = ["label", "hint", "required_message"]
        df.columns = df.columns.str.lower()
        existing_columns = df.columns.tolist()

        # Map existing columns and standardize their names
        for col in existing_columns:
            standardized_col = col
            for base_col in base_columns:
                if col.startswith(f"{base_col}::"):
                    match = re.match(rf"{base_col}::\s*(\w+)", col)
                    if match:
                        lang_name = match.group(1)
                        if lang_name in INCLUDED_LANGUAGES:
                            standardized_col = f"{base_col}::{lang_name}({INCLUDED_LANGUAGES[lang_name]})"

                elif col == base_col and col != "label":  # if only label,hint or required_message then add '::english(en)'
                    standardized_col = f"{base_col}::english(en)"

                if col != standardized_col:
                    df.rename(columns={col: standardized_col}, inplace=True)
        return df

    def filter_df_empty_rows(df: pd.DataFrame, column: str = NAME_COLUMN):
        """Remove rows with None values in the specified column.

        NOTE We retain 'end group' and 'end group' rows even if they have no name.
        NOTE A generic df.dropna(how="all") would not catch accidental spaces etc.
        """
        if column in df.columns:
            # Only retain 'begin group' and 'end group' if 'type' column exists
            if "type" in df.columns:
                return df[(df[column].notna()) | (df["type"].isin(["begin group", "end group", "begin_group", "end_group"]))]
            else:
                return df[df[column].notna()]
        return df

    label_cols = set()
    for sheet_name, sheet_df in xlsform.items():
        if sheet_df.empty:
            continue
        # standardize the language columns
        sheet_df = standardize_language_columns(sheet_df)
        sheet_df = filter_df_empty_rows(sheet_df)
        label_cols.update(
            [col for col in sheet_df.columns if "label" in col.lower()]
        )
        xlsform[sheet_name] = sheet_df

    return xlsform, list(label_cols)


def normalize_with_meta(row, meta_df):
    """Replace metadata in user_question_df with metadata from meta_df of mandatory fields if exists."""
    matching_meta = meta_df[meta_df["type"] == row[TYPE_COLUMN]]
    if not matching_meta.empty:
        for col in matching_meta.columns:
            row[col] = matching_meta.iloc[0][col]
    return row


def merge_dataframes(
        mandatory_df: pd.DataFrame, 
        user_question_df: pd.DataFrame, 
        add_label: bool,
        digitisation_df: Optional[pd.DataFrame] = None,
        photo_collection_df: Optional[pd.DataFrame] = None,
        need_verification: Optional[bool] = True,
    ) -> pd.DataFrame:
    """
    Merge multiple Pandas dataframes together, removing duplicate fields.
    
    Arguments:
        mandatory_df: DataFrame containing required fields
        user_question_df: DataFrame containing user-specified questions
        digitisation_df: Optional DataFrame with digitisation fields
        photo_collection_df: Optional DataFrame with photo collection fields
        need_verification: Include geom verifiction questions
    
    Returns:
        pd.DataFrame: Merged DataFrame with duplicates removed
    """
    # If list_name present, use simpler merge logic
    if "list_name" in user_question_df.columns:
        frames = [mandatory_df, user_question_df]
        if digitisation_df is not None:
            frames.append(digitisation_df)
        if photo_collection_df is not None:
            frames.append(photo_collection_df)
        merged_df = pd.concat(frames, ignore_index=True)
        # NOTE here we remove duplicate PAIRS based on `list_name` and the name column
        return merged_df.drop_duplicates(subset=["list_name", NAME_COLUMN], ignore_index=True)
    
    # Normalize user questions if meta_df provided
    if meta_df is not None:
        user_question_df = user_question_df.apply(
            lambda row: normalize_with_meta(row, meta_df), 
            axis=1
        )
    
    # NOTE filter out 'end group' from duplicate check as they have empty NAME_COLUMN
    is_end_group = user_question_df["type"].isin(["end group", "end_group"])
    
    # Find duplicate fields
    digitisation_names = set() if digitisation_df is None else set(digitisation_df[NAME_COLUMN])
    photo_collection_names = set() if photo_collection_df is None else set(photo_collection_df[NAME_COLUMN])
    all_existing_names = set(mandatory_df[NAME_COLUMN]).union(digitisation_names).union(photo_collection_names)
    duplicate_fields = set(user_question_df[NAME_COLUMN]).intersection(all_existing_names)
    
    # Filter out duplicates but keep end group rows
    user_question_df_filtered = user_question_df[
        (~user_question_df[NAME_COLUMN].isin(duplicate_fields)) | is_end_group
    ]
    
    # We wrap the survey question in a group to easily disable all questions if the
    # feature does not exist. If we don't have the `feature_exists` question, then
    # wrapping in the group is unnecessary (all groups are flattened in processing anyway)
    if need_verification:
        survey_group_field = {
            "type": ["begin group"],
            "name": ["survey_questions"],
            "relevant": "(${feature_exists} = 'yes') or (${status} = '2')",
        }
        if add_label:
            survey_group_field = add_label_translations(survey_group_field)
        survey_group = {
            "begin": (
                pd.DataFrame(
                    survey_group_field
                )
            ),
            "end": pd.DataFrame({"type": ["end group"]}
        )}

    else:
        # Do not include the survey group wrapper (empty dataframes)
        survey_group = {"begin": pd.DataFrame(), "end": pd.DataFrame()}

    
    frames = [
        mandatory_df,
        survey_group["begin"],
        user_question_df_filtered,
        survey_group["end"],
    ]
    
    if digitisation_df is not None:
        frames.append(digitisation_df)
    if photo_collection_df is not None:
        frames.append(photo_collection_df)
    
    return pd.concat(frames, ignore_index=True)


def append_select_one_from_file_row(df: pd.DataFrame, entity_name: str) -> pd.DataFrame:
    """Add a new select_one_from_file question to reference an Entity."""
    # Find the row index where name column = 'feature'
    select_one_from_file_index = df.index[df[NAME_COLUMN] == FEATURE_COLUMN].tolist()
    if not select_one_from_file_index:
        raise ValueError(f"Row with '{NAME_COLUMN}' == '{FEATURE_COLUMN}' not found in survey sheet.")

    # Find the row index after 'feature' row
    row_index_to_split_on = select_one_from_file_index[0] + 1

    additional_row = pd.DataFrame(
        {
            "type": [f"select_one_from_file {entity_name}.csv"],
            "name": [entity_name],
            "appearance": ["map"],
            "label::english(en)": [entity_name],
            "label::swahili(sw)": [entity_name],
            "label::french(fr)": [entity_name],
            "label::spanish(es)": [entity_name],
        }
    )

    # Prepare the row for calculating coordinates based on the additional entity
    coordinates_row = pd.DataFrame(
        {
            "type": ["calculate"],
            "name": [f"{entity_name}_geom"],
            "calculation": [f"instance('{entity_name}')/root/item[name=${{{entity_name}}}]/geometry"],
            "label::english(en)": [f"{entity_name}_geom"],  # translations not needed, calculated field
        }
    )
    # Insert the new row into the DataFrame
    top_df = df.iloc[:row_index_to_split_on]
    bottom_df = df.iloc[row_index_to_split_on:]
    return pd.concat([top_df, additional_row, coordinates_row, bottom_df], ignore_index=True)


async def _process_all_form_tabs(
    custom_sheets: pd.DataFrame,
    form_name: str = f"fmtm_{uuid4()}",
    additional_entities: Optional[list[str]] = None,
    new_geom_type: DbGeomType = DbGeomType.POINT,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
    label_cols: list[str] = [],
) -> tuple[str, pd.DataFrame]:
    if "label" in label_cols:
        add_label = False
        digitisation_df = pd.DataFrame([
            add_label_translations(field, label_cols)
            for field in digitisation_fields
        ])
        digitisation_choices_df = pd.DataFrame([
            add_label_translations(choice)
            for choice in digitisation_choices
        ])
        choices_df = pd.DataFrame([
            add_label_translations(choice, label_cols)
            for choice in get_choice_fields(use_odk_collect)
        ])
        photo_collection_df = pd.DataFrame([
            add_label_translations(get_photo_collection_field(mandatory_photo_upload), label_cols)
        ])
    else:
        add_label = True
        digitisation_df = pd.DataFrame([
            add_label_translations(field)
            for field in digitisation_fields
        ])
        digitisation_choices_df = pd.DataFrame([
            add_label_translations(choice)
            for choice in digitisation_choices
        ])
        choices_df = pd.DataFrame([
            add_label_translations(choice)
            for choice in get_choice_fields(use_odk_collect)
        ])
        photo_collection_df = pd.DataFrame([
            add_label_translations(get_photo_collection_field(mandatory_photo_upload))
        ])

    # Configure form settings
    xform_id = _configure_form_settings(custom_sheets, form_name)

    # Select appropriate form components based on target platform
    form_components = _get_form_components(use_odk_collect, new_geom_type, need_verification_fields, choices_df, digitisation_df, digitisation_choices_df, photo_collection_df, label_cols)
    
    # Process survey sheet
    custom_sheets["survey"] = _process_survey_sheet(
        custom_sheets.get("survey"),
        form_components["survey_df"],
        form_components["digitisation_df"] if need_verification_fields else None,
        form_components["photo_collection_df"],
        add_label = add_label,
        need_verification=need_verification_fields,
    )
    
    # Process choices sheet
    custom_sheets["choices"] = _process_choices_sheet(
        custom_sheets.get("choices"), 
        form_components["choices_df"],
        form_components["digitisation_choices_df"],
        add_label = add_label,
    )

    # Process entities and settings sheets
    custom_sheets["entities"] = form_components["entities_df"]
    _validate_required_sheet(custom_sheets, "entities")
    
    # Handle additional entities if specified
    if additional_entities:
        custom_sheets["survey"] = _add_additional_entities(custom_sheets["survey"], additional_entities)

    return (xform_id, custom_sheets)


async def write_xlsform(form_content: pd.DataFrame) -> BytesIO:
    """Write the dataframe to Excel wrapped in BytesIO object."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in form_content.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output


async def append_field_mapping_fields(
    custom_form: BytesIO,
    form_name: str = f"fmtm_{uuid4()}",
    additional_entities: Optional[list[str]] = None,
    new_geom_type: DbGeomType = DbGeomType.POINT,
    need_verification_fields: bool = True,
    mandatory_photo_upload: bool = False,
    use_odk_collect: bool = False,
) -> tuple[str, BytesIO]:
    """Append mandatory fields to the XLSForm for use in Field-TM.

    Args:
        custom_form (BytesIO): The XLSForm data uploaded, wrapped in BytesIO.
        form_name (str): The friendly form name in ODK web view.
        additional_entities (list[str], optional): Add extra select_one_from_file fields to
            reference additional Entity lists (sets of geometries). Defaults to None.
        new_geom_type (DbGeomType): The type of geometry required when collecting
            new geometry data: point, line, polygon. Defaults to DbGeomType.POINT.
        need_verification_fields (bool): Whether to include verification fields.
            Defaults to True.
        use_odk_collect (bool): Whether to use ODK Collect-specific components.
            Defaults to False.

    Returns:
        tuple[str, BytesIO]: The xFormId and the updated XLSForm wrapped in BytesIO.
        
    Raises:
        ValueError: If required sheets are missing from the XLSForm.
    """
    log.info("Appending field mapping questions to XLSForm")

    custom_sheets = pd.read_excel(custom_form, sheet_name=None, engine="calamine")
    if "survey" not in custom_sheets:
        msg = "Survey sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)
    
    custom_sheets, label_cols = standardize_xlsform_sheets(custom_sheets)  # Also get the label columns
    xformid, updated_form = await _process_all_form_tabs(
        custom_sheets=custom_sheets,
        form_name=form_name,
        additional_entities=additional_entities,
        new_geom_type=new_geom_type,
        need_verification_fields=need_verification_fields,
        mandatory_photo_upload=mandatory_photo_upload,
        use_odk_collect=use_odk_collect,
        label_cols=label_cols,
    )
    return (xformid, await write_xlsform(updated_form))


async def append_task_id_choices(
    existing_form: BytesIO,
    task_ids: list[int],
) -> BytesIO:
    """From the previously modified form, add the final task_filter choices."""

    task_id_choice_df = generate_task_id_choices(task_ids)

    existing_sheets = pd.read_excel(existing_form, sheet_name=None, engine="calamine")
    if "choices" not in existing_sheets:
        raise ValueError("Choices sheet is required in XLSForm!")

    choices_df = existing_sheets["choices"]

    # Ensure translation columns exist in BOTH dataframes
    for lang_name, lang_key in INCLUDED_LANGUAGES.items():
        label_key = f"label::{lang_name}({lang_key})"
        if label_key not in choices_df.columns:
            choices_df[label_key] = ""
        if label_key not in task_id_choice_df.columns:
            task_id_choice_df[label_key] = ""

    # Append new rows
    choices_df = pd.concat([choices_df, task_id_choice_df], ignore_index=True)

    # Fill translations for new rows (string compare to avoid int/str mismatch)
    for lang_name, lang_key in INCLUDED_LANGUAGES.items():
        label_key = f"label::{lang_name}({lang_key})"
        for task_id in task_ids:
            mask = choices_df["name"].astype(str) == str(task_id)
            choices_df.loc[mask, label_key] = str(task_id)

    # Drop plain "label" if translations exist
    if "label" in choices_df.columns:
        choices_df = choices_df.drop(columns=["label"])

    existing_sheets["choices"] = choices_df

    return await write_xlsform(existing_sheets)


async def modify_form_for_qfield(
    custom_form: BytesIO,
    geom_layer_type: DbGeomType = DbGeomType.POINT,
) -> tuple[Optional[str], BytesIO]:
    """Append mandatory fields to the XLSForm for use in QField.

    Args:
        custom_form (BytesIO): The XLSForm data uploaded, wrapped in BytesIO.
        new_geom_type (DbGeomType): The type of geometry required when collecting
            new geometry data: point, line, polygon. Defaults to DbGeomType.POINT.

    Returns:
        tuple[str, BytesIO]: The updated XLSForm wrapped in BytesIO.
        
    Raises:
        ValueError: If required sheets are missing from the XLSForm.
    """
    log.info("Modifying XLSForm to work with QField")

    custom_sheets = pd.read_excel(custom_form, sheet_name=None, engine="calamine")
    if "survey" not in custom_sheets:
        msg = "Survey sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)

    # Get first available language in format 'english(en)'
    form_languages = []
    all_columns = custom_sheets["survey"].columns.tolist()
    for col_name in all_columns:
        if "::" in col_name:
            form_languages.append(col_name)
    form_language = form_languages[0].split("::")[1] if form_languages else None
    if (total_languages := len(form_languages)) > 1:
        log.warning(
            f"Found {total_languages} form translations, but only the first will "
            f"be used {form_language}"
        )

    # 1. Replace the "select_one_from_file features.csv"
    #    row with a geometry field
    qf_survey_df = custom_sheets["survey"]
    geom_type_map = {
        DbGeomType.POINT: "geopoint",
        DbGeomType.POLYGON: "geoshape",
        DbGeomType.LINESTRING: "geotrace",
    }
    geom_type = geom_type_map.get(geom_layer_type, "geopoint")
    geom_field_mask = qf_survey_df["type"] == "select_one_from_file features.csv"
    if geom_field_mask.any():
        idx = qf_survey_df.index[geom_field_mask][0]
        # Build the replacement row
        replacement = qf_survey_df.iloc[idx:idx+1].copy()
        replacement.loc[:, "type"] = geom_type
        replacement.loc[:, "name"] = "feature"
        # Replace the row
        qf_survey_df = pd.concat(
            [qf_survey_df.iloc[:idx], replacement, qf_survey_df.iloc[idx+1:]]
        ).reset_index(drop=True)

    # 2. Remove the 'start-geopoint' field we add as mandatory fields for ODK
    #    - this breaks XLSFormConverter identifying the correct geom type
    start_geopoint_mask = qf_survey_df["type"] == "start-geopoint"
    if start_geopoint_mask.any():
        qf_survey_df = qf_survey_df[~start_geopoint_mask].reset_index(drop=True)

    # 3. Wrap the final two rows (end_note, image) in a group,
    #    so they display correctly as final QField tab
    last_two_rows = qf_survey_df.tail(2)
    begin_row = pd.DataFrame([{"type": "begin group", "name": "final"}])
    end_row = pd.DataFrame([{"type": "end group", "name": None}])
    # Rebuild: all rows except last two + begin + last two + end
    qf_survey_df = pd.concat(
        [qf_survey_df.iloc[:-2], begin_row, last_two_rows, end_row],
        ignore_index=True,
    )

    # 4. Update survey sheet in updated_form
    custom_sheets["survey"] = qf_survey_df

    return (form_language, await write_xlsform(custom_sheets))


def _get_form_components(
        use_odk_collect: bool,
        new_geom_type: DbGeomType,
        need_verification_fields: bool,
        choices_df: pd.DataFrame,
        digitisation_df: pd.DataFrame,
        digitisation_choices_df: pd.DataFrame,
        photo_collection_df: pd.DataFrame,
        label_cols: list[str],
    ) -> dict:
    """Select appropriate form components based on target platform."""
    if use_odk_collect:
        # Here we modify digitisation_df to include the `new_feature` field
        # NOTE we set digitisation_correct to 'yes' if the user is drawing a new geometry
        digitisation_correct_col = digitisation_df["name"] == "digitisation_correct"
        digitisation_df.loc[digitisation_correct_col, "calculation"] = "once(if(${new_feature} != '', 'yes', ''))"
        digitisation_df.loc[digitisation_correct_col, "read_only"] = "${new_feature} != ''"

    return {
        "survey_df": create_survey_df(use_odk_collect, new_geom_type, need_verification_fields, label_cols),
        "choices_df": choices_df,
        "digitisation_df": digitisation_df,
        "photo_collection_df": photo_collection_df,
        "digitisation_choices_df": digitisation_choices_df,
        "entities_df": create_entity_df(use_odk_collect)
    }


def _process_survey_sheet(
        existing_survey: pd.DataFrame, 
        survey_df: pd.DataFrame, 
        digitisation_df: pd.DataFrame,
        photo_collection_df: pd.DataFrame,
        add_label: bool,
        need_verification: Optional[bool] = True,
    ) -> pd.DataFrame:
    """Process and merge survey sheets."""
    log.debug("Merging survey sheet XLSForm data")
    return merge_dataframes(
        survey_df,
        existing_survey,
        add_label=add_label,
        digitisation_df=digitisation_df,
        photo_collection_df=photo_collection_df,
        need_verification=need_verification,
    )


def _process_choices_sheet(
        existing_choices: pd.DataFrame, 
        choices_df: pd.DataFrame, 
        digitisation_choices_df: pd.DataFrame,
        add_label: bool,
    ) -> pd.DataFrame:
    """Process and merge choices sheets."""
    log.debug("Merging choices sheet XLSForm data")
    # Ensure the 'choices' sheet exists with required columns
    if existing_choices is None:
        existing_choices = pd.DataFrame(columns=["list_name", "name", "label::english(en)"])
    
    return merge_dataframes(
        choices_df,
        existing_choices,
        add_label=add_label,
        digitisation_df=digitisation_choices_df,
    )


def _validate_required_sheet(
        custom_sheets: dict, sheet_name: str
    ) -> None:
    """Validate that a required sheet exists."""
    if sheet_name not in custom_sheets:
        msg = f"{sheet_name} sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)


def _configure_form_settings(custom_sheets: dict, form_name: str) -> str:
    """Configure form settings and extract/set form ID.
    
    Args:
        custom_sheets: Dictionary containing dataframes for each sheet
        form_name: Name of the form to be used as form_title
        
    Returns:
        str: The form ID (xform_id)
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Check if settings sheet exists and create if needed
    if "settings" not in custom_sheets or custom_sheets["settings"].empty:
        xform_id = str(uuid4())
        custom_sheets["settings"] = pd.DataFrame([{
            "form_id": xform_id,
            "version": current_datetime,
            "form_title": form_name,
            "allow_choice_duplicates": "yes",
            "default_language": "en"
        }])
        
        log.debug(f"Created default settings with form_id: {xform_id}")
        return xform_id
    
    # Work with existing settings
    settings = custom_sheets["settings"]
    
    # Extract existing form id if present, else set to random uuid
    xform_id = settings["form_id"].iloc[0] if "form_id" in settings else str(uuid4())
    log.debug(f"Using form_id: {xform_id}")

    # Update settings
    log.debug(f"Setting xFormId = {xform_id} | version = {current_datetime} | form_name = {form_name}")
    
    settings["version"] = current_datetime
    settings["form_id"] = xform_id
    settings["form_title"] = form_name
    
    if "default_language" not in settings:
        settings["default_language"] = "en"
    
    return xform_id


def _add_additional_entities(
        survey_df: pd.DataFrame, 
        additional_entities: list[str]
    ) -> pd.DataFrame:
    """Add additional entity references to the survey sheet."""
    log.debug("Adding additional entity list reference to XLSForm")
    result_df = survey_df.copy()
    
    for entity_name in additional_entities:
        result_df = append_select_one_from_file_row(result_df, entity_name)
        
    return result_df


async def main():
    """Used for the `fmtm_xlsform` CLI command."""
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    parser = argparse.ArgumentParser(description="Append field mapping fields to XLSForm")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--input", help="Input XLSForm file")
    parser.add_argument("-c", "--category", help="A category of demo form to use instead")
    parser.add_argument("-o", "--output", help="Output merged XLSForm filename")
    parser.add_argument("-a", "--additional-dataset-names", help="Names of additional entity lists to append")
    parser.add_argument(
        "-n",
        "--new-geom-type",
        type=DbGeomType,
        choices=list(DbGeomType),
        help="The type of new geometry",
        default=DbGeomType.POINT,
    )
    parser.add_argument(
        "-verify",
        "--need-verification-fields",
        type=str2bool,
        nargs='?',
        const=True,
        default=True,
        help="Requirement of verification questions (true/false)",
    )
    parser.add_argument(
        "-photo",
        "--mandatory-photo-upload",
        type=str2bool,
        nargs='?',
        const=True,
        default=False,
        help="Requirement of photo upload field (true/false)",
    )
    parser.add_argument(
        "-odk",
        "--use-odk-collect",
        type=str2bool,
        nargs='?',
        const=True,
        default=False,
        help="Use of ODK Collect (true/false)",
    )
    args = parser.parse_args()

    # If verbose, dump to the terminal
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    if not args.output:
        log.error("You must provide an output file with the '-o' flag")
        parser.print_help()

    if args.input:
        input_file = Path(args.input)
    elif args.category:
        input_file = Path(f"{xlsforms_path}/{args.category}.yaml")
    else:
        log.error("Must choose one of '-i' for file input, or '-c' for category selection")
        parser.print_help()
        sys.exit(1)

    if not input_file.exists():
        log.error(f"The file does not exist: {str(input_file)}")
        sys.exit(1)

    with open(input_file, "rb") as file_handle:
        input_xlsform = BytesIO(file_handle.read())

    form_id, form_bytes = await append_field_mapping_fields(
        custom_form=input_xlsform,
        form_name=f"fmtm_{uuid4()}",
        additional_entities=args.additional_dataset_names,
        new_geom_type=args.new_geom_type,
        need_verification_fields=args.need_verification_fields,
        mandatory_photo_upload=args.mandatory_photo_upload,
        use_odk_collect=args.use_odk_collect,
    )

    log.info(f"Form ({form_id}) created successfully")
    with open(args.output, "wb") as file_handle:
        file_handle.write(form_bytes.getvalue())


def run():
    """Wrapper to run via CLI / pyproject scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    """Wrap for running the file directly."""
    run()
