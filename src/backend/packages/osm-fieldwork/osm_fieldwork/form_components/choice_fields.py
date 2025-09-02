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

import pandas as pd


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
