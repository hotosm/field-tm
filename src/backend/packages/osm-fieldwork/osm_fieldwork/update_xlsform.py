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
from uuid import uuid4

import pandas as pd
from python_calamine.pandas import pandas_monkeypatch

from osm_fieldwork.form_components.choice_fields import choices_df, digitisation_choices_df
from osm_fieldwork.form_components.digitisation_fields import digitisation_df
from osm_fieldwork.form_components.mandatory_fields import DbGeomType, create_survey_df, entities_df, meta_df
from osm_fieldwork.xlsforms import xlsforms_path

log = logging.getLogger(__name__)

# Monkeypatch pandas to add calamine driver
pandas_monkeypatch()

# Constants
FEATURE_COLUMN = "feature"
NAME_COLUMN = "name"
TYPE_COLUMN = "type"
DEFAULT_LANGUAGES = {
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "swahili": "sw",
    "nepali": "ne",
    "portuguese": "pt-BR",
}

# def handle_translations(
#     mandatory_df: pd.DataFrame, user_question_df: pd.DataFrame, digitisation_df: pd.DataFrame, fields: list[str]
# ):
#     """Handle translations, defaulting to English if no translations are present.

#     Handles all field types that can be translated, such as
#     'label', 'hint', 'required_message'.
#     """
#     for field in fields:
#         # Identify translation columns for this field in the user_question_df
#         translation_columns = [col for col in user_question_df.columns if col.startswith(f"{field}::")]

#         if field in user_question_df.columns and not translation_columns:
#             # If user_question_df has only the base field (e.g., 'label'), map English translation from mandatory and digitisation
#             mandatory_df[field] = mandatory_df.get(f"{field}::english(en)", mandatory_df.get(field))
#             digitisation_df[field] = digitisation_df.get(f"{field}::english(en)", digitisation_df.get(field))

#             # Then drop translation columns
#             mandatory_df = mandatory_df.loc[:, ~mandatory_df.columns.str.startswith("label::")]
#             digitisation_df = digitisation_df.loc[:, ~digitisation_df.columns.str.startswith("label::")]

#         else:
#             # If translation columns exist, match them for mandatory and digitisation dataframes
#             for col in translation_columns:
#                 mandatory_col = mandatory_df.get(col)
#                 digitisation_col = digitisation_df.get(col)
#                 if mandatory_col is not None:
#                     mandatory_df[col] = mandatory_col
#                 if digitisation_col is not None:
#                     digitisation_df[col] = digitisation_col

#     return mandatory_df, user_question_df, digitisation_df


def standardize_xlsform_sheets(xlsform: dict) -> dict:
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
                        if lang_name in DEFAULT_LANGUAGES:
                            standardized_col = f"{base_col}::{lang_name}({DEFAULT_LANGUAGES[lang_name]})"

                elif col == base_col:  # if only label,hint or required_message then add '::english(en)'
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

    for sheet_name, sheet_df in xlsform.items():
        if sheet_df.empty:
            continue
        # standardize the language columns
        sheet_df = standardize_language_columns(sheet_df)
        sheet_df = filter_df_empty_rows(sheet_df)
        xlsform[sheet_name] = sheet_df

    return xlsform


def create_survey_group() -> dict[str, pd.DataFrame]:
    """Helper function to create a begin and end group for XLSForm."""
    begin_group = pd.DataFrame(
        {
            "type": ["begin group"],
            "name": ["survey_questions"],
            "label::english(en)": ["Survey Questions"],
            "label::swahili(sw)": ["Maswali ya Utafiti"],
            "label::french(fr)": ["Questions de l'enquête"],
            "label::spanish(es)": ["Preguntas de la encuesta"],
            "label::portuguese(pt-BR)": ["Perguntas da pesquisa"],
            "label::nepali(ne)": ["सर्वेक्षण प्रश्नहरू"],
            "relevant": "(${new_feature} != '') or (${building_exists} = 'yes')",
        }
    )
    end_group = pd.DataFrame(
        {
            "type": ["end group"],
        }
    )
    return {"begin": begin_group, "end": end_group}


def normalize_with_meta(row, meta_df):
    """Replace metadata in user_question_df with metadata from meta_df of mandatory fields if exists."""
    matching_meta = meta_df[meta_df["type"] == row[TYPE_COLUMN]]
    if not matching_meta.empty:
        for col in matching_meta.columns:
            row[col] = matching_meta.iloc[0][col]
    return row


