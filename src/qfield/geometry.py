"""Geometry fix/validate/convert utilities."""

import logging
from pathlib import Path


def validate_geometry_file(file_path: Path, log: logging.Logger) -> bool:
    """Validate that geometry file exists and is readable by QGIS."""
    if not file_path.exists():
        log.error(f"File does not exist: {file_path}")
        return False

    try:
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(str(file_path), "layer", "ogr")
        if not layer.isValid():
            log.error(f"QGIS cannot read file as a vector layer: {file_path}")
            return False
        count = layer.featureCount()
        if count == 0:
            log.warning(f"File has 0 features: {file_path}")
            return False
        log.debug(f"Validated {file_path}: {count} features")
        return True
    except Exception as e:
        log.error(f"Error validating geometry file {file_path}: {e}")
        return False


def _geometry_output_paths(input_file: Path) -> tuple[Path, Path, Path]:
    """Build the intermediate and final output paths for geometry fixing."""
    output_dir = input_file.parent
    return (
        output_dir / f"{input_file.stem}_prefixed.geojson",
        output_dir / f"{input_file.stem}_valid.geojson",
        output_dir / f"{input_file.stem}_valid.gpkg",
    )


def _prefilter_fixed_geometries(input_file: Path, pre_fixed_geojson: Path) -> dict:
    """Run the first-pass QGIS geometry fix and geometry-type filter."""
    from qgis import processing

    processing.run(
        "native:fixgeometries",
        {
            "INPUT": str(input_file),
            "METHOD": 1,
            "OUTPUT": str(pre_fixed_geojson),
        },
    )
    return processing.run(
        "native:filterbygeometry",
        {
            "INPUT": str(pre_fixed_geojson),
            "POINTS": "TEMPORARY_OUTPUT",
            "LINES": "TEMPORARY_OUTPUT",
            "POLYGONS": "TEMPORARY_OUTPUT",
            "NO_GEOMETRY": "TEMPORARY_OUTPUT",
        },
    )


def _geometry_counts(filter_result: dict, log: logging.Logger) -> dict[str, int]:
    """Count valid filtered features by geometry type."""
    geometry_counts = {}
    for geom_type in ["POINTS", "LINES", "POLYGONS"]:
        temp_layer = filter_result[geom_type]
        if not temp_layer:
            continue
        count = temp_layer.featureCount() if temp_layer.isValid() else 0
        geometry_counts[geom_type] = count
        log.debug(f"  {geom_type}: {count} features")
    return geometry_counts


def _predominant_geometry_input(
    filter_result: dict,
    log: logging.Logger,
):
    """Return the filtered layer with the predominant geometry type."""
    geometry_counts = _geometry_counts(filter_result, log)
    if not geometry_counts or all(count == 0 for count in geometry_counts.values()):
        raise RuntimeError("No valid geometries found after filtering")

    predominant_type = max(geometry_counts, key=geometry_counts.get)
    predominant_count = geometry_counts[predominant_type]
    log.info(f"Using {predominant_type} ({predominant_count} features)")
    return filter_result[predominant_type]


def _validate_fixed_geometries(fixed_geojson: Path, log: logging.Logger) -> None:
    """Run QGIS validity checks and log the remaining invalid count."""
    from qgis import processing

    validation_result = processing.run(
        "qgis:checkvalidity",
        {
            "INPUT_LAYER": str(fixed_geojson),
            "METHOD": 2,
            "IGNORE_RING_SELF_INTERSECTION": False,
            "VALID_OUTPUT": "TEMPORARY_OUTPUT",
            "INVALID_OUTPUT": "TEMPORARY_OUTPUT",
            "ERROR_OUTPUT": "TEMPORARY_OUTPUT",
        },
    )
    invalid_layer = validation_result["INVALID_OUTPUT"]
    invalid_count = invalid_layer.featureCount()
    if invalid_count > 0:
        log.warning(f"{invalid_count} geometries are still invalid after fixing")
        return
    log.info("All geometries are valid")


def analyse_and_fix_geometries(
    input_geojson_path: str,
    log: logging.Logger,
    populate_uuid: bool = False,
) -> str:
    """
    Analyse geometry types, filter, fix geometries, and convert to GeoPackage.

    Args:
        input_geojson_path: Path to input GeoJSON file
        log: Logger instance
        populate_uuid: When True, add a ``uuid`` column populated with a
            generated UUID v4 per feature. Required for layers that xlsform2qgis
            turns into a survey layer with photo repeats — QField's relation
            editor refuses to add a child feature when the parent's ``uuid``
            linking field is NULL.

    Returns:
        Path to output GeoPackage file

    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If processing fails
    """
    from qgis import processing

    input_file = Path(input_geojson_path)
    if not validate_geometry_file(input_file, log):
        raise FileNotFoundError(f"Invalid or empty geometry file: {input_file}")
    pre_fixed_geojson, fixed_geojson, fixed_gpkg = _geometry_output_paths(input_file)

    try:
        from qgis import processing

        log.info("Analysing geometries by type...")
        log.info("Pre-fixing geometries before filtering...")
        log.debug("Filtering geoms")
        filter_result = _prefilter_fixed_geometries(input_file, pre_fixed_geojson)
        log.debug("Counting geoms")
        input_for_fixing = _predominant_geometry_input(filter_result, log)
        log.info("Fixing invalid geometries...")
        processing.run(
            "native:fixgeometries",
            {
                "INPUT": input_for_fixing,
                "METHOD": 1,
                "OUTPUT": str(fixed_geojson),
            }
        )
        log.info("Validating fixed geometries...")
        _validate_fixed_geometries(fixed_geojson, log)

        savefeatures_input = str(fixed_geojson)
        if populate_uuid:
            log.info("Populating uuid column...")
            uuid_geojson = fixed_geojson.with_name(f"{fixed_geojson.stem}_uuid.geojson")
            processing.run(
                "native:fieldcalculator",
                {
                    "INPUT": savefeatures_input,
                    "FIELD_NAME": "uuid",
                    "FIELD_TYPE": 2,
                    "FIELD_LENGTH": 36,
                    "FIELD_PRECISION": 0,
                    "FORMULA": "uuid('WithoutBraces')",
                    "OUTPUT": str(uuid_geojson),
                },
            )
            savefeatures_input = str(uuid_geojson)

        log.info("Converting to GeoPackage...")
        # The chained QGIS algorithms above leave the output gpkg with both a
        # `fid` and `fid_1` column (one is the OGR-assigned primary key, the
        # other is a passed-through copy). Harmless but redundant; could be
        # collapsed later via `native:refactorfields` if it starts mattering.
        processing.run(
            "native:savefeatures",
            {
                "INPUT": savefeatures_input,
                "OUTPUT": str(fixed_gpkg),
            }
        )

        log.info(f"GeoPackage created: {fixed_gpkg}")
        return str(fixed_gpkg)
    except Exception as e:
        log.error(f"Geometry processing failed: {e}")
        raise RuntimeError(f"Geometry processing failed: {e}")
