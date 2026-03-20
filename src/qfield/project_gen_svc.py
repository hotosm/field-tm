#!/usr/bin/env python3

import sys
import os
import logging
import json
import threading
import traceback
import atexit
import shutil
import re
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Dict, Any
from pathlib import Path

qgis_application = None

# Serialise QGIS work: the QgsApplication and its processing providers are
# not thread-safe.  ThreadingHTTPServer accepts connections concurrently, but
# only one request at a time proceeds past this lock, effectively queuing work
# rather than dropping or racing it.
_qgis_lock = threading.Lock()


def setup_logging() -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def setup_qgis_paths() -> None:
    """Initialize QGIS paths."""
    qgis_pluginpath = os.environ.get('QGIS3_PLUGINPATH', '/usr/share/qgis/python/plugins/')
    if qgis_pluginpath not in sys.path:
        sys.path.append(qgis_pluginpath)


def start_qgis_application(
    enable_processing: bool = True,
    verbose: bool = False,
    log: Optional[logging.Logger] = None,
) -> Any:
    """
    Start QGIS application with proper error handling.
    
    Args:
        enable_processing: Enable processing algorithms
        verbose: Output QGIS settings
        log: Logger instance
    
    Returns:
        QgsApplication instance
    
    Raises:
        RuntimeError: If QGIS version is incompatible or initialization fails
    """
    global qgis_application
    
    log = log or logging.getLogger(__name__)

    if qgis_application is not None:
        log.info("QGIS application already initialized")
        return qgis_application
    
    # Set environment variables
    os.environ.update({
        'QGIS_NO_OVERRIDE_IMPORT': '1',
        'QGIS_DISABLE_MESSAGE_HOOKS': '1'
    })

    # Set offscreen mode if no display
    if not os.environ.get('DISPLAY'):
        log.info("Setting offscreen mode")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    setup_qgis_paths()
    
    try:
        from qgis.core import Qgis, QgsApplication
        
        log.info(f"Starting QGIS application: {Qgis.QGIS_VERSION}")

        # Initialise
        qgis_prefix = os.environ.get('QGIS3_HOME', '/usr')
        os.environ['QGIS_PREFIX_PATH'] = qgis_prefix
        qgis_application = QgsApplication([], False)
        qgis_application.setPrefixPath(qgis_prefix, True)
        qgis_application.initQgis()
        
        # Register cleanup (else may prevent container shutdown)
        @atexit.register
        def cleanup_qgis():
            global qgis_application
            if qgis_application:
                log.info("Cleaning up QGIS application")
                qgis_application.exitQgis()
                qgis_application = None
        
        # Install message logger
        install_logger_hook(qgis_application, log)
        
        if verbose:
            print(qgis_application.showSettings())
        
        # Initialize processing
        if enable_processing:
            init_processing(log)
        
        log.info("QGIS application initialized successfully")
        return qgis_application
        
    except ImportError as e:
        raise RuntimeError(f"Failed to import QGIS modules: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize QGIS: {e}")


def init_processing(log: logging.Logger) -> None:
    """Initialize QGIS processing algorithms."""
    try:
        from processing.core.Processing import Processing
        from qgis.analysis import QgsNativeAlgorithms
        
        # Add native algorithms
        qgis_application.processingRegistry().addProvider(QgsNativeAlgorithms())
        Processing.initialize()

        log.info("QGIS processing initialized")
       
    except Exception as e:
        log.error(f"Failed to initialize processing: {e}")
        raise


def install_logger_hook(qgis_app: Any, log: logging.Logger) -> None:
    """Install QGIS message log hook."""
    try:
        from qgis.core import Qgis
        
        def log_qgis_message(message: str, tag: str, level: int):
            msg = f"QGIS {tag}: {message}"
            if level == Qgis.Warning:
                log.warning(msg)
            elif level == Qgis.Critical:
                log.error(msg)
            else:
                log.debug(msg)
        
        qgis_app.messageLog().messageReceived.connect(log_qgis_message)
        
    except Exception as e:
        log.warning(f"Failed to install logger hook: {e}")


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


