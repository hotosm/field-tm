"""Tests for QField project generator compatibility helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_project_gen_svc_module():
    """Load the QField wrapper module from the sibling service directory."""
    module_path = Path(__file__).resolve().parents[2] / "qfield" / "project_gen_svc.py"
    spec = spec_from_file_location("project_gen_svc", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_over_point_label_placement_prefers_qgis_labelplacement_enum():
    """Modern PyQGIS defines placement with Qgis.LabelPlacement."""
    module = _load_project_gen_svc_module()

    class MockLabelPlacementEnum:
        OverPoint = object()

        def __call__(self, value):
            if value == 1:
                return self.OverPoint
            raise ValueError(value)

    class MockQgis:
        LabelPlacement = MockLabelPlacementEnum()

    class MockQgsPalLayerSettings:
        LabelPlacement = type("WrongEnum", (), {"OverPoint": object()})
        OverPoint = object()

    assert (
        module._resolve_over_point_label_placement(
            MockQgsPalLayerSettings,
            MockQgis,
        )
        is MockQgis.LabelPlacement.OverPoint
    )


def test_resolve_over_point_label_placement_falls_back_to_enum_member_lookup():
    """Modern bindings can fall back to the raw enum value if construction fails."""
    module = _load_project_gen_svc_module()

    class MockLabelPlacementEnum:
        OverPoint = object()

        def __call__(self, value):
            raise ValueError(value)

    class MockQgis:
        LabelPlacement = MockLabelPlacementEnum()

    class MockQgsPalLayerSettings:
        OverPoint = object()

    assert (
        module._resolve_over_point_label_placement(
            MockQgsPalLayerSettings,
            MockQgis,
        )
        == 1
    )


def test_resolve_over_point_label_placement_uses_labelplacement_if_present():
    """Support environments exposing a nested LabelPlacement enum name."""
    module = _load_project_gen_svc_module()

    class MockLabelPlacement:
        OverPoint = object()

    class MockQgsPalLayerSettings:
        LabelPlacement = MockLabelPlacement
        OverPoint = object()

    assert (
        module._resolve_over_point_label_placement(MockQgsPalLayerSettings)
        is MockLabelPlacement.OverPoint
    )


def test_resolve_over_point_label_placement_falls_back_to_legacy_shape():
    """Older PyQGIS exposes OverPoint directly on QgsPalLayerSettings."""
    module = _load_project_gen_svc_module()

    class MockQgsPalLayerSettings:
        OverPoint = object()

    assert (
        module._resolve_over_point_label_placement(MockQgsPalLayerSettings)
        is MockQgsPalLayerSettings.OverPoint
    )
