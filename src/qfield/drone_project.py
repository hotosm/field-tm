"""/drone endpoint: tasks-only + plugin bundling (new)."""

import io
import json
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import urlopen
from urllib.error import URLError

from basemaps import create_osm_basemap
from sanitize import sanitize_generated_qgis_metadata
from styling import configure_task_layer_style


def generate_drone_project(
    project_name: str,
    tasks_geojson: dict,
    extent_bbox: list[float],
    flight_params: Dict[str, Any],
    dem_url: Optional[str],
    plugin_zip: Optional[bytes],
    log: logging.Logger,
) -> bytes:
    """Generate a QField-ready drone project and return it as zip bytes.

    Args:
        project_name: Human-readable project name (used for filenames).
        tasks_geojson: GeoJSON FeatureCollection of task polygons.
        extent_bbox: [xmin, ymin, xmax, ymax] in EPSG:4326.
        flight_params: Dict with keys gsd, agl, forward_overlap, side_overlap.
        dem_url: Optional presigned URL to a DEM GeoTIFF.
        plugin_zip: Optional zip bytes containing plugin files to bundle.
            The zip should contain files at the root level (no wrapping
            directory).  A file named ``main.qml`` is renamed to
            ``{project_name}.qml`` in the output; all other files and
            subdirectories are copied as-is.
        log: Logger instance.

    Returns:
        Raw zip bytes ready to send as an HTTP response body.
    """
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsProject,
        QgsReferencedRectangle,
        QgsVectorLayer,
    )
    from qgis import processing

    tmp_dir = tempfile.mkdtemp(prefix="drone_job_")
    tmp = Path(tmp_dir)

    try:
        tasks_gpkg_path = _create_tasks_geopackage(tmp, tasks_geojson, processing, log)
        project, crs = _create_project(QgsProject, QgsCoordinateReferenceSystem, project_name)
        root = project.layerTreeRoot()

        _add_task_layer(
            project,
            tasks_gpkg_path,
            QgsVectorLayer,
            QgsReferencedRectangle,
            crs,
            log,
        )
        dem_path = _maybe_add_dem_layer(project, root, tmp, dem_url, log)
        _add_osm_basemap(project, root, log)
        _set_flight_variables(project, flight_params)

        qgs_path = tmp / f"{project_name}.qgs"
        project.write(str(qgs_path))
        sanitize_generated_qgis_metadata(str(qgs_path), log, extent_bbox=extent_bbox)
        log.info("QGIS project written: %s", qgs_path)

        zip_bytes = _bundle_zip(
            project_name, qgs_path, tasks_gpkg_path, dem_path, plugin_zip, log,
        )
        log.info("Drone project zip built (%d bytes)", len(zip_bytes))
        return zip_bytes
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _create_tasks_geopackage(
    tmp: Path,
    tasks_geojson: dict,
    processing: Any,
    log: logging.Logger,
) -> Path:
    """Write task GeoJSON and convert it to a GeoPackage."""
    tasks_geojson_path = tmp / "tasks.geojson"
    with open(tasks_geojson_path, "w") as f:
        json.dump(tasks_geojson, f)

    tasks_gpkg_path = tmp / "dtm-tasks.gpkg"
    processing.run(
        "native:savefeatures",
        {
            "INPUT": str(tasks_geojson_path),
            "OUTPUT": str(tasks_gpkg_path),
        },
    )
    log.info("Tasks GeoPackage created: %s", tasks_gpkg_path)
    return tasks_gpkg_path


def _create_project(
    qgs_project_cls: Any,
    crs_cls: Any,
    project_name: str,
) -> tuple[Any, Any]:
    """Create a fresh QGIS project configured for EPSG:4326."""
    project = qgs_project_cls.instance()
    project.clear()

    crs = crs_cls("EPSG:4326")
    project.setCrs(crs)
    project.setTitle(project_name)
    return project, crs


def _add_task_layer(
    project: Any,
    tasks_gpkg_path: Path,
    vector_layer_cls: Any,
    referenced_rectangle_cls: Any,
    crs: Any,
    log: logging.Logger,
) -> None:
    """Load the tasks layer, apply styling, and set the default extent."""
    task_layer = vector_layer_cls(str(tasks_gpkg_path), "dtm-tasks", "ogr")
    if not task_layer.isValid():
        raise RuntimeError(f"Failed to load tasks layer from {tasks_gpkg_path}")
    project.addMapLayer(task_layer)

    configure_task_layer_style(
        task_layer,
        log,
        label_field='coalesce("project_task_id", $id)',
    )

    project.viewSettings().setDefaultViewExtent(
        referenced_rectangle_cls(task_layer.extent(), crs)
    )


