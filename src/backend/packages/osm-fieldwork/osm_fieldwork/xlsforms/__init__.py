"""Index of XLSForm file paths."""

import importlib.resources

def buildings(): 
    "Returns a Traversable object for the buildings.yaml file"
    return importlib.resources.files(__name__).joinpath("buildings.yaml")

def health(): 
    "Returns a Traversable object for the health.yaml file"
    return importlib.resources.files(__name__).joinpath("health.yaml")

def highways(): 
    "Returns a Traversable object for the highways.yaml file"
    return importlib.resources.files(__name__).joinpath("highways.yaml")
