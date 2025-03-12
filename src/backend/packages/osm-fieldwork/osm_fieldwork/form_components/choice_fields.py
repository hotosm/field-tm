#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023, 2024 Humanitarian OpenStreetMap Team
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
        "list_name": "yes_no",
        "name": "yes",
        "label::english(en)": "Yes",
        "label::nepali(ne)": "छ",
        "label::portuguese(pt-BR)": "Sim",
    },
    {
        "list_name": "yes_no",
        "name": "no",
        "label::english(en)": "No",
        "label::nepali(ne)": "छैन",
        "label::portuguese(pt-BR)": "Não",
    },
]

choices_df = pd.DataFrame(choices_data)

digitisation_choices = [
    {
        "list_name": "digitisation_problem",
        "name": "lumped",
        "label::english(en)": "Lumped - one polygon (more than one building digitized as one)",
        "label::nepali(ne)": "लुम्पेड - एक बहुभुज (एउटा भन्दा बढी भवनहरू एकको रूपमा डिजिटलाइज गरिएको)",
        "label::swahili(sw)": "Lumped - poligoni moja (zaidi ya jengo moja limewekwa dijiti kuwa moja)",
        "label::french(fr)": "Lumped - un polygone (plus d'un bâtiment numérisé en un seul)",
        "label::spanish(es)": "Agrupado - un polígono (más de un edificio digitalizado como uno)",
        "label::portuguese(pt-BR)": "Agrupado - um polígono (mais de um edifício digitalizado como um só)",
    },
    {
        "list_name": "digitisation_problem",
        "name": "split",
        "label::english(en)": "Split - one building (one building digitized as more than one polygon)",
        "label::nepali(ne)": "विभाजन - एउटा भवन (एउटा भवन एक भन्दा बढी बहुभुजको रूपमा डिजिटाइज गरिएको)",
        "label::swahili(sw)": "Mgawanyiko - jengo moja (jengo moja limebadilishwa kuwa zaidi ya poligoni moja)",
        "label::french(fr)": "Fractionnement - un bâtiment (un bâtiment numérisé sous la forme de plusieurs polygones)",
        "label::spanish(es)": "Split - un edificio (un edificio digitalizado como más de un polígono)",
        "label::portuguese(pt-BR)": "Split - um edifício (um edifício digitalizado como mais de um polígono)",
    },
    {
        "list_name": "digitisation_problem",
        "name": "other",
        "label::english(en)": "OTHER",
        "label::nepali(ne)": "अन्य",
        "label::swahili(sw)": "MENGINEYO",
        "label::french(fr)": "AUTRES",
        "label::spanish(es)": "OTROS",
        "label::portuguese(pt-BR)": "OUTROS",
    },
]

digitisation_choices_df = pd.DataFrame(digitisation_choices)
