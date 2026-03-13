"""Tests for QField project generator compatibility helpers."""

import xml.etree.ElementTree as ET
import zipfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


def _load_project_gen_svc_module():
    """Load project_gen_svc.py from the checkout."""
    resolved = Path(__file__).resolve()
    search_roots = list(resolved.parents) + [Path.cwd(), *Path.cwd().parents]
    candidate_suffixes = (
        Path("src/qfield/project_gen_svc.py"),
        Path("qfield/project_gen_svc.py"),
    )

    module_path = None
    for root in search_roots:
        for suffix in candidate_suffixes:
            candidate = root / suffix
            if candidate.exists():
                module_path = candidate
                break
        if module_path is not None:
            break

    assert module_path is not None, "project_gen_svc.py not found in repository"
    spec = spec_from_file_location("project_gen_svc", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_fake_qgis(monkeypatch, qgis_obj, pal_settings_obj):
    """Install a fake qgis.core module for helper tests."""
    fake_qgis_core = SimpleNamespace(
        Qgis=qgis_obj, QgsPalLayerSettings=pal_settings_obj
    )
    monkeypatch.setitem(
        __import__("sys").modules, "qgis", SimpleNamespace(core=fake_qgis_core)
    )
    monkeypatch.setitem(__import__("sys").modules, "qgis.core", fake_qgis_core)


def test_resolve_over_point_label_placement_prefers_qgis_labelplacement_enum(
    monkeypatch,
):
    """Modern PyQGIS should use Qgis.LabelPlacement.OverPoint."""
    module = _load_project_gen_svc_module()

    class MockQgis:
        class LabelPlacement:
            OverPoint = object()

    class MockQgsPalLayerSettings:
        OverPoint = object()

    _install_fake_qgis(monkeypatch, MockQgis, MockQgsPalLayerSettings)
    assert (
        module._resolve_over_point_label_placement()
        is MockQgis.LabelPlacement.OverPoint
    )


def test_resolve_over_point_label_placement_falls_back_to_legacy_shape(monkeypatch):
    """Older PyQGIS should fall back to QgsPalLayerSettings.OverPoint."""
    module = _load_project_gen_svc_module()

    class MockQgis:
        class LabelPlacement:
            pass

    class MockQgsPalLayerSettings:
        OverPoint = object()

    _install_fake_qgis(monkeypatch, MockQgis, MockQgsPalLayerSettings)
    assert (
        module._resolve_over_point_label_placement()
        is MockQgsPalLayerSettings.OverPoint
    )


def test_resolve_over_point_label_placement_last_resort_value(monkeypatch):
    """Missing enum members should return the documented raw fallback integer."""
    module = _load_project_gen_svc_module()

    class MockQgis:
        class LabelPlacement:
            pass

    class MockQgsPalLayerSettings:
        pass

    _install_fake_qgis(monkeypatch, MockQgis, MockQgsPalLayerSettings)
    assert module._resolve_over_point_label_placement() == 1


_MINIMAL_QGS_WITH_PROJECT_CRS = """\
<qgis>
  <projectCrs>
    <spatialrefsys nativeFormat="Wkt">
      <wkt>GEOGCRS["WGS 84",ID["EPSG",4326]]</wkt>
      <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
      <srsid>3452</srsid><srid>4326</srid>
      <authid>EPSG:4326</authid>
      <description>WGS 84</description>
      <projectionacronym>longlat</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>true</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <verticalCrs><spatialrefsys nativeFormat="Wkt"><wkt/></spatialrefsys></verticalCrs>
{extra}
</qgis>"""


def test_sanitize_generated_qgz_metadata_removes_missing_icc_attachment(tmp_path):
    """Dangling iccProfileId attachment refs should be stripped from .qgs."""
    module = _load_project_gen_svc_module()
    qgz_path = tmp_path / "test.qgz"
    qgs_name = "test.qgs"
    qgs_xml = _MINIMAL_QGS_WITH_PROJECT_CRS.format(
        extra=(
            "<ProjectStyleSettings "
            'iccProfileId="attachment:///qt_temp-MISSING" '
            'projectStyleId="attachment:///styles.db" />'
        )
    )

    with zipfile.ZipFile(qgz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(qgs_name, qgs_xml.encode("utf-8"))
        archive.writestr("styles.db", b"sqlite")

    module.sanitize_generated_qgz_metadata(
        str(qgz_path), module.logging.getLogger(__name__)
    )

    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    settings = root.find(".//ProjectStyleSettings")
    assert settings is not None
    assert "iccProfileId" not in settings.attrib
    assert settings.attrib.get("projectStyleId") == "attachment:///styles.db"


def test_sanitize_generated_qgz_metadata_keeps_valid_icc_attachment(tmp_path):
    """Valid iccProfileId attachment refs should remain unchanged."""
    module = _load_project_gen_svc_module()
    qgz_path = tmp_path / "test.qgz"
    qgs_name = "test.qgs"
    qgs_xml = _MINIMAL_QGS_WITH_PROJECT_CRS.format(
        extra=(
            "<ProjectStyleSettings "
            'iccProfileId="attachment:///icc.bin" '
            'projectStyleId="attachment:///styles.db" />'
        )
    )

    with zipfile.ZipFile(qgz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(qgs_name, qgs_xml.encode("utf-8"))
        archive.writestr("styles.db", b"sqlite")
        archive.writestr("icc.bin", b"profile")

    module.sanitize_generated_qgz_metadata(
        str(qgz_path), module.logging.getLogger(__name__)
    )

    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    settings = root.find(".//ProjectStyleSettings")
    assert settings is not None
    assert settings.attrib.get("iccProfileId") == "attachment:///icc.bin"


def test_sanitize_generated_qgz_metadata_injects_map_canvas(tmp_path):
    """Missing theMapCanvas element should be injected when extent_bbox provided."""
    module = _load_project_gen_svc_module()
    qgz_path = tmp_path / "test.qgz"
    qgs_name = "test.qgs"
    qgs_xml = _MINIMAL_QGS_WITH_PROJECT_CRS.format(extra="")

    with zipfile.ZipFile(qgz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(qgs_name, qgs_xml.encode("utf-8"))

    extent = [85.0, 27.5, 85.5, 28.0]
    module.sanitize_generated_qgz_metadata(
        str(qgz_path), module.logging.getLogger(__name__), extent_bbox=extent
    )

    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)

    root = ET.fromstring(updated_qgs)  # noqa: S314
    canvas = root.find(".//mapcanvas[@name='theMapCanvas']")
    assert canvas is not None, "theMapCanvas element was not injected"
    assert canvas.findtext("units") == "degrees"
    assert float(canvas.findtext("extent/xmin")) == 85.0
    assert float(canvas.findtext("extent/ymin")) == 27.5
    assert float(canvas.findtext("extent/xmax")) == 85.5
    assert float(canvas.findtext("extent/ymax")) == 28.0
    assert canvas.find(".//destinationsrs/spatialrefsys") is not None


def test_sanitize_generated_qgz_metadata_skips_existing_map_canvas(tmp_path):
    """Existing theMapCanvas should not be overwritten."""
    module = _load_project_gen_svc_module()
    qgz_path = tmp_path / "test.qgz"
    qgs_name = "test.qgs"
    existing_canvas = (
        '<mapcanvas name="theMapCanvas" annotationsVisible="1">'
        "<units>degrees</units>"
        "<extent><xmin>1</xmin><ymin>2</ymin><xmax>3</xmax><ymax>4</ymax></extent>"
        "<rotation>0</rotation>"
        "<rendermaptile>0</rendermaptile>"
        "</mapcanvas>"
    )
    qgs_xml = _MINIMAL_QGS_WITH_PROJECT_CRS.format(extra=existing_canvas)

    with zipfile.ZipFile(qgz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(qgs_name, qgs_xml.encode("utf-8"))

    module.sanitize_generated_qgz_metadata(
        str(qgz_path), module.logging.getLogger(__name__), extent_bbox=[0, 0, 1, 1]
    )

    # File should be unchanged (nothing to fix)
    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    canvas = root.find(".//mapcanvas[@name='theMapCanvas']")
    assert canvas is not None
    assert float(canvas.findtext("extent/xmin")) == 1.0  # original value preserved
