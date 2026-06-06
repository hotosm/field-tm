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
from styling import (
    apply_styles_from_dir,
    set_layer_not_identifiable,
    unpack_plugin_zip,
)
from utils import register_plugin_data_dirs


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
        _normalize_root_layer_order(project, log)
        _set_flight_variables(project, flight_params)
        plugin_dir = _apply_plugin_and_styles(
            project, plugin_zip, tmp, project_name, log
        )

        qgs_path = tmp / f"{project_name}.qgs"
        project.write(str(qgs_path))
        sanitize_generated_qgis_metadata(str(qgs_path), log, extent_bbox=extent_bbox)
        log.info("QGIS project written: %s", qgs_path)

        zip_bytes = _bundle_zip(
            project_name, qgs_path, tasks_gpkg_path, dem_path, plugin_dir, log,
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
    """Load the tasks layer and set the default extent.

    Styling is applied later via the caller-supplied plugin_zip's
    ``styles/dtm-tasks.qml``; see ``_apply_plugin_and_styles``.
    """
    task_layer = vector_layer_cls(str(tasks_gpkg_path), "dtm-tasks", "ogr")
    if not task_layer.isValid():
        raise RuntimeError(f"Failed to load tasks layer from {tasks_gpkg_path}")
    project.addMapLayer(task_layer)

    set_layer_not_identifiable(task_layer, log)

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


def _layer_order_priority(layer: Any) -> int:
    """Return semantic ordering priority for known drone layer names."""
    layer_name = (layer.name() or "").strip().lower()
    if layer_name in {"tasks", "dtm-tasks", "survey"}:
        return 1
    if layer_name == "basemap":
        return 90
    if layer_name == "openstreetmap":
        return 100
    if layer_name == "dem":
        return 95
    return 10


def _normalize_root_layer_order(project: Any, log: logging.Logger) -> None:
    """Normalize known layer positions in the drone project root tree."""
    root = project.layerTreeRoot()

    ordered_layers = []
    for index, node in enumerate(root.children()):
        layer = getattr(node, "layer", lambda: None)()
        if layer is None:
            continue
        ordered_layers.append((index, layer))

    if not ordered_layers:
        return

    desired_layers = [
        layer
        for _, layer in sorted(
            ordered_layers,
            key=lambda item: (_layer_order_priority(item[1]), item[0]),
        )
    ]

    changed = False
    for target_index, layer in enumerate(desired_layers):
        node = root.findLayer(layer.id())
        if node is None:
            continue
        current_children = list(root.children())
        if node not in current_children:
            continue
        current_index = current_children.index(node)
        if current_index == target_index:
            continue
        root.insertLayer(target_index, layer)
        root.removeChildNode(node)
        changed = True

    if changed:
        log.info("Normalized drone project layer order in root tree")


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


def _apply_plugin_and_styles(
    project: Any,
    plugin_zip: Optional[bytes],
    tmp: Path,
    project_name: str,
    log: logging.Logger,
) -> Optional[Path]:
    """Unpack ``plugin_zip`` and apply bundled QML styles to the project.

    ``main.qml`` is renamed to ``{project_name}.qml`` so QField discovers
    it as the project plugin; ``styles/{layer_name}.qml`` files are
    applied to matching layers via ``loadNamedStyle``.

    Returns the unpacked plugin directory for downstream bundling, or
    ``None`` if no plugin was supplied.
    """
    if not plugin_zip:
        log.info("No plugin_zip supplied; skipping plugin/style application")
        return None

    plugin_dir = tmp / "plugin"
    plugin_dir.mkdir(exist_ok=True)
    styles_dir = unpack_plugin_zip(plugin_zip, plugin_dir, project_name, log)
    # plugin_dir's contents are flattened into the project root in the final
    # zip, so its subdirs (plugin/, styles/) become the top-level dirs we need
    # libqfieldsync to recursively copy to the device.
    register_plugin_data_dirs(project, plugin_dir, log)
    if styles_dir is not None:
        apply_styles_from_dir(project, styles_dir, log)
    return plugin_dir


def _bundle_zip(
    project_name: str,
    qgs_path: Path,
    tasks_gpkg_path: Path,
    dem_path: Optional[Path],
    plugin_dir: Optional[Path],
    log: logging.Logger,
) -> bytes:
    """Build the final zip with project files and any unpacked plugin files.

    Zip structure:
        {project_name}/
            {project_name}.qgs
            dtm-tasks.gpkg
            dem.tif                    (if available)
            <plugin files>             (if plugin_dir provided)
    """
    buf = io.BytesIO()
    prefix = f"{project_name}/"

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(qgs_path, f"{prefix}{project_name}.qgs")
        zf.write(tasks_gpkg_path, f"{prefix}dtm-tasks.gpkg")
        if dem_path and dem_path.exists():
            zf.write(dem_path, f"{prefix}dem.tif")

        if plugin_dir and plugin_dir.is_dir():
            _add_plugin_files(zf, prefix, plugin_dir, log)

    return buf.getvalue()


def _add_plugin_files(
    output_zf: zipfile.ZipFile,
    prefix: str,
    plugin_dir: Path,
    log: logging.Logger,
) -> None:
    """Add each file under ``plugin_dir`` into the output zip."""
    count = 0
    for file_path in sorted(plugin_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(plugin_dir).as_posix()
        output_zf.write(file_path, f"{prefix}{rel}")
        count += 1
    log.info("Added %d plugin files to project zip", count)
