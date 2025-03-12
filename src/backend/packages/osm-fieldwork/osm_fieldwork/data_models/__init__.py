"""Index of data model file paths."""

import os

import yaml

data_models_path = os.path.dirname(os.path.abspath(__file__))

amenities = f"{data_models_path}/amenities.yaml"
buildings = f"{data_models_path}/buildings.yaml"
camping = f"{data_models_path}/camping.yaml"
cemeteries = f"{data_models_path}/cemeteries.yaml"
education = f"{data_models_path}/education.yaml"
emergency = f"{data_models_path}/emergency.yaml"
health = f"{data_models_path}/health.yaml"
highways = f"{data_models_path}/highways.yaml"
landusage = f"{data_models_path}/landusage.yaml"
nature = f"{data_models_path}/nature.yaml"
places = f"{data_models_path}/places.yaml"
religious = f"{data_models_path}/religious.yaml"
toilets = f"{data_models_path}/toilets.yaml"
wastedisposal = f"{data_models_path}/wastedisposal.yaml"
waterpoints = f"{data_models_path}/waterpoints.yaml"
waterways = f"{data_models_path}/waterways.yaml"


def get_choices():
    """Get the categories and associated XLSFiles from the config file.

    Returns:
        (list): A list of the XLSForms included in osm-fieldwork
    """
    data = dict()
    if os.path.exists(f"{data_models_path}/category.yaml"):
        file = open(f"{data_models_path}/category.yaml").read()
        contents = yaml.load(file, Loader=yaml.Loader)
        for entry in contents:
            [[k, v]] = entry.items()
            data[k] = v[0]
    return data