def analyse_and_fix_geometries(input_geojson_path: str, log: logging.Logger) -> str:
    """
    Analyse geometry types, filter, fix geometries, and convert to GeoPackage.
    
    Args:
        input_geojson_path: Path to input GeoJSON file
        log: Logger instance
    
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

        log.info("Converting to GeoPackage...")
        processing.run(
            "native:savefeatures",
            {
                "INPUT": str(fixed_geojson),
                "OUTPUT": str(fixed_gpkg),
            }
        )
        
        log.info(f"GeoPackage created: {fixed_gpkg}")
        return str(fixed_gpkg)
    except Exception as e:
        log.error(f"Geometry processing failed: {e}")
        raise RuntimeError(f"Geometry processing failed: {e}")


def parse_and_validate_extent(extent_str: str) -> list[float]:
    """Parse and validate extent string."""
    try:
        values = [float(x.strip()) for x in extent_str.split(",")]
        if len(values) != 4:
            raise ValueError("Extent must have exactly 4 values: xmin,ymin,xmax,ymax")
        return values
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid extent format: {e}")


def parse_bool(value: Any, default: bool = True) -> bool:
    """Parse a JSON-ish boolean with a safe default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def set_project_file_permissions(project_path: str | Path) -> None:
    """Set permissive 777 permissions for upstream file access."""
    project_path = Path(project_path)
    for file_path in project_path.iterdir():
        file_path.chmod(0o777)
    for file_path in (project_path / "final").iterdir():
        file_path.chmod(0o777)


def xlsform_to_project(
    final_output_dir: Path,
    features_gpkg_path: Optional[str],
    extent_bbox: list[float],
    title: str,
    language: str,
    open_in_edit_mode: bool,
    log: logging.Logger,
) -> str:
    """Using a defined XLSForm create a project via xlsformconverter.

    Args:
        final_output_dir: Directory for the generated project output.
        features_gpkg_path: Path to the features GeoPackage, or None if
            there are no features (collect-new-data workflow).
        extent_bbox: Project extent as [xmin, ymin, xmax, ymax].
        title: Project title (used for the .qgz filename).
        language: Preferred form language.
        open_in_edit_mode: Whether the form should open in edit mode.
        log: Logger instance.

    Returns:
        str: Path to the final .qgz project file.
    """
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsReferencedRectangle,
        QgsRectangle,
        QgsVectorLayer,
    )

    project_path = final_output_dir.parent

    # Check XLSForm file
    xlsform_path = project_path / "xlsform.xlsx"
    if not xlsform_path.exists():
        raise FileNotFoundError(f"XLSForm file not found: {xlsform_path}")

    # Generate project
    final_output_dir = project_path / "final"
    final_output_dir.mkdir(mode=0o777, exist_ok=True)
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    extent_rect = QgsReferencedRectangle(QgsRectangle(*extent_bbox), crs)

    from xlsform2qgis.converter import XLSFormConverter
    converter = XLSFormConverter(str(xlsform_path))

    if not converter.is_valid():
        raise RuntimeError("The provided XLSForm is invalid, aborting.")
    converter.info.connect(lambda message: log.info(message))
    converter.warning.connect(lambda message: log.warning(message))
    converter.error.connect(lambda message: log.error(message))

    converter.set_custom_title(title)
    converter.set_preferred_language(language)
    converter.set_basemap("OpenStreetMap")
    converter.set_groups_as_tabs(True)
    converter.set_crs(crs)
    converter.set_extent(extent_rect)
    _configure_converter_edit_mode(converter, open_in_edit_mode, log)

    if features_gpkg_path:
        features_layer = QgsVectorLayer(features_gpkg_path, "features_valid", "ogr")
        if features_layer.isValid():
            converter.set_geometries(features_layer)
        else:
            log.warning(
                "Could not load features layer from %s, "
                "proceeding without features",
                features_gpkg_path,
            )

    return converter.convert(str(final_output_dir))


