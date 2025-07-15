"""Index of data model file paths."""

import os

import json


data_models_path = os.path.dirname(os.path.abspath(__file__))

amenities = f"{data_models_path}/amenities.json"
buildings = f"{data_models_path}/buildings.json"
camping = f"{data_models_path}/camping.json"
cemeteries = f"{data_models_path}/cemeteries.json"
education = f"{data_models_path}/education.json"
emergency = f"{data_models_path}/emergency.json"
health = f"{data_models_path}/health.json"
highways = f"{data_models_path}/highways.json"
landusage = f"{data_models_path}/landusage.json"
nature = f"{data_models_path}/nature.json"
places = f"{data_models_path}/places.json"
religious = f"{data_models_path}/religious.json"
toilets = f"{data_models_path}/toilets.json"
wastedisposal = f"{data_models_path}/wastedisposal.json"
waterpoints = f"{data_models_path}/waterpoints.json"
waterways = f"{data_models_path}/waterways.json"


def get_choices():
    """Get the categories and associated XLSFiles from the config file.

    Returns:
        (list): A list of the XLSForms included in osm-fieldwork
    """
    data = dict()
    json_data_file = os.path.join(data_models_path, "category.json")

    if os.path.exists(json_data_file):
        with open(json_data_file, encoding="utf-8") as f:
            contents = json.load(f)
            for entry in contents:
                if isinstance(entry, dict) and len(entry) == 1:
                    k, v = list(entry.items())[0]
                    data[k] = v[0] if isinstance(v, list) and v else v
    return data
