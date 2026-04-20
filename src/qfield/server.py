#!/usr/bin/env python3
"""HTTP server, work queue, routing, and entrypoint."""

import base64
import json
import logging
import os
import queue
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from qgis_init import setup_logging, start_qgis_application
from utils import parse_bool, parse_and_validate_extent

# QGIS work must run on the main thread (the thread that called
# QgsApplication.initQgis()) because Qt objects have thread affinity.
# ThreadingHTTPServer handles each HTTP request in a worker thread so health
# checks stay responsive, but POST handlers dispatch QGIS work to the main
# thread via this queue and wait for the result.
_work_queue: queue.Queue = queue.Queue()
QGIS_DISPATCH_TIMEOUT_SECONDS = 180


class QGISRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for QGIS processing."""

    def __init__(self, *args, logger=None, **kwargs):
        self.log = logger or logging.getLogger(__name__)
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """Route POST requests by path."""
        if self.path == "/field" or self.path == "/":
            self._handle_field()
        elif self.path == "/drone":
            self._handle_drone()
        elif self.path == "/basemap":
            self._handle_basemap()
        else:
            self._send_error(404, f"Unknown endpoint: {self.path}")

    def _handle_field(self):
        """Handle /field POST — existing xlsform workflow."""
        try:
            data = self._read_json_body()
            if data is None:
                return

            required_params = ["job_id", "title", "language", "extent"]
            missing_params = [p for p in required_params if p not in data]
            if missing_params:
                self._send_error(400, f"Missing required parameters: {missing_params}")
                return

            db_url = self._resolve_db_url()
            if db_url is None:
                return

            self.log.info(f"Processing /field request for project: {data.get('title')}")
            result = self._dispatch_to_main_thread(
                "field",
                {
                    "db_url": db_url,
                    "job_id": data["job_id"],
                    "title": data["title"],
                    "language": data["language"],
                    "extent": data["extent"],
                    "open_in_edit_mode": parse_bool(data.get("open_in_edit_mode"), True),
                    "log": self.log,
                },
            )

            status_code = 200 if result["status"] == "success" else 500
            self._send_json_response(status_code, result)

        except Exception as e:
            self.log.error(f"Request handling error: {e}")
            self._send_error(500, f"Internal server error: {e}")

    def _handle_drone(self):
        """Handle /drone POST — drone project generation."""
        try:
            data = self._read_json_body()
            if data is None:
                return

            required_params = ["project_name", "tasks_geojson", "extent"]
            missing_params = [p for p in required_params if p not in data]
            if missing_params:
                self._send_error(400, f"Missing required parameters: {missing_params}")
                return

            try:
                extent_bbox = parse_and_validate_extent(data["extent"])
            except ValueError as e:
                self._send_error(400, str(e))
                return

            # Decode optional base64-encoded plugin zip
            plugin_zip = None
            plugin_b64 = data.get("plugin_zip")
            if plugin_b64:
                try:
                    plugin_zip = base64.b64decode(plugin_b64)
                except Exception as e:
                    self._send_error(400, f"Invalid plugin_zip encoding: {e}")
                    return

            self.log.info(
                "Processing /drone request for project: %s",
                data.get("project_name"),
            )
            result = self._dispatch_to_main_thread(
                "drone",
                {
                    "project_name": data["project_name"],
                    "tasks_geojson": data["tasks_geojson"],
                    "extent_bbox": extent_bbox,
                    "flight_params": data.get("flight_params", {}),
                    "dem_url": data.get("dem_url"),
                    "plugin_zip": plugin_zip,
                    "log": self.log,
                },
            )

            if isinstance(result, bytes):
                # Success — return raw zip bytes
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{data["project_name"]}.zip"',
                )
                self.send_header("Content-Length", str(len(result)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(result)
            else:
                # Error dict
                self._send_json_response(500, result)

        except Exception as e:
            self.log.error(f"Request handling error: {e}")
            self._send_error(500, f"Internal server error: {e}")

    def _handle_basemap(self):
        """Handle /basemap POST — attach MBTiles to existing QField project."""
        try:
            data = self._read_json_body()
            if data is None:
                return

            required_params = ["job_id"]
            missing_params = [p for p in required_params if p not in data]
            if missing_params:
                self._send_error(400, f"Missing required parameters: {missing_params}")
                return

            db_url = self._resolve_db_url()
            if db_url is None:
                return

            self.log.info("Processing /basemap request for job: %s", data.get("job_id"))
            result = self._dispatch_to_main_thread(
                "basemap",
                {
                    "db_url": db_url,
                    "job_id": data["job_id"],
                    "log": self.log,
                },
            )

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
                "qgis_version": getattr(
                    __import__("qgis.core", fromlist=["Qgis"]).Qgis,
                    "QGIS_VERSION",
                    "unknown",
                ),
            })
        else:
            self._send_error(404, "Not found")

    def _read_json_body(self):
        """Read and parse JSON body. Returns None and sends error on failure."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_error(400, "Empty request body")
            return None

        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            self._send_error(400, f"Invalid JSON: {e}")
            return None

    def _resolve_db_url(self):
        """Resolve database URL from environment. Returns None and sends error on failure."""
        db_url = os.environ.get("FTM_DB_URL")
        if not db_url:
            db_host = os.environ.get("FTM_DB_HOST")
            db_user = os.environ.get("FTM_DB_USER")
            db_password = os.environ.get("FTM_DB_PASSWORD")
            db_name = os.environ.get("FTM_DB_NAME")
            if all((db_host, db_user, db_password, db_name)):
                db_url = (
                    f"postgresql://{db_user}:{db_password}"
                    f"@{db_host}/{db_name}"
                )
            else:
                self._send_error(
                    500,
                    "Database not configured: set FTM_DB_URL or "
                    "FTM_DB_HOST/FTM_DB_USER/FTM_DB_PASSWORD/FTM_DB_NAME",
                )
                return None
        return db_url

    def _dispatch_to_main_thread(self, endpoint: str, args: dict) -> Any:
        """Dispatch work to the main thread and block until done."""
        result_event = threading.Event()
        work_item = {
            "endpoint": endpoint,
            "args": args,
            "result": None,
            "done": result_event,
        }
        _work_queue.put(work_item)
        completed = result_event.wait(timeout=QGIS_DISPATCH_TIMEOUT_SECONDS)
        if not completed:
            return {
                "status": "error",
                "message": (
                    "QGIS processing timed out while waiting for main-thread dispatch "
                    f"(>{QGIS_DISPATCH_TIMEOUT_SECONDS}s)."
                ),
            }
        return work_item["result"]

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


