"""Layer styling (symbols, labels, rules)."""

import logging
from typing import Any


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


def _set_layer_not_identifiable(layer, log: logging.Logger) -> None:
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


def configure_task_layer_style(
    task_layer,
    log: logging.Logger,
    label_field: str = 'coalesce("task_id", $id)',
) -> None:
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
    _set_layer_not_identifiable(layer, log)
    layer.triggerRepaint()


def configure_survey_layer_style(survey_layer, log: logging.Logger) -> None:
    """Configure the survey layer in QGIS."""
    layer = _resolve_vector_layer(survey_layer)
    if not layer:
        log.warning("No survey layer available for styling")
        return

    log.info("Styling survey/features layer")
    symbol = _build_layer_symbol(
        layer,
        fill_rgba=(0, 0, 0, 0),
        stroke_rgba=(64, 66, 72, 255),
        stroke_width=1.2,
    )
    layer.renderer().setSymbol(symbol)
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


def _rgba_string(rgba: tuple[int, int, int, int]) -> str:
    """Convert an RGBA tuple to the string format QGIS expects."""
    return ",".join(str(value) for value in rgba)
