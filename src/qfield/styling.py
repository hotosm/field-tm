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
        stroke_rgba=(130, 128, 133, 255),  # --hot-color-neutral-500 (#828085)
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
    layer.triggerRepaint()


def configure_survey_layer_style(survey_layer, log: logging.Logger) -> None:
    """Configure the survey layer in QGIS."""
    from qgis.core import QgsRuleBasedRenderer

    layer = _resolve_vector_layer(survey_layer)
    if not layer:
        log.warning("No survey layer available for styling")
        return

    log.info("Styling survey/features layer")

    root_rule = QgsRuleBasedRenderer.Rule(None)
    root_rule.appendChild(
        _build_status_rule(
            layer,
            label="Mapped",
            expression='"status" = \'mapped\'',
            fill_rgba=(80, 193, 203, 120),
            stroke_rgba=(80, 193, 203, 255),
        )
    )
    root_rule.appendChild(
        _build_status_rule(
            layer,
            label="Invalid",
            expression='"status" = \'invalid\'',
            fill_rgba=(215, 63, 63, 110),
            stroke_rgba=(215, 63, 63, 255),
        )
    )

    default_rule = _build_status_rule(
        layer,
        label="Default",
        expression="",
        fill_rgba=(130, 128, 133, 90),
        stroke_rgba=(64, 66, 72, 220),
    )
    default_rule.setIsElse(True)
    root_rule.appendChild(default_rule)

    layer.setRenderer(QgsRuleBasedRenderer(root_rule))
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


def _build_status_rule(
    layer,
    *,
    label: str,
    expression: str,
    fill_rgba: tuple[int, int, int, int],
    stroke_rgba: tuple[int, int, int, int],
):
    """Build a rule for survey-layer status styling."""
    from qgis.core import QgsRuleBasedRenderer

    rule = QgsRuleBasedRenderer.Rule(
        _build_layer_symbol(
            layer,
            fill_rgba=fill_rgba,
            stroke_rgba=stroke_rgba,
            stroke_width=0.9,
        )
    )
    rule.setLabel(label)
    if expression:
        rule.setFilterExpression(expression)
    return rule


def _rgba_string(rgba: tuple[int, int, int, int]) -> str:
    """Convert an RGBA tuple to the string format QGIS expects."""
    return ",".join(str(value) for value in rgba)
