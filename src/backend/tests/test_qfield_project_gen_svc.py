"""Tests for QField project generator compatibility helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_project_gen_svc_module():
    """Load the QField wrapper module across supported checkout layouts."""
    resolved = Path(__file__).resolve()
    search_roots = list(resolved.parents) + [Path.cwd(), *Path.cwd().parents]
    candidate_suffixes = (
        Path("src/qfield/project_gen_svc.py"),
        Path("qfield/project_gen_svc.py"),
    )

    tried_paths: list[Path] = []
    module_path = None
    for root in search_roots:
        for suffix in candidate_suffixes:
            candidate = root / suffix
            tried_paths.append(candidate)
            if candidate.exists():
                module_path = candidate
                break
        if module_path is not None:
            break

    if module_path is None:
        pytest.skip(
            "qfield/project_gen_svc.py is not available in this test environment. "
            "Tried: " + ", ".join(str(path) for path in tried_paths)
        )
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
