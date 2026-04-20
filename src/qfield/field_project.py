"""/field endpoint: xlsform + DB I/O (existing flow)."""

import base64
import json
import logging
import os
import shutil
import tempfile
import traceback
from pathlib import Path, PurePosixPath
from typing import Optional, Dict, Any

import psycopg
import requests

from geometry import validate_geometry_file, analyse_and_fix_geometries
from styling import configure_task_layer_style, configure_survey_layer_style
from sanitize import sanitize_generated_qgis_metadata
from utils import parse_and_validate_extent, set_project_file_permissions


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


def configure_project_settings(qgis_project, log: logging.Logger) -> None:
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


def _read_job_inputs(db_url: str, job_id: str, project_path: Path, log: logging.Logger) -> None:
    """Read input files from the qgis_jobs table and write to local temp dir."""
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT xlsform, features, tasks FROM qgis_jobs WHERE job_id = %s",
            (job_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Job {job_id} not found in database")

    xlsform_bytes, features, tasks = row
    (project_path / "xlsform.xlsx").write_bytes(xlsform_bytes)
    with open(project_path / "features.geojson", "w") as f:
        json.dump(features, f)
    with open(project_path / "tasks.geojson", "w") as f:
        json.dump(tasks, f)
    log.debug("Read job inputs from DB and wrote to %s", project_path)


def _read_basemap_job_inputs(db_url: str, job_id: str) -> tuple[str, str]:
    """Read basemap attach metadata from qgis_jobs."""
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT project_id, basemap_url FROM qgis_jobs WHERE job_id = %s",
            (job_id,),
        )
        row = cur.fetchone()

    if not row:
        raise RuntimeError(f"Job {job_id} not found in database")

    project_id, basemap_url = row
    if not project_id:
        raise RuntimeError("Missing project_id for basemap attach job")
    if not basemap_url or not str(basemap_url).strip():
        raise RuntimeError("Missing basemap_url for basemap attach job")

    return str(project_id), str(basemap_url).strip()


def _write_job_outputs(db_url: str, job_id: str, final_dir: Path, log: logging.Logger) -> int:
    """Read output files from final/ dir and write as base64 dict to DB."""
    output_files = {}
    for file_path in final_dir.iterdir():
        if file_path.is_file():
            output_files[file_path.name] = base64.b64encode(
                file_path.read_bytes()
            ).decode("ascii")
            log.debug("Collected output file: %s (%d bytes)", file_path.name, file_path.stat().st_size)

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE qgis_jobs SET output_files = %s WHERE job_id = %s",
            (json.dumps(output_files), job_id),
        )
        conn.commit()

    log.info("Wrote %d output files to DB for job %s", len(output_files), job_id)
    return len(output_files)