def merge_dataframes(mandatory_df: pd.DataFrame, user_question_df: pd.DataFrame, digitisation_df: pd.DataFrame) -> pd.DataFrame:
    """Merge multiple Pandas dataframes together, removing duplicate fields."""
    if "list_name" in user_question_df.columns:
        merged_df = pd.concat(
            [
                mandatory_df,
                user_question_df,
                digitisation_df,
            ],
            ignore_index=True,
        )
        # NOTE here we remove duplicate PAIRS based on `list_name` and the name column
        # we have `allow_duplicate_choices` set in the settings sheet, so it is possible
        # to have duplicate NAME_COLUMN entries, if they are in different a `list_name`.
        return merged_df.drop_duplicates(subset=["list_name", NAME_COLUMN], ignore_index=True)

    user_question_df = user_question_df.apply(normalize_with_meta, axis=1, meta_df=meta_df)

    # Find common fields between user_question_df and mandatory_df or digitisation_df
    duplicate_fields = set(user_question_df[NAME_COLUMN]).intersection(
        set(mandatory_df[NAME_COLUMN]).union(set(digitisation_df[NAME_COLUMN]))
    )

    # NOTE filter out 'end group' from duplicate check as they have empty NAME_COLUMN
    end_group_rows = user_question_df[user_question_df["type"].isin(["end group", "end_group"])]
    user_question_df_filtered = user_question_df[
        (~user_question_df[NAME_COLUMN].isin(duplicate_fields)) | (user_question_df.index.isin(end_group_rows.index))
    ]

    # Create survey group wrapper
    survey_group = create_survey_group()

    # Concatenate dataframes in the desired order
    return pd.concat(
        [
            mandatory_df,
            # Wrap the survey question in a group
            survey_group["begin"],
            user_question_df_filtered,
            survey_group["end"],
            digitisation_df,
        ],
        ignore_index=True,
    )


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


async def append_mandatory_fields(
    custom_form: BytesIO,
    form_name: str = f"fmtm_{uuid4()}",
    additional_entities: list[str] = None,
    new_geom_type: DbGeomType = DbGeomType.POINT,
) -> tuple[str, BytesIO]:
    """Append mandatory fields to the XLSForm for use in FMTM.

    Args:
        custom_form(BytesIO): the XLSForm data uploaded, wrapped in BytesIO.
        form_name(str): the friendly form name in ODK web view.
        additional_entities(list[str]): add extra select_one_from_file fields to
            reference an additional Entity list (set of geometries).
        new_geom_type (DbGeomType): the type of geometry required when collecting
            new geometry data: point, line, polygon.

    Returns:
        tuple(str, BytesIO): the xFormId + the update XLSForm wrapped in BytesIO.
    """
    log.info("Appending field mapping questions to XLSForm")
    custom_sheets = pd.read_excel(custom_form, sheet_name=None, engine="calamine")

    if "survey" not in custom_sheets:
        msg = "Survey sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)

    custom_sheets = standardize_xlsform_sheets(custom_sheets)

    log.debug("Merging survey sheet XLSForm data")
    survey_df = create_survey_df(new_geom_type)
    custom_sheets["survey"] = merge_dataframes(survey_df, custom_sheets.get("survey"), digitisation_df)

    # Ensure the 'choices' sheet exists in custom_sheets
    if "choices" not in custom_sheets or custom_sheets["choices"] is None:
        custom_sheets["choices"] = pd.DataFrame(columns=["list_name", "name", "label::english(en)"])

    log.debug("Merging choices sheet XLSForm data")
    custom_sheets["choices"] = merge_dataframes(choices_df, custom_sheets.get("choices"), digitisation_choices_df)

    # Append or overwrite 'entities' and 'settings' sheets
    log.debug("Overwriting entities and settings XLSForm sheets")
    custom_sheets["entities"] = entities_df
    if "entities" not in custom_sheets:
        msg = "Entities sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)
    if "settings" not in custom_sheets:
        msg = "Settings sheet is required in XLSForm!"
        log.error(msg)
        raise ValueError(msg)

    # Extract existing form id if present, else set to random uuid
    if "form_id" in custom_sheets["settings"]:
        xform_id = custom_sheets["settings"]["form_id"].iloc[0]
        log.debug(f"Extracted existing form_id field: {xform_id}")
    else:
        xform_id = str(uuid4())

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.debug(f"Setting xFormId = {xform_id} | version = {current_datetime} | form_name = {form_name}")

    # Set the 'version' column to the current timestamp
    custom_sheets["settings"]["version"] = current_datetime
    custom_sheets["settings"]["form_id"] = xform_id
    custom_sheets["settings"]["form_title"] = form_name
    if "default_language" not in custom_sheets["settings"]:
        custom_sheets["settings"]["default_language"] = "en"

    # Append select_one_from_file for additional entities
    if additional_entities:
        log.debug("Adding additional entity list reference to XLSForm")
        for entity_name in additional_entities:
            custom_sheets["survey"] = append_select_one_from_file_row(custom_sheets["survey"], entity_name)

    # Return spreadsheet wrapped as BytesIO memory object
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in custom_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return (xform_id, output)


async def main():
    """Used for the `fmtm_xlsform` CLI command."""
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

    form_id, form_bytes = await append_mandatory_fields(
        custom_form=input_xlsform,
        form_name=f"fmtm_{uuid4()}",
        additional_entities=args.additional_dataset_names,
        new_geom_type=args.new_geom_type,
    )

    log.info(f"Form ({form_id}) created successfully")
    with open(args.output, "wb") as file_handle:
        file_handle.write(form_bytes.getvalue())


if __name__ == "__main__":
    """Wrap for running the file directly."""
    asyncio.run(main())
