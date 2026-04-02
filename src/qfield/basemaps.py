"""Basemap layer helpers for QField project generation."""

import logging


def create_osm_basemap(log: logging.Logger):
    """Create an OpenStreetMap XYZ tile basemap layer.

    Returns:
        QgsRasterLayer configured for OSM tiles, or None if invalid.
    """
    from qgis.core import QgsRasterLayer

    uri = (
        "type=xyz"
        "&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        "&zmin=0&zmax=19"
    )
    layer = QgsRasterLayer(uri, "OpenStreetMap", "wms")
    if not layer.isValid():
        log.warning("Failed to create OpenStreetMap basemap layer")
        return None
    log.info("OpenStreetMap basemap layer created")
    return layer