def _configure_converter_edit_mode(
    converter: Any,
    open_in_edit_mode: bool,
    log: logging.Logger,
) -> None:
    """Best-effort toggle for the xlsform2qgis edit-mode default."""
    setter_names = (
        "set_open_in_edit_mode",
        "set_start_in_edit_mode",
        "set_edit_mode",
    )
    for setter_name in setter_names:
        setter = getattr(converter, setter_name, None)
        if callable(setter):
            setter(open_in_edit_mode)
            log.info(
                "Configured converter %s(%s)",
                setter_name,
                open_in_edit_mode,
            )
            return

    attribute_names = (
        "open_in_edit_mode",
        "start_in_edit_mode",
        "edit_mode",
    )
    for attribute_name in attribute_names:
        if hasattr(converter, attribute_name):
            setattr(converter, attribute_name, open_in_edit_mode)
            log.info(
                "Configured converter %s=%s",
                attribute_name,
                open_in_edit_mode,
            )
            return

    log.warning(
        "Could not configure initial edit mode; xlsform2qgis API exposes no known hook"
    )


def _resolve_over_point_label_placement() -> Any:
    """Return the OverPoint label placement enum value.

    Uses direct attribute access instead of integer construction to avoid
    SIP binding bugs where ``Qgis.LabelPlacement(1)`` resolves to a
    ``LabelPredefinedPointPosition`` member.
    """
    from qgis.core import Qgis, QgsPalLayerSettings

    # QGIS 3.26+ scoped enum
    try:
        return Qgis.LabelPlacement.OverPoint
    except AttributeError:
        pass
    # Legacy (pre-3.26) enum on QgsPalLayerSettings
    try:
        return QgsPalLayerSettings.OverPoint
    except AttributeError:
        pass
    # Last resort: raw integer (OverPoint = 1 in all known versions)
    return 1


def configure_task_layer_style(task_layer: "qgis.core.QgsLayer", log: logging.Logger) -> None:
    """Configure the tasks layer in QGIS."""
    from qgis.core import (
        QgsPalLayerSettings,
        QgsTextBufferSettings,
        QgsTextFormat,
        QgsVectorLayerSimpleLabeling,
    )
    from qgis.PyQt.QtGui import QColor, QFont

    layer = _resolve_vector_layer(task_layer)
    if not layer:
        log.warning("No task layer available for styling")
        return

    log.info("Styling tasks layer")
    symbol = _build_layer_symbol(
        layer,
        fill_rgba=(0, 0, 0, 0),
        stroke_rgba=(130, 128, 133, 255),  # --hot-color-neutral-500 (#828085)
        stroke_width=1.2,
    )
    layer.renderer().setSymbol(symbol)

    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = 'coalesce("task_id", $id)'
    label_settings.isExpression = True
    label_settings.enabled = True
    label_settings.placement = _resolve_over_point_label_placement()
    label_settings.centroidInside = True
    label_settings.centroidWhole = True

    text_format = QgsTextFormat()
    font = QFont()
    font.setBold(True)
    text_format.setFont(font)
    text_format.setSize(10)
    text_format.setColor(QColor(64, 66, 72))

    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(1)
    buffer_settings.setColor(QColor(255, 255, 255))
    text_format.setBuffer(buffer_settings)
    label_settings.setFormat(text_format)

    layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()
   

def configure_survey_layer_style(survey_layer: "qgis.core.QgsLayer", log: logging.Logger) -> None:
    """Configure the survey layer in QGIS."""
    from qgis.core import QgsRuleBasedRenderer

    layer = _resolve_vector_layer(survey_layer)
    if not layer:
        log.warning("No survey layer available for styling")
        return

    log.info("Styling survey/features layer")

    root_rule = QgsRuleBasedRenderer.Rule(None)
    root_rule.appendChild(
        _build_status_rule(
            layer,
            label="Mapped",
            expression='"status" = \'mapped\'',
            fill_rgba=(80, 193, 203, 120),
            stroke_rgba=(80, 193, 203, 255),
        )
    )
    root_rule.appendChild(
        _build_status_rule(
            layer,
            label="Invalid",
            expression='"status" = \'invalid\'',
            fill_rgba=(215, 63, 63, 110),
            stroke_rgba=(215, 63, 63, 255),
        )
    )

    default_rule = _build_status_rule(
        layer,
        label="Default",
        expression="",
        fill_rgba=(130, 128, 133, 90),
        stroke_rgba=(64, 66, 72, 220),
    )
    default_rule.setIsElse(True)
    root_rule.appendChild(default_rule)

    layer.setRenderer(QgsRuleBasedRenderer(root_rule))
    layer.triggerRepaint()


