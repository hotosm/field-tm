"""/field endpoint: xlsform + DB I/O (existing flow)."""

import json
import logging
import base64
import shutil
import tempfile
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

import psycopg

from geometry import validate_geometry_file, analyse_and_fix_geometries
from styling import configure_task_layer_style, configure_survey_layer_style
from sanitize import sanitize_generated_qgz_metadata
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
        sanitize_generated_qgz_metadata(project_file, log, extent_bbox=extent_bbox)

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
