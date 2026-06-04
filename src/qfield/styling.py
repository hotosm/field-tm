"""Layer styling.

QML-based styling fed by ``plugin_zip`` from the caller: layer styling
is driven by ``styles/{layer_name}.qml`` files inside the supplied zip,
matched to the in-project layer with the same name.
"""

import io
import logging
import zipfile
from pathlib import Path
from typing import Any, Optional


def _resolve_identifiable_map_layer_flag() -> Any:
    """Return the map-layer identifiable flag enum value when available.

    QGIS 3.30+ exposes ``Qgis.MapLayerFlag``; QGIS 3.44 / current ships
    ``QgsMapLayer.LayerFlag``.  Try both so the resolver works across
    versions.
    """
    from qgis.core import Qgis, QgsMapLayer

    enum_holders = (
        getattr(Qgis, "MapLayerFlag", None),
        getattr(QgsMapLayer, "LayerFlag", None),
    )
    for holder in enum_holders:
        if holder is None:
            continue
        for attr_name in ("Identifiable", "IdentifiableLayer"):
            flag_value = getattr(holder, attr_name, None)
            if flag_value is not None:
                return flag_value

    return None


def set_layer_not_identifiable(layer, log: logging.Logger) -> None:
    """Disable identify interaction for the given layer when supported."""
    if hasattr(layer, "flags") and hasattr(layer, "setFlags"):
        identifiable_flag = _resolve_identifiable_map_layer_flag()
        if identifiable_flag is not None:
            layer.setFlags(layer.flags() & ~identifiable_flag)
            return
        log.debug("Identifiable flag enum unresolved; falling back to setIdentifiable")

    if hasattr(layer, "setIdentifiable"):
        layer.setIdentifiable(False)
        return

    log.warning("Layer does not expose an identifiable toggle API")


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
