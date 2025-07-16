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

"""This script generates an XLS form with mandatory fields.

For use in data collection and mapping tasks.
The generated form includes metadata, survey questions, and settings
required for compatibility with HOT's Field-TM tools.
It programmatically organizes form sections into metadata,
mandatory fields, and entities, and outputs them in a structured format.

Modules and functionalities:
- **Metadata Sheet**: Includes default metadata fields
    such as `start`, `end`, `username`, and `deviceid`.
- **Survey Sheet**: Combines metadata with mandatory fields required for Field-TM workflows.
    - `warmup` for collecting initial location.
    - `feature` for selecting map geometry from predefined options.
    - `new_feature` (ODK Collect only) for capturing GPS coordinates of new features.
    - Calculated fields such as `xid`, `xlocation`, `status`, and others.
- **Entities Sheet**: Defines entity management rules to handle mapping tasks dynamically.
    - Includes rules for entity creation and updates with user-friendly labels.
- **Settings Sheet**: Sets the form ID, version, and configuration options.
"""

import pandas as pd
from datetime import datetime

from osm_fieldwork.enums import DbGeomType
from osm_fieldwork.form_components.translations import add_label_translations


NEW_FEATURE = "${new_feature}"
FEATURE = "${feature}"
INSTANCE_ID = "${instanceID}"
INSTANCE_FEATURE = "instance('features')/root/item[name=${feature}]"
USERNAME = "${username}"
RANDOM_NEG_ID = "int(-1 * random() * 1073741823)"


meta_df = pd.DataFrame(
    [
        {"type": "start", "name": "start"},
        {"type": "end", "name": "end"},
        {"type": "today", "name": "today"},
        {"type": "phonenumber", "name": "phonenumber"},
        {"type": "deviceid", "name": "deviceid"},
        {"type": "username", "name": "username"},
        {
            "type": "email",
            "name": "email",
        },
    ]
)

photo_collection_df = pd.DataFrame([
    add_label_translations({
        "type": "image",
        "name": "image",
        "appearance": "minimal",
        "parameters": "max-pixels=1000",
    })
])


