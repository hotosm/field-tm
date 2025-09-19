#!/usr/bin/env python3

import sys
import os
import logging
import json
import traceback
import atexit
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


def validate_geometry_file(file_path: Path) -> bool:
    """Validate that geometry file exists and is readable."""
    if not file_path.exists():
        return False
    
    try:
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(str(file_path), "test", "ogr")
        return layer.isValid() and layer.featureCount() > 0
    except Exception:
        return False


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
    if not validate_geometry_file(input_file):
        raise FileNotFoundError(f"Invalid or empty geometry file: {input_file}")
    
    output_dir = input_file.parent
    fixed_geojson = output_dir / "features_valid.geojson"
    fixed_gpkg = output_dir / "features_valid.gpkg"

    try:
        log.info("Analysing geometries by type...")
        
        log.debug("Filtering geoms")
        # Filter geometries by type
        filter_result = processing.run(
            "native:filterbygeometry",
            {
                "INPUT": str(input_file),
                "POINTS": "TEMPORARY_OUTPUT",
                "LINES": "TEMPORARY_OUTPUT", 
                "POLYGONS": "TEMPORARY_OUTPUT",
                "NO_GEOMETRY": "TEMPORARY_OUTPUT"
            }
        )

        # Count features by geometry type
        log.debug("Counting geoms")
        geometry_counts = {}
        for geom_type in ["POINTS", "LINES", "POLYGONS"]:
            temp_layer = filter_result[geom_type]
            if temp_layer:
                count = temp_layer.featureCount() if temp_layer.isValid() else 0
                geometry_counts[geom_type] = count
                log.debug(f"  {geom_type}: {count} features")
        
        if not geometry_counts or all(count == 0 for count in geometry_counts.values()):
            raise RuntimeError("No valid geometries found after filtering")
        
        # Use geometry type with most features
        predominant_type = max(geometry_counts, key=geometry_counts.get)
        predominant_count = geometry_counts[predominant_type]
        log.info(f"Using {predominant_type} ({predominant_count} features)")
        
        input_for_fixing = filter_result[predominant_type]
        
        # Fix geometries
        log.info("Fixing invalid geometries...")
        processing.run(
            "native:fixgeometries",
            {
                "INPUT": input_for_fixing,
                "METHOD": 1,  # Structure method
                "OUTPUT": str(fixed_geojson),
            }
        )
        
        # Validate fixed geometries
        log.info("Validating fixed geometries...")
        validation_result = processing.run(
            "qgis:checkvalidity",
            {
                "INPUT_LAYER": str(fixed_geojson),
                "METHOD": 2,  # QGIS method
                "IGNORE_RING_SELF_INTERSECTION": False,
                "VALID_OUTPUT": "TEMPORARY_OUTPUT",
                "INVALID_OUTPUT": "TEMPORARY_OUTPUT",
                "ERROR_OUTPUT": "TEMPORARY_OUTPUT",
            }
        )
        
        # Check for remaining invalid geometries
        invalid_layer = validation_result['INVALID_OUTPUT']
        invalid_count = invalid_layer.featureCount()
        if invalid_count > 0:
            log.warning(f"{invalid_count} geometries are still invalid after fixing")
        else:
            log.info("All geometries are valid")

        # Convert to GeoPackage
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
        from qgis.core import (
            QgsCoordinateReferenceSystem,
            QgsReferencedRectangle,
            QgsRectangle,
            QgsVectorLayer,
        )

        # Validate inputs
        project_path = Path(project_dir)
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        extent_bbox = parse_and_validate_extent(extent)
 
        # Process geometries
        input_geojson = project_path / "features.geojson"
        gpkg_path = analyse_and_fix_geometries(str(input_geojson), log)
        
        # Check XLSForm file
        xlsform_path = project_path / "xlsform.xlsx"
        if not xlsform_path.exists():
            raise FileNotFoundError(f"XLSForm file not found: {xlsform_path}")
        
        # Generate project
        final_output_dir = project_path / "final"
        final_output_dir.mkdir(mode=0o777, exist_ok=True)
        crs = QgsCoordinateReferenceSystem("EPSG:4326")
        extent_rect = QgsReferencedRectangle(QgsRectangle(*extent_bbox), crs)
        features_layer = QgsVectorLayer(gpkg_path, "features_valid", "ogr")
        if not features_layer.isValid():
            raise RuntimeError(f"Failed to load vector layer from {gpkg_path}")

        # FIXME running via processing didn't work!
        # FIXME Issue: Project generation failed: Error creating algorithm from createInstance()
        # params = {
        #     "INPUT": str(xlsform_path),
        #     "TITLE": title,
        #     "LANGUAGE": language,
        #     "BASEMAP": 0,
        #     "GROUPS_AS_TABS": True,
        #     "UPLOAD_TO_QFIELDCLOUD": False,
        #     "CRS": crs,
        #     "EXTENT": f"{extent} [EPSG:4326]",
        #     "GEOMETRIES": f"{gpkg_path}|layername=features_valid",
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
        project_file = converter.convert(str(final_output_dir))

        # Ensure permissions are permissive for deletion upstream
        for file_path in project_path.iterdir():
            file_path.chmod(0o777)
        for file_path in final_output_dir.iterdir():
            file_path.chmod(0o777)

        return {
            "status": "success",
            "message": "QGIS project generated successfully",
            # "output": result['OUTPUT']
            "output": project_file,
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
