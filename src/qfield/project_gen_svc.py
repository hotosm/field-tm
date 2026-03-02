#!/usr/bin/env python3

import sys
import os
import logging
import json
import traceback
import atexit
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Dict, Any
from pathlib import Path

qgis_application = None


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

        # Try to add XLSFormConverter if available
        try:
            from xlsformconverter.XLSFormConverterPlugin import XLSFormConverterProvider
            provider = XLSFormConverterProvider(None)
            success = qgis_application.processingRegistry().addProvider(provider)
            if success:
                log.info("XLSFormConverter provider added successfully")
            else:
                log.warning("Failed to add XLSFormConverter provider")
            algorithms = provider.algorithms()
            log.debug(f"xlsformconverter algorithms available: {algorithms}")

        except ImportError:
            log.warning("XLSFormConverter plugin not available")
        
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
    """Validate that geometry file exists and is readable."""
    if not file_path.exists():
        log.error(f"File does not exist: {file_path}")
        return False
    
    try:
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(str(file_path), "layer", "ogr")
        return layer.isValid() and layer.featureCount() > 0
    except Exception as e:
        log.error(e)
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


def set_project_file_permissions(project_path: str | Path) -> None:
    """Set permissive 777 permissions for upstream file access."""
    project_path = Path(project_path)
    for file_path in project_path.iterdir():
        file_path.chmod(0o777)
    for file_path in (project_path / "final").iterdir():
        file_path.chmod(0o777)