def _maybe_add_dem_layer(
    project: Any,
    root: Any,
    tmp: Path,
    dem_url: Optional[str],
    log: logging.Logger,
) -> Optional[Path]:
    """Download and add the DEM raster layer when available and valid."""
    if not dem_url:
        return None

    dem_path = tmp / "dem.tif"
    try:
        log.info("Downloading DEM from presigned URL...")
        with urlopen(dem_url, timeout=120) as resp:
            dem_path.write_bytes(resp.read())
        log.info("DEM downloaded: %d bytes", dem_path.stat().st_size)

        from qgis.core import QgsRasterLayer

        dem_layer = QgsRasterLayer(str(dem_path), "dem", "gdal")
        if not dem_layer.isValid():
            log.warning("Downloaded DEM is not a valid raster layer")
            return None

        project.addMapLayer(dem_layer, addToLegend=False)
        dem_node = root.addLayer(dem_layer)
        dem_node.setItemVisibilityChecked(False)
        log.info("DEM raster layer added to project (hidden by default)")
        return dem_path
    except (URLError, OSError) as exc:
        log.warning("Failed to download DEM, skipping: %s", exc)
        return None


def _add_osm_basemap(project: Any, root: Any, log: logging.Logger) -> None:
    """Add the OSM basemap as the bottom layer when it is available."""
    osm_layer = create_osm_basemap(log)
    if osm_layer:
        project.addMapLayer(osm_layer, addToLegend=False)
        root.addLayer(osm_layer)


def _set_flight_variables(project: Any, flight_params: Dict[str, Any]) -> None:
    """Persist flight parameters as project custom variables."""
    variable_keys = {
        "gsd": "dtm_gsd",
        "agl": "dtm_agl",
        "forward_overlap": "dtm_forward_overlap",
        "side_overlap": "dtm_side_overlap",
    }

    scope = project.customVariables()
    for param_name, variable_name in variable_keys.items():
        value = flight_params.get(param_name)
        if value is not None:
            scope[variable_name] = str(value)
    project.setCustomVariables(scope)


def _bundle_zip(
    project_name: str,
    qgs_path: Path,
    tasks_gpkg_path: Path,
    dem_path: Optional[Path],
    plugin_zip: Optional[bytes],
    log: logging.Logger,
) -> bytes:
    """Build the final zip with project files and an optional plugin.

    Zip structure:
        {project_name}/
            {project_name}.qgs
            dtm-tasks.gpkg
            dem.tif                    (if available)
            <plugin files>             (if plugin_zip provided)

    Plugin convention: if the plugin zip contains a file named ``main.qml``
    it is renamed to ``{project_name}.qml`` so QField discovers it as the
    project plugin.  All other files keep their original paths.
    """
    buf = io.BytesIO()
    prefix = f"{project_name}/"

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Project files
        zf.write(qgs_path, f"{prefix}{project_name}.qgs")
        zf.write(tasks_gpkg_path, f"{prefix}dtm-tasks.gpkg")
        if dem_path and dem_path.exists():
            zf.write(dem_path, f"{prefix}dem.tif")

        # Plugin files from caller-supplied zip
        if plugin_zip:
            _merge_plugin_zip(zf, prefix, project_name, plugin_zip, log)

    return buf.getvalue()


def _merge_plugin_zip(
    output_zf: zipfile.ZipFile,
    prefix: str,
    project_name: str,
    plugin_zip: bytes,
    log: logging.Logger,
) -> None:
    """Extract a plugin zip and merge its contents into the output zip.

    ``main.qml`` is renamed to ``{project_name}.qml``; everything else
    is copied with its original relative path.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(plugin_zip), "r") as pz:
            for info in pz.infolist():
                if info.is_dir():
                    continue
                # Strip any single wrapping directory if every entry shares one
                arc_name = _strip_common_prefix(info.filename, pz.namelist())
                # Rename main.qml -> {project_name}.qml
                if arc_name == "main.qml":
                    arc_name = f"{project_name}.qml"
                data = pz.read(info.filename)
                output_zf.writestr(f"{prefix}{arc_name}", data)
            log.info("Merged %d plugin files into project zip", len(pz.namelist()))
    except zipfile.BadZipFile:
        log.error("plugin_zip is not a valid zip file; skipping plugin bundling")


def _strip_common_prefix(filename: str, all_names: list[str]) -> str:
    """If every entry in the zip shares a single top-level directory, strip it.

    This handles both flat zips (files at root) and wrapped zips
    (everything under one directory like ``qfield-plugin/``).
    """
    parts = [n for n in all_names if not n.endswith("/")]
    if not parts:
        return filename
    first_dirs = {p.split("/", 1)[0] for p in parts if "/" in p}
    roots_without_dir = {p for p in parts if "/" not in p}
    # Only strip if every file is under exactly one common directory
    if len(first_dirs) == 1 and not roots_without_dir:
        common = first_dirs.pop() + "/"
        if filename.startswith(common):
            return filename[len(common):]
    return filename