def generate_qgis_project(
    db_url: str,
    job_id: str,
    title: str,
    language: str,
    extent: str,
    open_in_edit_mode: bool,
    log: logging.Logger,
) -> Dict[str, Any]:
    """Generate QGIS project using input files from the database.

    Reads inputs from the ``qgis_jobs`` table, processes them locally,
    and writes the output files back to the same row.

    Returns:
        Result dictionary with status and message.
    """
    tmp_dir = tempfile.mkdtemp(prefix="qgis_job_")
    project_path = Path(tmp_dir)
    try:
        _read_job_inputs(db_url, job_id, project_path, log)

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

        configure_project_settings(project, log)
        sanitize_generated_qgis_metadata(project_file, log, extent_bbox=extent_bbox)

        num_files = _write_job_outputs(db_url, job_id, final_output_dir, log)
        log.info("Project generation complete, wrote %d output files to DB", num_files)
        return {
            "status": "success",
            "message": "QGIS project generated successfully",
        }

    except Exception as e:
        log.error(f"Project generation failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _qfc_api_root() -> str:
    """Resolve QFieldCloud API URL from environment."""
    base = (os.environ.get("QFIELDCLOUD_URL") or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("QFIELDCLOUD_URL is required for basemap attachment")
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


def _qfc_token() -> str:
    """Authenticate against QFieldCloud and return API token."""
    user = (os.environ.get("QFIELDCLOUD_USER") or "").strip()
    password = (os.environ.get("QFIELDCLOUD_PASSWORD") or "").strip()
    if not user or not password:
        raise RuntimeError(
            "QFIELDCLOUD_USER and QFIELDCLOUD_PASSWORD are required for basemap attachment"
        )

    api_root = _qfc_api_root()
    response = requests.post(
        f"{api_root}/auth/login",
        data={"username": user, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("token")
    if not token:
        raise RuntimeError("QFieldCloud login returned no token")
    return str(token)


def _safe_remote_project_path(remote_name: str) -> Path:
    """Validate and normalize remote QFieldCloud file paths for local write."""
    normalized = str(PurePosixPath(remote_name or ""))
    if not normalized or normalized in {".", "/"}:
        raise RuntimeError("Remote project file has an empty path")
    if normalized.startswith("/"):
        raise RuntimeError(f"Remote project file path must be relative: {remote_name}")

    parts = PurePosixPath(normalized).parts
    if any(part in {"..", ""} for part in parts):
        raise RuntimeError(f"Unsafe remote project file path: {remote_name}")

    return Path(*parts)


def _download_qfc_project_files(project_id: str, destination: Path, log: logging.Logger) -> None:
    """Download all project files from QFieldCloud into destination directory."""
    api_root = _qfc_api_root()
    token = _qfc_token()
    headers = {"Authorization": f"token {token}"}

    files_response = requests.get(
        f"{api_root}/files/{project_id}",
        params={"skip_metadata": "1"},
        headers=headers,
        timeout=30,
    )
    files_response.raise_for_status()
    files = files_response.json() or []

    for remote in files:
        remote_name = remote.get("name")
        if not remote_name:
            continue

        safe_relative_path = _safe_remote_project_path(str(remote_name))
        local_path = destination / safe_relative_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        file_response = requests.get(
            f"{api_root}/files/{project_id}/{remote_name}",
            headers=headers,
            timeout=120,
        )
        file_response.raise_for_status()
        local_path.write_bytes(file_response.content)
        log.debug("Downloaded remote file %s", remote_name)


def _download_mbtiles_file(
    basemap_url: str,
    destination: Path,
    log: logging.Logger,
) -> None:
    """Download MBTiles to destination with non-empty validation."""
    total = 0
    with requests.get(basemap_url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                output.write(chunk)

    if total == 0 or not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError("Downloaded basemap MBTiles is empty")

    log.info("Downloaded basemap MBTiles (%d bytes)", total)


def _attach_mbtiles_layer_to_project(
    project_file: Path,
    mbtiles_path: Path,
    log: logging.Logger,
) -> None:
    """Attach MBTiles raster layer at the bottom of project layer tree."""
    from qgis.core import QgsProject, QgsRasterLayer

    project = QgsProject.instance()
    project.clear()
    if not project.read(str(project_file)):
        raise RuntimeError(f"Failed to open QGIS project: {project_file}")

    existing = project.mapLayersByName("basemap")
    for layer in existing:
        project.removeMapLayer(layer.id())

    basemap_layer = QgsRasterLayer(str(mbtiles_path), "basemap", "gdal")
    if not basemap_layer.isValid():
        raise RuntimeError("Generated MBTiles is not a valid QGIS raster layer")

    project.addMapLayer(basemap_layer, addToLegend=False)
    root = project.layerTreeRoot()
    root.addLayer(basemap_layer)

    if not project.write(str(project_file)):
        raise RuntimeError("Failed to save QGIS project after basemap attach")


def attach_basemap_to_qgis_project(
    db_url: str,
    job_id: str,
    log: logging.Logger,
) -> Dict[str, Any]:
    """Attach MBTiles basemap to an existing QField project and write outputs."""
    tmp_dir = tempfile.mkdtemp(prefix="qgis_basemap_job_")
    working_dir = Path(tmp_dir) / "project"
    final_dir = Path(tmp_dir) / "final"
    working_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    try:
        project_id, basemap_url = _read_basemap_job_inputs(db_url, job_id)
        _download_qfc_project_files(project_id, working_dir, log)

        qgz_files = sorted(working_dir.glob("**/*.qgz"))
        if not qgz_files:
            raise RuntimeError("No .qgz file found in downloaded QField project")
        if len(qgz_files) > 1:
            raise RuntimeError(
                "Multiple .qgz files found in downloaded QField project; "
                "cannot determine target project file deterministically"
            )

        qgz_file = qgz_files[0]
        qgz_dir = qgz_file.parent
        mbtiles_dest = qgz_dir / "basemap.mbtiles"
        _download_mbtiles_file(basemap_url, mbtiles_dest, log)

        _attach_mbtiles_layer_to_project(qgz_file, mbtiles_dest, log)
        sanitize_generated_qgis_metadata(str(qgz_file), log)

        for source in working_dir.rglob("*"):
            if source.is_dir():
                continue
            relative_path = source.relative_to(working_dir)
            target = final_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        num_files = _write_job_outputs(db_url, job_id, final_dir, log)
        return {
            "status": "success",
            "message": f"Basemap attached successfully ({num_files} files).",
        }
    except Exception as exc:
        log.error("Basemap attach failed: %s", exc)
        return {
            "status": "error",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