def _resolve_vector_layer(layer_or_layers):
    """Return the first vector layer when a list is passed in."""
    if isinstance(layer_or_layers, list):
        return layer_or_layers[0] if layer_or_layers else None
    return layer_or_layers


def _build_layer_symbol(
    layer,
    *,
    fill_rgba: tuple[int, int, int, int],
    stroke_rgba: tuple[int, int, int, int],
    stroke_width: float,
):
    """Build a symbol matching the layer geometry type."""
    from qgis.core import Qgis, QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol

    # Qgis.GeometryType (3.30+) replaces deprecated QgsWkbTypes constants
    try:
        polygon_type = Qgis.GeometryType.Polygon
        line_type = Qgis.GeometryType.Line
    except AttributeError:
        from qgis.core import QgsWkbTypes
        polygon_type = QgsWkbTypes.PolygonGeometry
        line_type = QgsWkbTypes.LineGeometry

    geometry_type = layer.geometryType()
    if geometry_type == polygon_type:
        return QgsFillSymbol.createSimple(
            {
                "color": _rgba_string(fill_rgba),
                "outline_color": _rgba_string(stroke_rgba),
                "outline_width": str(stroke_width),
                "outline_style": "solid",
                "style": "solid",
            }
        )

    if geometry_type == line_type:
        return QgsLineSymbol.createSimple(
            {
                "line_color": _rgba_string(stroke_rgba),
                "line_width": str(stroke_width),
                "line_style": "solid",
            }
        )

    return QgsMarkerSymbol.createSimple(
        {
            "color": _rgba_string(fill_rgba),
            "outline_color": _rgba_string(stroke_rgba),
            "outline_width": str(max(stroke_width / 2, 0.4)),
            "size": "2.8",
            "name": "circle",
        }
    )


def _build_status_rule(
    layer,
    *,
    label: str,
    expression: str,
    fill_rgba: tuple[int, int, int, int],
    stroke_rgba: tuple[int, int, int, int],
):
    """Build a rule for survey-layer status styling."""
    from qgis.core import QgsRuleBasedRenderer

    rule = QgsRuleBasedRenderer.Rule(
        _build_layer_symbol(
            layer,
            fill_rgba=fill_rgba,
            stroke_rgba=stroke_rgba,
            stroke_width=0.9,
        )
    )
    rule.setLabel(label)
    if expression:
        rule.setFilterExpression(expression)
    return rule


def _rgba_string(rgba: tuple[int, int, int, int]) -> str:
    """Convert an RGBA tuple to the string format QGIS expects."""
    return ",".join(str(value) for value in rgba)


def configure_project_settings(qgis_project: "qgis.core.QgsProject", log: logging.Logger) -> None:
    """Configure the QField project for field mapping."""
    log.info("Configuring QField project settings for field mapping")
    
    # Configure tasks layer
    task_layers = qgis_project.mapLayersByName("tasks")
    if task_layers:
        configure_task_layer_style(task_layers, log)
        log.info("Tasks layer styled successfully")
    else:
        log.warning("Tasks layer not found in project")

    # Configure features layer (survey layer with purple fill, no stroke)
    survey_layers = qgis_project.mapLayersByName("survey")
    if survey_layers:
        configure_survey_layer_style(survey_layers, log)
        log.info("Survey/features layer styled successfully")
    else:
        log.warning("Survey layer not found in project")
    
    # Save project changes
    qgis_project.write()


def _prepare_features_layer(
    project_path: Path,
    log: logging.Logger,
) -> Optional[str]:
    """Convert seed feature GeoJSON to a cleaned GeoPackage when available."""
    log.info("Processing feature geometries")
    features_geojson_path = project_path / "features.geojson"
    if not (
        features_geojson_path.exists()
        and validate_geometry_file(features_geojson_path, log)
    ):
        log.warning(
            "No valid feature geometries found, creating project without features layer"
        )
        return None

    return analyse_and_fix_geometries(str(features_geojson_path), log)