def _get_mandatory_fields(
        use_odk_collect: bool,
        new_geom_type: DbGeomType,
        need_verification_fields: bool
    ):
    """
    Return the mandatory fields data for form creation.
    
    Args:
        use_odk_collect: Mode of data collection
        new_geom_type: The geometry type (POINT, POLYGON, LINESTRING)
        need_verification_fields: Whether to include verification fields
    
    Returns:
        List of field definitions for the form
    """
    status_field_calculation = f"if({FEATURE} != '', 2, "
    if need_verification_fields:
        status_field_calculation += "if(${feature_exists} = 'no', 6, "
        status_field_calculation += "if(${digitisation_correct} = 'no', 6, "
    if use_odk_collect:
        status_field_calculation += f"if({NEW_FEATURE} != '', 2, 6)"
    else:
        status_field_calculation += "6"
    if need_verification_fields:
        status_field_calculation += "))"
    status_field_calculation += ")"

    if use_odk_collect:
        # Map geometry types to field types
        geom_type_mapping = {
            DbGeomType.POINT: "geopoint",
            DbGeomType.POLYGON: "geoshape",
            DbGeomType.LINESTRING: "geotrace"
        }
        
        # Get the correct field type or raise error if not supported
        if new_geom_type not in geom_type_mapping:
            raise ValueError(f"Unsupported geometry type: {new_geom_type}")

        geom_field = geom_type_mapping[new_geom_type]

        fields = [
            {"type": "start-geopoint", "name": "warmup", "notes": "collects location on form start"},
            add_label_translations({
                "type": "select_one mapping_mode",
                "name": "mapping_mode",
                "required": "yes",
            }),
            add_label_translations({
                "type": "select_one_from_file features.csv",
                "name": "feature",
                "appearance": "map",
                "relevant": "${mapping_mode} = 'existing'",
                "required": "yes",
            }),
            add_label_translations({
                "type": geom_field,
                "name": "new_feature",
                "appearance": "placement-map",
                "relevant": "${mapping_mode} = 'new'",
                "required": "yes",
            })
        ]
    else:
        fields = [
            {"type": "start-geopoint", "name": "warmup", "notes": "collects location on form start"},
            add_label_translations({
                "type": "select_one_from_file features.csv",
                "name": "feature",
                "appearance": "map",
            })
        ]

    fields.extend([
        {
            "type": "calculate",
            "name": "xid",
            "notes": "e.g. OSM ID",
            "label::english(en)": "Feature ID",
            "appearance": "minimal",
            "calculation": (
                f"if({FEATURE} != '', {INSTANCE_FEATURE}/osm_id, "
                f"if({NEW_FEATURE} != '', {RANDOM_NEG_ID}, ''))"
                if use_odk_collect
                else f"if({FEATURE} != '', {INSTANCE_FEATURE}/osm_id, '')"
            ),
            "save_to": "osm_id",
        },
        {
            "type": "calculate",
            "name": "xlocation",
            "notes": "e.g. OSM Geometry",
            "label::english(en)": "Feature Geometry",
            "appearance": "minimal",
            "calculation": (
                f"if({FEATURE} != '', {INSTANCE_FEATURE}/geometry, "
                f"if({NEW_FEATURE} != '', {NEW_FEATURE}, ''))"
                if use_odk_collect
                else f"if({FEATURE} != '', {INSTANCE_FEATURE}/geometry, '')"
            ),
            "save_to": "geometry",
        },
        {
            "type": "calculate",
            "name": "task_id",
            "notes": "e.g. Field-TM Task ID",
            "label::english(en)": "Task ID",
            "appearance": "minimal",
            "calculation": f"if({FEATURE} != '', {INSTANCE_FEATURE}/task_id, '')",
            "save_to": "task_id",
        },
        {
            "type": "calculate",
            "name": "status",
            "notes": "Update the Entity 'status' field",
            "label::english(en)": "Mapping Status",
            "appearance": "minimal",
            "calculation": f"{status_field_calculation}",
            "default": "2",
            "trigger": f"{NEW_FEATURE}" if use_odk_collect else "",
            "save_to": "status",
        },
        {
            "type": "calculate",
            "name": "submission_ids",
            "notes": "Update the submission ids",
            "label::english(en)": "Submission ids",
            "appearance": "minimal",
            "calculation": (
                f"if({INSTANCE_FEATURE}/submission_ids,"
                f"concat({INSTANCE_FEATURE}/submission_ids, ',',{INSTANCE_ID}),"
                f"{INSTANCE_ID})"
            ),
            "save_to": "submission_ids",
        },
        {
            "type": "calculate",
            "name": "created_by",
            "notes": "Update the created_by field",
            "label::english(en)": "Created by",
            "appearance": "minimal",
            "calculation": f"if({NEW_FEATURE} != '', {USERNAME}, 'svcfmtm')" if use_odk_collect else "''",
            "save_to": "created_by",
        },
    ])
    if need_verification_fields:
        fields.append(add_label_translations({
            "type": "select_one yes_no",
            "name": "feature_exists",
            "relevant": "${feature} != '' ",
        }))
    return fields


def create_survey_df(
        use_odk_collect: bool,
        new_geom_type: DbGeomType,
        need_verification_fields: bool
    ) -> pd.DataFrame:
    """Create the survey sheet dataframe.

    We do this in a function to allow the geometry type
    for new data to be specified.
    """
    fields = _get_mandatory_fields(use_odk_collect, new_geom_type, need_verification_fields)
    mandatory_df = pd.DataFrame(fields)
    return pd.concat([meta_df, mandatory_df])


def create_entity_df(use_odk_collect: bool) -> pd.DataFrame:
    """Get the entities sheet for the dataframe."""
    status_label_expr = """concat(
        if(${status} = '1', "🔒 ",
        if(${status} = '2', "✅ ",
        if(${status} = '5', "🏁 ",
        if(${status} = '6', "❌ ", '')))),
        "Task ", ${task_id},
        " Feature ", if(${xid} != ' ', ${xid}, ' ')
    )"""
    entities_data = [
        {
            "list_name": "features",
            "entity_id": f"coalesce({FEATURE}, uuid())",
            "create_if": f"if({NEW_FEATURE}, true(), false())" if use_odk_collect else "false()",
            "update_if": f"if({NEW_FEATURE}, false(), true())" if use_odk_collect else "true()",
            "label": status_label_expr,
        }
    ]
    return pd.DataFrame(entities_data)

# Define the settings sheet
settings_data = [
    {
        "form_id": "mandatory_fields",
        "version": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "form_title": "Mandatory Fields Form",
        "allow_choice_duplicates": "yes",
    }
]

settings_df = pd.DataFrame(settings_data)
