"""Tests for QField project generator compatibility helpers."""

import xml.etree.ElementTree as ET
import zipfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests


def _find_repo_root(start: Path) -> Path:
    """Find repository root containing the src/qfield worker modules."""
    for candidate in [start, *start.parents]:
        if (candidate / "src" / "qfield").is_dir():
            return candidate
    searched = [str(start), *[str(p) for p in start.parents]]
    raise AssertionError(
        "Repository root with src/qfield not found. Searched: " + ", ".join(searched)
    )


def _find_existing_file(repo_root: Path, *relative_paths: str) -> Path:
    """Return first existing file from candidate relative paths."""
    for relative_path in relative_paths:
        candidate = repo_root / relative_path
        if candidate.is_file():
            return candidate
    raise AssertionError(
        "Expected one of these files to exist: "
        + ", ".join(str(repo_root / p) for p in relative_paths)
    )


def _load_project_gen_svc_module():
    """Load qfield helper functions from the checkout."""
    repo_root = _find_repo_root(Path(__file__).resolve())

    sanitize_path = _find_existing_file(
        repo_root,
        "src/qfield/sanitize.py",
        "qfield/sanitize.py",
    )
    styling_path = _find_existing_file(
        repo_root,
        "src/qfield/styling.py",
        "qfield/styling.py",
    )

    sanitize_spec = spec_from_file_location("qfield_sanitize", sanitize_path)
    styling_spec = spec_from_file_location("qfield_styling", styling_path)
    assert sanitize_spec is not None and sanitize_spec.loader is not None
    assert styling_spec is not None and styling_spec.loader is not None

    sanitize_module = module_from_spec(sanitize_spec)
    styling_module = module_from_spec(styling_spec)
    sanitize_spec.loader.exec_module(sanitize_module)
    styling_spec.loader.exec_module(styling_module)

    return SimpleNamespace(
        _resolve_over_point_label_placement=(
            styling_module._resolve_over_point_label_placement
        ),
        sanitize_generated_qgis_metadata=sanitize_module.sanitize_generated_qgis_metadata,
        logging=sanitize_module.logging,
    )


def _load_field_project_module():
    """Load qfield field_project.py from the checkout."""
    repo_root = _find_repo_root(Path(__file__).resolve())
    module_path = _find_existing_file(
        repo_root,
        "src/qfield/field_project.py",
        "qfield/field_project.py",
    )

    module_name = "qfield_field_project_test"
    module = __import__("sys").modules.get(module_name)
    if module is not None:
        return module

    spec = spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)

    # Provide lightweight stubs for sibling imports used by field_project.py
    sys_modules = __import__("sys").modules
    sys_modules.setdefault(
        "geometry",
        SimpleNamespace(
            validate_geometry_file=lambda *args, **kwargs: True,
            analyse_and_fix_geometries=lambda *args, **kwargs: "",
        ),
    )
    sys_modules.setdefault(
        "styling",
        SimpleNamespace(
            configure_task_layer_style=lambda *args, **kwargs: None,
            configure_survey_layer_style=lambda *args, **kwargs: None,
        ),
    )
    sys_modules.setdefault(
        "sanitize",
        SimpleNamespace(sanitize_generated_qgis_metadata=lambda *args, **kwargs: None),
    )
    sys_modules.setdefault(
        "utils",
        SimpleNamespace(
            parse_and_validate_extent=lambda *args, **kwargs: [0, 0, 0, 0],
            set_project_file_permissions=lambda *args, **kwargs: None,
        ),
    )

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


def test_sanitize_generated_qgis_metadata_removes_missing_icc_attachment(tmp_path):
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

    module.sanitize_generated_qgis_metadata(
        str(qgz_path), module.logging.getLogger(__name__)
    )

    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    settings = root.find(".//ProjectStyleSettings")
    assert settings is not None
    assert "iccProfileId" not in settings.attrib
    assert settings.attrib.get("projectStyleId") == "attachment:///styles.db"


def test_sanitize_generated_qgis_metadata_keeps_valid_icc_attachment(tmp_path):
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

    module.sanitize_generated_qgis_metadata(
        str(qgz_path), module.logging.getLogger(__name__)
    )

    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    settings = root.find(".//ProjectStyleSettings")
    assert settings is not None
    assert settings.attrib.get("iccProfileId") == "attachment:///icc.bin"