def _prepare_tasks_layer(
    project_path: Path,
    final_output_dir: Path,
    log: logging.Logger,
) -> Optional[str]:
    """Convert task GeoJSON to a packaged GeoPackage when available."""
    log.info("Processing task geometries")
    set_project_file_permissions(project_path)
    tasks_geojson_path = project_path / "tasks.geojson"
    if not (tasks_geojson_path.exists() and validate_geometry_file(tasks_geojson_path, log)):
        log.warning("No valid task geometries found, project will not have a tasks layer")
        return None

    tasks_gpkg_path_input = analyse_and_fix_geometries(str(tasks_geojson_path), log)
    tasks_gpkg_path_final = final_output_dir / "tasks.gpkg"
    log.debug("Moving %s --> %s", tasks_gpkg_path_input, tasks_gpkg_path_final)
    shutil.move(tasks_gpkg_path_input, tasks_gpkg_path_final)
    set_project_file_permissions(project_path)
    return str(tasks_gpkg_path_final)


_DANGLING_ICC_RE = re.compile(rb'\s+iccProfileId="attachment:///([^"]+)"')


def _fix_dangling_icc_refs(
    qgs_data: bytes, bundled: set, log: logging.Logger
) -> tuple[bytes, bool]:
    """Strip iccProfileId attrs that reference attachments absent from the zip."""
    changed = False

    def _strip_if_missing(m: re.Match) -> bytes:
        nonlocal changed
        attachment_name = m.group(1).decode("utf-8")
        if attachment_name in bundled:
            return m.group(0)
        changed = True
        log.warning(
            "Removed dangling iccProfileId reference to missing attachment: %s",
            attachment_name,
        )
        return b""

    return _DANGLING_ICC_RE.sub(_strip_if_missing, qgs_data), changed


def _fix_task_layer_tree(
    qgs_data: bytes, log: logging.Logger
) -> tuple[bytes, bool]:
    """Ensure the tasks layer node appears in the layer-tree-group.

    When QGIS runs headless, addMapLayer(addToLegend=True) registers the layer
    in <projectlayers> but does not always write the corresponding
    <layer-tree-layer> node.  The missing node causes QFieldCloud's metadata
    parser to fail with "Failed to parse metadata from project", and also
    prevents the tasks layer from appearing in the QField layer panel.
    """
    # Only act if a tasks maplayer block is present in projectlayers
    tasks_block_m = re.search(
        rb"<maplayer\b[^>]*>(?:(?!</maplayer>).)*?<layername>tasks</layername>"
        rb"(?:(?!</maplayer>).)*?</maplayer>",
        qgs_data,
        re.DOTALL,
    )
    if not tasks_block_m:
        return qgs_data, False

    tasks_block = tasks_block_m.group(0)
    id_m = re.search(rb"<id>(.*?)</id>", tasks_block)
    ds_m = re.search(rb"<datasource>(.*?)</datasource>", tasks_block)
    if not id_m:
        log.warning("tasks maplayer has no <id>; skipping layer-tree fix")
        return qgs_data, False

    tasks_id = id_m.group(1).decode("utf-8")
    datasource = ds_m.group(1).decode("utf-8") if ds_m else "./tasks.gpkg"

    # Already in the tree? Nothing to do.
    if re.search(
        rb'<layer-tree-layer\b[^>]*\bid="' + re.escape(tasks_id.encode()) + rb'"',
        qgs_data,
    ):
        return qgs_data, False

    layer_tree_node = (
        f'\n    <layer-tree-layer patch_size="-1,-1" expanded="1" providerKey="ogr"'
        f' id="{tasks_id}" checked="Qt::Checked" source="{datasource}"'
        f' legend_split_behavior="0" name="tasks" legend_exp="">\n'
        f"      <customproperties>\n"
        f"        <Option />\n"
        f"      </customproperties>\n"
        f"    </layer-tree-layer>"
    ).encode()

    # Insert after the first </layer-tree-layer> (survey layer), so tasks
    # appears second in the tree - below survey but above list/basemap layers.
    ltg_m = re.search(rb"<layer-tree-group\b[^>]*>", qgs_data)
    if not ltg_m:
        log.warning("No <layer-tree-group> found; skipping layer-tree fix")
        return qgs_data, False

    first_end_m = re.search(rb"</layer-tree-layer>", qgs_data[ltg_m.end():])
    if first_end_m:
        insert_at = ltg_m.end() + first_end_m.end()
    else:
        insert_at = ltg_m.end()

    updated = qgs_data[:insert_at] + layer_tree_node + qgs_data[insert_at:]
    log.info("Injected tasks <layer-tree-layer> node into project layer tree")
    return updated, True


