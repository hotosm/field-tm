"""Layer styling.

Two distinct styling paths live in this module:

- ``configure_drone_task_layer_style`` (drone-tm): programmatic styling
  applied to ``dtm-tasks``.  Kept here verbatim because the drone wrapper
  does not yet ship QML style files. Will be removed / made generic in future!

- ``apply_named_style`` / ``apply_styles_from_dir`` / ``unpack_plugin_zip``
  (field-tm): generic QML-based styling fed by ``plugin_zip`` from the
  caller.  Layer styling is driven by ``styles/{layer_name}.qml`` files
  inside the supplied zip.
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Any, Optional


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


def _resolve_identifiable_map_layer_flag() -> Any:
    """Return the map-layer identifiable flag enum value when available."""
    from qgis.core import Qgis

    map_layer_flag = getattr(Qgis, "MapLayerFlag", None)
    if map_layer_flag is None:
        return None

    for attr_name in ("Identifiable", "IdentifiableLayer"):
        flag_value = getattr(map_layer_flag, attr_name, None)
        if flag_value is not None:
            return flag_value

    return None


def set_layer_not_identifiable(layer, log: logging.Logger) -> None:
    """Disable identify interaction for the given layer when supported."""
    if hasattr(layer, "flags") and hasattr(layer, "setFlags"):
        identifiable_flag = _resolve_identifiable_map_layer_flag()
        if identifiable_flag is None:
            log.warning("Could not resolve QGIS identifiable layer flag")
            return
        layer.setFlags(layer.flags() & ~identifiable_flag)
        return

    if hasattr(layer, "setIdentifiable"):
        layer.setIdentifiable(False)
        return

    log.warning("Layer does not expose an identifiable toggle API")


def configure_drone_task_layer_style(
    task_layer,
    log: logging.Logger,
    label_field: str = 'coalesce("task_id", $id)',
) -> None:
    """Configure the drone-tm tasks layer (programmatic styling).

    Drone-tm does not yet ship QML style files; this remains the
    programmatic path until that refactor lands.
    """
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

    log.info("Styling drone tasks layer")
    symbol = _build_layer_symbol(
        layer,
        fill_rgba=(0, 0, 0, 0),
        stroke_rgba=(66, 133, 244, 255),
        stroke_width=1.2,
    )
    layer.renderer().setSymbol(symbol)

    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = label_field
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
    set_layer_not_identifiable(layer, log)
    layer.triggerRepaint()


def apply_named_style(layer, qml_path: Path, log: logging.Logger) -> bool:
    """Apply a QML style file to a layer (Labeling + Symbology only).

    The category mask is intentionally narrow: form/field config from a
    style file can clobber the xlsform-derived attribute editor setup.
    """
    from qgis.core import QgsMapLayer

    categories = (
        QgsMapLayer.StyleCategory.Labeling | QgsMapLayer.StyleCategory.Symbology
    )
    message, ok = layer.loadNamedStyle(str(qml_path), False, categories)
    if not ok:
        log.warning("Failed to load style %s onto layer %s: %s", qml_path, layer.name(), message)
        return False
    layer.triggerRepaint()
    log.info("Applied style %s to layer %s", qml_path.name, layer.name())
    return True


def apply_styles_from_dir(project, styles_dir: Path, log: logging.Logger) -> set[str]:
    """Apply each ``{layer_name}.qml`` in ``styles_dir`` to its matching layer.

    Returns the set of layer names that were successfully styled.
    """
    styled: set[str] = set()
    if not styles_dir.is_dir():
        return styled

    for qml_path in sorted(styles_dir.glob("*.qml")):
        layer_name = qml_path.stem
        layers = project.mapLayersByName(layer_name)
        if not layers:
            log.debug("No layer named %s in project, skipping style %s", layer_name, qml_path.name)
            continue
        if apply_named_style(layers[0], qml_path, log):
            styled.add(layer_name)
    return styled


def unpack_plugin_zip(
    plugin_zip_bytes: bytes,
    dest_dir: Path,
    project_basename: str,
    log: logging.Logger,
) -> Optional[Path]:
    """Unpack a plugin zip into ``dest_dir``.

    ``main.qml`` is renamed to ``{project_basename}.qml`` so QField
    auto-discovers it as the project plugin.  All other entries keep
    their relative paths.

    Returns the path to the unpacked ``styles/`` directory if present,
    otherwise ``None``.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(plugin_zip_bytes), "r") as pz:
            _extract_plugin_entries(pz, dest_dir, project_basename, log)
    except zipfile.BadZipFile:
        log.error("plugin_zip is not a valid zip file; skipping plugin unpack")
        return None

    styles_dir = dest_dir / "styles"
    return styles_dir if styles_dir.is_dir() else None


def _extract_plugin_entries(
    pz: zipfile.ZipFile,
    dest_dir: Path,
    project_basename: str,
    log: logging.Logger,
) -> None:
    """Write each non-dir entry from the plugin zip into ``dest_dir``."""
    namelist = pz.namelist()
    common_prefix = _common_zip_prefix(namelist)
    for info in pz.infolist():
        if info.is_dir():
            continue
        rel_name = _resolve_plugin_entry_name(
            info.filename, common_prefix, project_basename
        )
        if not rel_name:
            continue
        target = dest_dir / rel_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(pz.read(info.filename))
    log.info("Unpacked %d plugin entries into %s", len(namelist), dest_dir)


def _resolve_plugin_entry_name(
    raw_name: str, common_prefix: str, project_basename: str
) -> str:
    """Strip the common wrapping dir and rename ``main.qml`` to the basename."""
    rel_name = raw_name
    if common_prefix and rel_name.startswith(common_prefix):
        rel_name = rel_name[len(common_prefix):]
    if rel_name == "main.qml":
        return f"{project_basename}.qml"
    return rel_name


def _common_zip_prefix(namelist: list[str]) -> str:
    """Return a single common top-level directory prefix if every entry shares one.

    Handles both flat zips (files at root) and wrapped zips (everything
    under a single directory like ``qfield-plugin/``).
    """
    files = [n for n in namelist if not n.endswith("/")]
    if not files:
        return ""
    first_dirs = {p.split("/", 1)[0] for p in files if "/" in p}
    roots_without_dir = {p for p in files if "/" not in p}
    if len(first_dirs) == 1 and not roots_without_dir:
        return first_dirs.pop() + "/"
    return ""


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


def _rgba_string(rgba: tuple[int, int, int, int]) -> str:
    """Convert an RGBA tuple to the string format QGIS expects."""
    return ",".join(str(value) for value in rgba)
