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

"""This creates DataFrames for choice lists used in the survey form.

These include predefined options for fields such as yes/no responses
and issues related to digitization problems. Each choice contains
multilingual labels to support various languages.

Returns:
    tuple: Two pandas DataFrames containing the `choices` data for yes/no
and digitisation problems respectively.
"""

import logging
import pandas as pd


log = logging.getLogger(__name__)

# Define the choices sheet
choices_data = [
    {
        "list_name": "mapping_mode",
        "name": "existing",
    },
    {
        "list_name": "mapping_mode",
        "name": "new",
    },
    {
        "list_name": "yes_no",
        "name": "yes",
    },
    {
        "list_name": "yes_no",
        "name": "no",
    },
]


def get_choice_fields(use_odk_collect: bool):
    if use_odk_collect:
        # Append an empty task_filter choice, to ensure validation passes
        # We add the actual values in later in the final stages of project
        # creation, once we know all the task ids in the project.
        # Selecting None choice removes the filter in the logic
        log.debug("Appending task_ids list to choices sheet")
        choices_data.append({
            "list_name": "task_ids",
            "name": "none",
        })
    return choices_data


def generate_task_id_choices(task_ids: list[int]) -> pd.DataFrame:
    """Given a list of task ids, generate the values for the choice selection."""
    return pd.DataFrame(
        [
            {
                "list_name": "task_ids",
                "name": str(task_id),
                "label": str(task_id),
            }
            for task_id in task_ids
        ]
    )