def _inject_map_canvas(
    qgs_data: bytes, extent_bbox: list, log: logging.Logger
) -> tuple[bytes, bool]:
    """Inject <mapcanvas name="theMapCanvas"> if absent.

    QFieldCloud's process_projectfile worker searches for this element by name
    to extract the project extent and background colour.  Projects generated by
    xlsform2qgis omit it because QGIS only writes it when a QgsMapCanvas
    object is attached (GUI context only).

    TODO remove this logic if after solved issue:
    https://github.com/opengisch/xlsform2qgis/issues/7
    """
    if b'name="theMapCanvas"' in qgs_data:
        return qgs_data, False

    # Grab the <spatialrefsys> block from <projectCrs> to reuse as <destinationsrs>
    crs_m = re.search(
        rb"<projectCrs>\s*(<spatialrefsys\b.*?</spatialrefsys>)\s*</projectCrs>",
        qgs_data,
        re.DOTALL,
    )
    if not crs_m:
        log.warning(
            "Cannot inject theMapCanvas: no <projectCrs> found in project XML"
        )
        return qgs_data, False

    srs_block = crs_m.group(1)

    # Derive map units from the CRS projection acronym
    acronym_m = re.search(rb"<projectionacronym>(.*?)</projectionacronym>", srs_block)
    acronym = acronym_m.group(1).decode() if acronym_m else ""
    units = "degrees" if acronym == "longlat" else "meters"

    xmin, ymin, xmax, ymax = extent_bbox
    canvas_xml = (
        f'\n  <mapcanvas name="theMapCanvas" annotationsVisible="1">\n'
        f"    <units>{units}</units>\n"
        f"    <extent>\n"
        f"      <xmin>{xmin}</xmin>\n"
        f"      <ymin>{ymin}</ymin>\n"
        f"      <xmax>{xmax}</xmax>\n"
        f"      <ymax>{ymax}</ymax>\n"
        f"    </extent>\n"
        f"    <rotation>0</rotation>\n"
        f"    <destinationsrs>\n"
        f"      {srs_block.decode()}\n"
        f"    </destinationsrs>\n"
        f"    <rendermaptile>0</rendermaptile>\n"
        f"  </mapcanvas>"
    ).encode()

    # Insert right after </verticalCrs> (preferred) or </projectCrs> (fallback)
    for anchor in (b"</verticalCrs>", b"</projectCrs>"):
        if anchor in qgs_data:
            updated = qgs_data.replace(anchor, anchor + canvas_xml, 1)
            log.info("Injected <mapcanvas name=\"theMapCanvas\"> into project XML")
            return updated, True

    log.warning("Could not find insertion point for theMapCanvas in project XML")
    return qgs_data, False


