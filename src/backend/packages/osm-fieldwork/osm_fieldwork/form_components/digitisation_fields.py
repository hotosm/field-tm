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

"""This script creates a DataFrame for digitization-related fields in the survey form.

These fields focus on verifying the accuracy of digitized locations,
capturing any issues with digitization, and adding additional notes or
images if required. The fields include logic for relevance, mandatory
requirements, and conditions based on user responses.

NOTE the fields are omitted if need_verification_fields=False is
NOTE passed to update_xlsform.

Returns:
    pd.DataFrame: A DataFrame containing the digitization-related fields.
"""

import pandas as pd
from osm_fieldwork.form_components.translations import add_label_translations

digitisation_fields = [
    {
        "type": "begin group",
        "name": "verification",
        "relevant": "${feature_exists} = 'yes'",
    },
    {
        "type": "select_one yes_no",
        "name": "digitisation_correct",
        "required": "yes",
    },
    {
        "type": "select_one digitisation_problem",
        "name": "digitisation_problem",
        "relevant": "${digitisation_correct}='no'",
    },
    {
        "type": "text",
        "name": "digitisation_problem_other",
        "relevant": "${digitisation_problem}='other' ",
    },
    {"type": "end group"},
    {
        "type": "note",
        "name": "end_note",
        "relevant": "${feature_exists} = 'no'",
    },
]


digitisation_choices = [
    {
        "list_name": "digitisation_problem",
        "name": "lumped",
    },
    {
        "list_name": "digitisation_problem",
        "name": "split",
    },
    {
        "list_name": "digitisation_problem",
        "name": "other",
    },
]