def test_sanitize_generated_qgis_metadata_injects_map_canvas(tmp_path):
    """Missing theMapCanvas element should be injected when extent_bbox provided."""
    module = _load_project_gen_svc_module()
    qgz_path = tmp_path / "test.qgz"
    qgs_name = "test.qgs"
    qgs_xml = _MINIMAL_QGS_WITH_PROJECT_CRS.format(extra="")

    with zipfile.ZipFile(qgz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(qgs_name, qgs_xml.encode("utf-8"))

    extent = [85.0, 27.5, 85.5, 28.0]
    module.sanitize_generated_qgis_metadata(
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


def test_sanitize_generated_qgis_metadata_skips_existing_map_canvas(tmp_path):
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

    module.sanitize_generated_qgis_metadata(
        str(qgz_path), module.logging.getLogger(__name__), extent_bbox=[0, 0, 1, 1]
    )

    # File should be unchanged (nothing to fix)
    with zipfile.ZipFile(qgz_path, "r") as archive:
        updated_qgs = archive.read(qgs_name)
    root = ET.fromstring(updated_qgs)  # noqa: S314
    canvas = root.find(".//mapcanvas[@name='theMapCanvas']")
    assert canvas is not None
    assert canvas.attrib.get("annotationsVisible") == "1"
    assert canvas.findtext("units") == "degrees"
    assert float(canvas.findtext("extent/xmin")) == 1.0
    assert float(canvas.findtext("extent/ymin")) == 2.0
    assert float(canvas.findtext("extent/xmax")) == 3.0
    assert float(canvas.findtext("extent/ymax")) == 4.0
    assert canvas.findtext("rotation") == "0"
    assert canvas.findtext("rendermaptile") == "0"


def test_download_mbtiles_file_rejects_empty_url(tmp_path):
    """Worker downloader should fail fast on empty basemap URL."""
    field_project = _load_field_project_module()

    with pytest.raises(requests.exceptions.MissingSchema):
        field_project._download_mbtiles_file(
            "",
            tmp_path / "basemap.mbtiles",
            field_project.logging.getLogger(__name__),
        )


def test_download_mbtiles_file_allows_large_stream_without_local_cap(
    monkeypatch, tmp_path
):
    """Worker downloader should stream all bytes without enforcing a local max cap."""
    field_project = _load_field_project_module()

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=0):
            del chunk_size
            yield b"a" * (2 * 1024 * 1024)
            yield b"b" * (2 * 1024 * 1024)

    monkeypatch.setenv("QFIELD_BASEMAP_MAX_BYTES", "1")
    monkeypatch.setattr(
        field_project.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(),
    )

    destination = tmp_path / "basemap.mbtiles"
    field_project._download_mbtiles_file(
        "https://tiles.example.com/large.mbtiles",
        destination,
        field_project.logging.getLogger(__name__),
    )

    assert destination.exists()
    assert destination.stat().st_size == 4 * 1024 * 1024
    """Reader should return project_id and trimmed basemap_url from qgis_jobs."""
    field_project = _load_field_project_module()

    class FakeCursor:
        def __init__(self, row):
            self.row = row

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query, _params):
            return None

        def fetchone(self):
            return self.row

    class FakeConn:
        def __init__(self, row):
            self.row = row

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor(self.row)

    monkeypatch.setattr(
        field_project.psycopg,
        "connect",
        lambda _db_url: FakeConn(
            ("qfc-123", "  https://tiles.example.com/a.mbtiles  ")
        ),
    )

    project_id, basemap_url = field_project._read_basemap_job_inputs("db-url", "job-id")

    assert project_id == "qfc-123"
    assert basemap_url == "https://tiles.example.com/a.mbtiles"


def test_read_basemap_job_inputs_rejects_missing_basemap_url(monkeypatch):
    """Reader should reject rows without a usable basemap_url."""
    field_project = _load_field_project_module()

    class FakeCursor:
        def __init__(self, row):
            self.row = row

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query, _params):
            return None

        def fetchone(self):
            return self.row

    class FakeConn:
        def __init__(self, row):
            self.row = row

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor(self.row)

    monkeypatch.setattr(
        field_project.psycopg,
        "connect",
        lambda _db_url: FakeConn(("qfc-123", "   ")),
    )

    with pytest.raises(RuntimeError, match="Missing basemap_url"):
        field_project._read_basemap_job_inputs("db-url", "job-id")