def _process_work_queue(log: logging.Logger) -> None:
    """Process QGIS work items on the main thread (Qt thread affinity).

    Blocks on the queue with a short timeout so the main thread can still
    handle KeyboardInterrupt.  Called in a loop from ``run_server``.
    """
    try:
        item = _work_queue.get(timeout=0.5)
    except queue.Empty:
        return

    try:
        endpoint = item.get("endpoint", "field")

        if endpoint == "drone":
            from drone_project import generate_drone_project
            item["result"] = generate_drone_project(**item["args"])
        elif endpoint == "basemap":
            from field_project import attach_basemap_to_qgis_project
            item["result"] = attach_basemap_to_qgis_project(**item["args"])
        else:
            from field_project import generate_qgis_project
            item["result"] = generate_qgis_project(**item["args"])

    except Exception as exc:
        item["result"] = {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        item["done"].set()


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the QGIS HTTP server.

    QGIS is initialised on the main thread.  The HTTP server runs in a
    daemon thread (ThreadingHTTPServer keeps health-check GETs responsive
    while a POST job is processing).  QGIS work dispatched by POST handlers
    is executed on the main thread via ``_work_queue``.
    """
    log = setup_logging()

    try:
        # Initialize QGIS on the main thread
        log.info("Initializing QGIS application...")
        start_qgis_application(enable_processing=True, log=log)
        log.info("QGIS application ready")

        handler = create_handler_with_logger(log)
        server = ThreadingHTTPServer((host, port), handler)

        # Run the HTTP server in a daemon thread so the main thread can
        # process the QGIS work queue.
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        log.info(f"QGIS API server listening on http://{host}:{port}")
        log.info("Endpoints:")
        log.info("  POST /field - Generate field mapping project")
        log.info("  POST /drone - Generate drone mapping project")
        log.info("  POST /basemap - Attach basemap to existing project")
        log.info("  GET /health - Health check")

        # Main-thread loop: process QGIS work items dispatched by handlers
        while True:
            _process_work_queue(log)

    except KeyboardInterrupt:
        log.info("Shutting down server...")
        server.shutdown()
    except Exception as e:
        log.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