def sanitize_generated_qgz_metadata(
    project_file: str,
    log: logging.Logger,
    extent_bbox: Optional[list] = None,
) -> None:
    """Fix generated .qgz projects for QFieldCloud compatibility.

    Applies two corrections that xlsform2qgis projects consistently need:

    1. Removes dangling iccProfileId attachment refs - QGIS sometimes writes
       iccProfileId="attachment:///qt_temp-XXXX" into ProjectStyleSettings but
       never bundles the temp file.  QFieldCloud rejects such refs even though
       QGIS/QField tolerate them.

    2. Injects <mapcanvas name="theMapCanvas"> if absent - QFieldCloud's
       process_projectfile worker looks for this element to extract the project
       extent and background colour.  xlsform2qgis runs headless (no
       QgsMapCanvas), so the element is never written.  extent_bbox must be
       supplied ([xmin, ymin, xmax, ymax] in the project CRS) for this fix to
       apply; if omitted the missing canvas is only logged as a warning.
    """
    project_path = Path(project_file)
    if project_path.suffix.lower() != ".qgz":
        return

    with zipfile.ZipFile(project_path, "r") as archive:
        entry_names = archive.namelist()
        bundled = set(entry_names)
        qgs_entries = [name for name in entry_names if name.lower().endswith(".qgs")]
        if not qgs_entries:
            log.warning("No .qgs entry found inside %s", project_path)
            return
        qgs_entry = qgs_entries[0]
        qgs_data = archive.read(qgs_entry)

    qgs_data, icc_changed = _fix_dangling_icc_refs(qgs_data, bundled, log)
    qgs_data, tree_fixed = _fix_task_layer_tree(qgs_data, log)

    if extent_bbox is not None:
        qgs_data, canvas_injected = _inject_map_canvas(qgs_data, extent_bbox, log)
    else:
        canvas_injected = False
        if b'name="theMapCanvas"' not in qgs_data:
            log.warning(
                "Project has no <mapcanvas name=\"theMapCanvas\"> and no "
                "extent_bbox was provided; QFieldCloud may fail to parse metadata"
            )

    if not (icc_changed or tree_fixed or canvas_injected):
        return

    temp_archive = project_path.with_suffix(project_path.suffix + ".tmp")
    with zipfile.ZipFile(project_path, "r") as src, zipfile.ZipFile(
        temp_archive, "w", compression=zipfile.ZIP_DEFLATED
    ) as dst:
        for entry_name in entry_names:
            if entry_name == qgs_entry:
                dst.writestr(entry_name, qgs_data)
                continue
            dst.writestr(entry_name, src.read(entry_name))

    temp_archive.replace(project_path)
    log.info("Patched project metadata in %s", project_path)


def _load_generated_project(project_file: str):
    """Load the generated QGIS project from disk."""
    from qgis.core import QgsProject

    project = QgsProject.instance()
    project.clear()
    if not project.read(project_file):
        raise RuntimeError(f"Failed to read generated QGIS project: {project_file}")
    return project


def _add_task_layer_to_project(
    project,
    tasks_gpkg_path_final: Optional[str],
    log: logging.Logger,
) -> None:
    """Attach the task layer to the generated project."""
    if not tasks_gpkg_path_final:
        return

    from qgis.core import QgsVectorLayer

    task_layer = QgsVectorLayer(tasks_gpkg_path_final, "tasks", "ogr")
    if not task_layer.isValid():
        log.warning("Tasks GeoPackage is not a valid QGIS layer")
        return

    # addToLegend=False then insertLayer is required in headless QGIS: the
    # addToLegend=True path silently fails to write a <layer-tree-layer> node
    # when the project was loaded from a QGZ without a live QgsMapCanvas.
    registered = project.addMapLayer(task_layer, addToLegend=False)
    if not registered:
        log.warning("Failed to register tasks layer in project")
        return

    layer_root = project.layerTreeRoot()
    layer_root.insertLayer(1, task_layer)

    log.info("Tasks layer added to project")


def _ensure_survey_layer_on_top(project) -> None:
    """Move the survey layer to the top of the layer tree when present."""
    survey_layers = project.mapLayersByName("survey")
    if not survey_layers:
        return

    survey_layer = survey_layers[0]
    layer_root = project.layerTreeRoot()
    survey_node = layer_root.findLayer(survey_layer.id())
    if not survey_node:
        return

    parent = survey_node.parent()
    current_index = parent.children().index(survey_node)
    if current_index != 0:
        parent.insertLayer(0, survey_layer)
        parent.removeChildNode(survey_node)


