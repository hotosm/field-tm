"""Convert an uploaded GeoPackage to per-layer GeoJSON FeatureCollections."""

import json
import logging
import os
import tempfile
from typing import Dict

from osgeo import gdal, ogr

gdal.UseExceptions()
ogr.UseExceptions()


def convert_gpkg_to_geojson_layers(
    gpkg_bytes: bytes,
    log: logging.Logger,
) -> Dict[str, dict]:
    """Convert each vector layer in a GeoPackage to a GeoJSON FeatureCollection.

    Reprojects to EPSG:4326 so the output is web-friendly.  Skips empty layers
    and layers without geometry (e.g. attribute-only tables).

    Returns a dict keyed by layer name, each value a GeoJSON FeatureCollection.
    """
    with tempfile.TemporaryDirectory(prefix="ftm_export_") as tmp_dir:
        gpkg_path = os.path.join(tmp_dir, "input.gpkg")
        with open(gpkg_path, "wb") as fp:
            fp.write(gpkg_bytes)

        src_ds = ogr.Open(gpkg_path)
        if src_ds is None:
            raise ValueError("Could not open uploaded GeoPackage")

        layer_names = [
            src_ds.GetLayerByIndex(i).GetName()
            for i in range(src_ds.GetLayerCount())
        ]
        src_ds = None  # close before VectorTranslate reopens it

        if not layer_names:
            log.warning("GeoPackage contains no layers")
            return {}

        out: Dict[str, dict] = {}
        for layer_name in layer_names:
            geojson_path = os.path.join(tmp_dir, f"{layer_name}.geojson")
            try:
                gdal.VectorTranslate(
                    geojson_path,
                    gpkg_path,
                    options=gdal.VectorTranslateOptions(
                        format="GeoJSON",
                        layers=[layer_name],
                        dstSRS="EPSG:4326",
                        reproject=True,
                    ),
                )
            except Exception as exc:
                log.warning("Failed to convert layer '%s': %s", layer_name, exc)
                continue

            if not os.path.exists(geojson_path):
                log.warning(
                    "Layer '%s' produced no GeoJSON (attribute-only?)", layer_name
                )
                continue

            with open(geojson_path, encoding="utf-8") as fp:
                feature_collection = json.load(fp)

            if not feature_collection.get("features"):
                log.debug("Layer '%s' is empty; skipping", layer_name)
                continue

            out[layer_name] = feature_collection
            log.info(
                "Converted layer '%s' with %d feature(s)",
                layer_name,
                len(feature_collection["features"]),
            )

        return out