def xlsform_to_project(
    final_output_dir: Path,
    features_gpkg_path: str,
    extent_bbox: list[float],
    title: str,
    language: str,
    log: logging.Logger
) -> str:
    """Using a defined XLSForm create a project via xlsformconverter.
    
    Returns:
        str: Path to the final qgz project file.
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
    features_layer = QgsVectorLayer(features_gpkg_path, "features_valid", "ogr")
    if not features_layer.isValid():
        raise RuntimeError(f"Failed to load vector layer from {features_gpkg_path}")

    # FIXME running via QGIS processing didn't work!
    # FIXME Issue: Project generation failed: Error creating algorithm from createInstance()
    # FIXME instead we import the converter algorithm directly below
    # params = {
    #     "INPUT": str(xlsform_path),
    #     "TITLE": title,
    #     "LANGUAGE": language,
    #     "BASEMAP": 0,
    #     "GROUPS_AS_TABS": True,
    #     "UPLOAD_TO_QFIELDCLOUD": False,
    #     "CRS": crs,
    #     "EXTENT": f"{extent} [EPSG:4326]",
    #     "GEOMETRIES": f"{features_gpkg_path}|layername=features_valid",
    #     "OUTPUT": str(final_output_dir),
    # }
    # log.info(f"Generating QGIS project with params: {params}")
    # result = processing.run("xlsformconverter:xlsformconverter", params)
    # log.info(f"Project generated: {result['OUTPUT']}")

    from xlsformconverter.XLSFormConverter import XLSFormConverter
    converter = XLSFormConverter(str(xlsform_path))

    if not converter.is_valid():
        log.error("The provided XLSForm is invalid, aborting.")
        sys.exit(1)
    converter.info.connect(lambda message: log.info(message))
    converter.warning.connect(lambda message: log.warning(message))
    converter.error.connect(lambda message: log.error(message))

    converter.set_custom_title(title)
    converter.set_preferred_language(language)
    converter.set_basemap("OpenStreetMap")
    converter.set_geometries(features_layer)
    converter.set_groups_as_tabs(True)
    converter.set_crs(crs)
    converter.set_extent(extent_rect)
    return converter.convert(str(final_output_dir))


def configure_task_layer_style(task_layer: "qgis.core.QgsLayer", log: logging.Logger) -> None:
    """Configure the tasks layer in QGIS."""
    pass
    # from qgis.core import (
    #     QgsFillSymbol,
    #     QgsPalLayerSettings,
    #     QgsTextFormat,
    #     QgsTextBufferSettings,
    #     QgsVectorLayerSimpleLabeling,
    # )
    # from qgis.PyQt.QtGui import QColor, QFont

    # task_layer = task_layer[0]
    # log.info("Styling tasks layer")
    
    # # Create fill symbol with light blue stroke and grey semi-transparent fill
    # symbol = QgsFillSymbol.createSimple({
    #     'color': '128,128,128,77',  # Grey with 0.3 opacity (77/255 ≈ 0.3)
    #     'outline_color': '173,216,230,255',  # Light blue
    #     'outline_style': 'solid',
    #     'outline_width': '0.5',
    #     'style': 'solid'
    # })
    
    # task_layer.renderer().setSymbol(symbol)
    
    # # Configure labels for task_id
    # label_settings = QgsPalLayerSettings()
    # label_settings.fieldName = 'task_id'
    # label_settings.enabled = True
    
    # # Text format
    # text_format = QgsTextFormat()
    # text_format.setSize(12)
    # font = QFont()
    # font.setBold(True)
    # text_format.setFont(font)
    # text_format.setColor(QColor(0, 0, 0))  # Black text
    
    # # Add text buffer for better visibility
    # buffer_settings = QgsTextBufferSettings()
    # buffer_settings.setEnabled(True)
    # buffer_settings.setSize(1)
    # buffer_settings.setColor(QColor(255, 255, 255))  # White buffer
    # text_format.setBuffer(buffer_settings)
    
    # label_settings.setFormat(text_format)
    
    # # Center placement
    # label_settings.placement = QgsPalLayerSettings.OverPoint
    # label_settings.centroidInside = True
    # label_settings.centroidWhole = True
    
    # # Apply labeling
    # labeling = QgsVectorLayerSimpleLabeling(label_settings)
    # task_layer.setLabeling(labeling)
    # task_layer.setLabelsEnabled(True)
    
    # task_layer.triggerRepaint()
   

def configure_survey_layer_style(survey_layer: "qgis.core.QgsLayer", log: logging.Logger) -> None:
    """Configure the survey layer in QGIS."""
    pass
    # from qgis.core import (
    #     QgsFillSymbol,
    # )

    # survey_layer = survey_layer[0]
    # log.info("Styling survey/features layer")
    
    # # Create fill symbol with purple fill and no stroke
    # symbol = QgsFillSymbol.createSimple({
    #     'color': '128,0,128,255',  # Purple
    #     'outline_style': 'no',  # No stroke
    #     'style': 'solid'
    # })
    
    # survey_layer.renderer().setSymbol(symbol)
    # survey_layer.triggerRepaint() 


def configure_project_settings(qgis_project: "qgis.core.QgsProject", log: logging.Logger) -> None:
    """Configure the QField project for field mapping."""
    log.info("Configuring QField project settings for field mapping")
    
    # Configure tasks layer
    task_layers = qgis_project.mapLayersByName("tasks")
    if task_layers:
        configure_task_layer_style(qgis_project, log)
        log.info("Tasks layer styled successfully")
    else:
        log.warning("Tasks layer not found in project")
    
    
    # Configure features layer (survey layer with purple fill, no stroke)
    survey_layers = qgis_project.mapLayersByName("survey")
    if survey_layers:
        configure_survey_layer_style(qgis_project, log)
        log.info("Survey/features layer styled successfully")
    else:
        log.warning("Survey layer not found in project")
    
    # Save project changes
    qgis_project.write()


def generate_qgis_project(project_dir: str, title: str, language: str, extent: str, log: logging.Logger) -> Dict[str, Any]:
    """
    Generate QGIS project from XLSForm and geometries.
    
    Args:
        project_dir: Project directory path
        title: Project title
        language: Project language
        extent: Extent string (xmin,ymin,xmax,ymax)
        log: Logger instance
    
    Returns:
        Result dictionary with status and message
    """
    try:
        # from qgis import processing
        from qgis.core import QgsProject, QgsVectorLayer

        # Validate inputs
        project_path = Path(project_dir)
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        extent_bbox = parse_and_validate_extent(extent)
 
        # Process feature geometries
        log.info("Adding feature geometries")
        features_geojson_path = project_path / "features.geojson"
        features_gpkg_path = analyse_and_fix_geometries(str(features_geojson_path), log)
        
        # XLSForm --> QGIS project
        log.info("Converting XLSForm --> project")
        final_output_dir = project_path / "final"
        project_file = xlsform_to_project(final_output_dir, features_gpkg_path, extent_bbox, title, language, log)

        # Add task geometries to project dir
        log.info("Adding task geometries")
        set_project_file_permissions(project_path) # Ensure permissions are permissive
        tasks_geojson_path = project_path / "tasks.geojson"
        tasks_gpkg_path_input = analyse_and_fix_geometries(str(tasks_geojson_path), log)
        tasks_gpkg_path_final = str(final_output_dir / "tasks.gpkg")
        log.debug(f"Moving {tasks_gpkg_path_input} --> {tasks_gpkg_path_final}")
        shutil.move(tasks_gpkg_path_input, tasks_gpkg_path_final)
        set_project_file_permissions(project_path) # Ensure permissions are permissive

        # Add task layer to project
        log.info("Adding task layer to project, then re-adding survey on top")
        project = QgsProject.instance()
        project.clear()
        project.read(project_file)

        # Add the task layer, then ensure the survey layer is on top
        task_layer = QgsVectorLayer(tasks_gpkg_path_final, 'tasks', 'ogr')
        project.addMapLayer(task_layer)
        # Find the 'survey' layer
        survey_layers = project.mapLayersByName("survey")
        if survey_layers:
            survey_layer = survey_layers[0]
            layer_root = project.layerTreeRoot()
            survey_node = layer_root.findLayer(survey_layer.id())
            if survey_node:
                parent = survey_node.parent()
                # Get current index
                current_index = parent.children().index(survey_node)
                if current_index != 0:
                    # Move survey layer to the top by re-inserting via insertLayer
                    parent.insertLayer(0, survey_layer)
                    parent.removeChildNode(survey_node)

        # Finalise the project
        project.write()

        # TODO configure project settings
        configure_project_settings(project, log)

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
            
            # Process request
            self.log.info(f"Processing request for project: {data.get('title')}")
            result = generate_qgis_project(
                project_dir=data["project_dir"],
                title=data["title"],
                language=data["language"],
                extent=data["extent"],
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

        # Create and start server
        handler = create_handler_with_logger(log)
        server = HTTPServer((host, port), handler)
        
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