def generate_qgis_project(
    project_dir: str,
    title: str,
    language: str,
    extent: str,
    open_in_edit_mode: bool,
    log: logging.Logger,
) -> Dict[str, Any]:
    """
    Generate QGIS project from XLSForm and geometries.
    
    Args:
        project_dir: Project directory path
        title: Project title
        language: Project language
        extent: Extent string (xmin,ymin,xmax,ymax)
        open_in_edit_mode: Whether the project should initially open in edit mode
        log: Logger instance
    
    Returns:
        Result dictionary with status and message
    """
    try:
        # Validate inputs
        project_path = Path(project_dir)
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        extent_bbox = parse_and_validate_extent(extent)
        features_gpkg_path = _prepare_features_layer(project_path, log)

        # XLSForm --> QGIS project
        log.info("Converting XLSForm --> project")
        final_output_dir = project_path / "final"
        project_file = xlsform_to_project(
            final_output_dir,
            features_gpkg_path,
            extent_bbox,
            title,
            language,
            open_in_edit_mode,
            log,
        )
        tasks_gpkg_path_final = _prepare_tasks_layer(project_path, final_output_dir, log)

        log.info("Opening generated QGIS project to add task layer")
        project = _load_generated_project(project_file)
        _add_task_layer_to_project(project, tasks_gpkg_path_final, log)
        _ensure_survey_layer_on_top(project)

        # Finalise the project
        project.write()

        # TODO configure project settings
        configure_project_settings(project, log)
        sanitize_generated_qgz_metadata(project_file, log, extent_bbox=extent_bbox)

        log.info(f"Final QField project located at: {project_file}")
        return {
            "status": "success",
            "message": "QGIS project generated successfully",
            # "output": result['OUTPUT']
            "output": str(final_output_dir),
        }

    except Exception as e:
        log.error(f"Project generation failed: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }


class QGISRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for QGIS processing."""
    
    def __init__(self, *args, logger=None, **kwargs):
        self.log = logger or logging.getLogger(__name__)
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            # Read and parse request
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_error(400, "Empty request body")
                return
            
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                self._send_error(400, f"Invalid JSON: {e}")
                return
            
            # Validate required parameters
            required_params = ["project_dir", "title", "language", "extent"]
            missing_params = [p for p in required_params if p not in data]
            if missing_params:
                self._send_error(400, f"Missing required parameters: {missing_params}")
                return
            
            # Process request – serialised via lock so concurrent HTTP requests
            # queue here rather than racing inside the single-threaded QGIS app.
            self.log.info(f"Processing request for project: {data.get('title')}")
            with _qgis_lock:
                result = generate_qgis_project(
                    project_dir=data["project_dir"],
                    title=data["title"],
                    language=data["language"],
                    extent=data["extent"],
                    open_in_edit_mode=parse_bool(data.get("open_in_edit_mode"), True),
                    log=self.log
                )
            
            # Send response
            status_code = 200 if result["status"] == "success" else 500
            self._send_json_response(status_code, result)
            
        except Exception as e:
            self.log.error(f"Request handling error: {e}")
            self._send_error(500, f"Internal server error: {e}")
    
    def do_GET(self):
        """Handle GET requests (health check)."""
        if self.path == "/health":
            self._send_json_response(200, {
                "status": "healthy",
                "qgis_version": getattr(__import__("qgis.core", fromlist=["Qgis"]).Qgis, "QGIS_VERSION", "unknown")
            })
        else:
            self._send_error(404, "Not found")
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response."""
        self._send_json_response(status_code, {
            "status": "error",
            "message": message
        })
    
    def log_message(self, format, *args):
        """Custom log message handler."""
        self.log.info(f"{self.address_string()} - {format % args}")


def create_handler_with_logger(logger):
    """Create request handler with logger dependency injection."""
    def handler(*args, **kwargs):
        return QGISRequestHandler(*args, logger=logger, **kwargs)
    return handler


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """
    Run the QGIS HTTP server.
    
    Args:
        host: Server host
        port: Server port
    """
    log = setup_logging()
    
    try:
        # Initialize QGIS
        log.info("Initializing QGIS application...")
        start_qgis_application(enable_processing=True, log=log)
        log.info("QGIS application ready")

        # Create and start server.  ThreadingHTTPServer spawns a thread per
        # connection so the socket is always ready to accept; _qgis_lock in the
        # handler serialises the actual QGIS work.
        handler = create_handler_with_logger(log)
        server = ThreadingHTTPServer((host, port), handler)
        
        log.info(f"🚀 QGIS API server listening on http://{host}:{port}")
        log.info("Endpoints:")
        log.info("  POST / - Process QGIS project")
        log.info("  GET /health - Health check")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        log.info("Shutting down server...")
        if 'server' in locals():
            server.shutdown()
    except Exception as e:
        log.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
