"""Tests for QField project generator compatibility helpers."""

# ruff: noqa: N802

import logging
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
    assert destination.stat().st_size == (4 * 1024 * 1024)


def test_read_basemap_job_inputs_returns_trimmed_values(monkeypatch):
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


def _make_fake_layer(layer_name: str, layer_id: str):
    """Create a minimal fake layer object for layer-order tests."""

    class FakeLayer:
        def __init__(self, name, layer_id_value):
            self._name = name
            self._id = layer_id_value

        def name(self):
            return self._name

        def id(self):
            return self._id

    return FakeLayer(layer_name, layer_id)


def _make_fake_root(layer_specs: list[tuple[str, str]]):
    """Create a minimal fake root tree supporting reorder operations."""

    class FakeNode:
        def __init__(self, layer):
            self._layer = layer

        def layer(self):
            return self._layer

    class FakeRoot:
        def __init__(self, specs):
            self._children = [
                FakeNode(_make_fake_layer(name, layer_id)) for name, layer_id in specs
            ]

        # noqa: N802 - mimic PyQGIS API
        def children(self):
            return list(self._children)

        # noqa: N802 - mimic PyQGIS API
        def findLayer(self, layer_id):
            for node in self._children:
                if node.layer().id() == layer_id:
                    return node
            return None

        # noqa: N802 - mimic PyQGIS API
        def insertLayer(self, index, layer):
            self._children.insert(index, FakeNode(layer))

        # noqa: N802 - mimic PyQGIS API
        def removeChildNode(self, node):
            self._children.remove(node)

    return FakeRoot(layer_specs)


def _layer_names_from_root(fake_root):
    return [node.layer().name() for node in fake_root.children()]


def test_normalize_root_layer_order_in_field_project_places_basemap_above_osm():
    """Canonical field ordering keeps vectors above basemap and OSM at bottom."""
    field_project = _load_field_project_module()
    fake_root = _make_fake_root(
        [
            ("OpenStreetMap", "osm"),
            ("survey", "survey"),
            ("basemap", "basemap"),
            ("tasks", "tasks"),
            ("notes", "notes"),
        ]
    )

    fake_project = SimpleNamespace(layerTreeRoot=lambda: fake_root)
    field_project._normalize_root_layer_order(
        fake_project, field_project.logging.getLogger(__name__)
    )

    assert _layer_names_from_root(fake_root) == [
        "survey",
        "tasks",
        "notes",
        "basemap",
        "OpenStreetMap",
    ]


def test_normalize_root_layer_order_in_drone_project_places_vectors_above_rasters():
    """Drone ordering keeps task vectors above rasters and OSM at bottom."""
    repo_root = _find_repo_root(Path(__file__).resolve())
    drone_path = _find_existing_file(
        repo_root,
        "src/qfield/drone_project.py",
        "qfield/drone_project.py",
    )

    drone_spec = spec_from_file_location("qfield_drone_project_test", drone_path)
    assert drone_spec is not None and drone_spec.loader is not None
    drone_module = module_from_spec(drone_spec)

    sys_modules = __import__("sys").modules
    sys_modules.setdefault(
        "basemaps", SimpleNamespace(create_osm_basemap=lambda *_args, **_kwargs: None)
    )
    sys_modules.setdefault(
        "sanitize",
        SimpleNamespace(sanitize_generated_qgis_metadata=lambda *args, **kwargs: None),
    )
    sys_modules.setdefault(
        "styling",
        SimpleNamespace(configure_task_layer_style=lambda *args, **kwargs: None),
    )

    drone_spec.loader.exec_module(drone_module)

    fake_root = _make_fake_root(
        [
            ("OpenStreetMap", "osm"),
            ("dem", "dem"),
            ("dtm-tasks", "dtm-tasks"),
            ("basemap", "basemap"),
        ]
    )
    fake_project = SimpleNamespace(layerTreeRoot=lambda: fake_root)

    drone_module._normalize_root_layer_order(
        fake_project, drone_module.logging.getLogger(__name__)
    )

    assert _layer_names_from_root(fake_root) == [
        "dtm-tasks",
        "basemap",
        "dem",
        "OpenStreetMap",
    ]


class _FakeSymbol:
    def __init__(self, props):
        self._props = props

    def symbolLayer(self, _index):
        return self

    def properties(self):
        return self._props


class _FakeRenderer:
    def __init__(self):
        self.symbol = None

    def setSymbol(self, symbol):
        self.symbol = symbol


class _FakeLayerForStyling:
    def __init__(self):
        self._renderer = _FakeRenderer()
        self._flags = 0b1111
        self.labeling = None
        self.labels_enabled = False

    def renderer(self):
        return self._renderer

    def setLabeling(self, labeling):
        self.labeling = labeling

    def setLabelsEnabled(self, enabled):
        self.labels_enabled = enabled

    def triggerRepaint(self):
        return None

    def flags(self):
        return self._flags

    def setFlags(self, flags):
        self._flags = flags

    def geometryType(self):
        return "polygon"


class _FakeQgsFillSymbol:
    @staticmethod
    def createSimple(props):
        return _FakeSymbol(props)


class _FakeQgsLineSymbol:
    @staticmethod
    def createSimple(props):
        return _FakeSymbol(props)


class _FakeQgsMarkerSymbol:
    @staticmethod
    def createSimple(props):
        return _FakeSymbol(props)


class _FakePalLayerSettings:
    def __init__(self):
        self.fieldName = ""
        self.isExpression = False
        self.enabled = False
        self.placement = None
        self.centroidInside = False
        self.centroidWhole = False
        self._format = None

    def setFormat(self, fmt):
        self._format = fmt


class _FakeTextBufferSettings:
    def __init__(self):
        self.enabled = False
        self.size = 0
        self.color = None

    def setEnabled(self, enabled):
        self.enabled = enabled

    def setSize(self, size):
        self.size = size

    def setColor(self, color):
        self.color = color


class _FakeTextFormat:
    def __init__(self):
        self.font = None
        self.size = 0
        self.color = None
        self.buffer = None

    def setFont(self, font):
        self.font = font

    def setSize(self, size):
        self.size = size

    def setColor(self, color):
        self.color = color

    def setBuffer(self, buffer):
        self.buffer = buffer


class _FakeVectorLayerSimpleLabeling:
    def __init__(self, settings):
        self.settings = settings


class _FakeQColor:
    def __init__(self, r, g, b, a=255):
        self.rgba = (r, g, b, a)


class _FakeQFont:
    def __init__(self):
        self.bold = False

    def setBold(self, bold):
        self.bold = bold


def _load_styling_module_with_fakes(monkeypatch):
    repo_root = _find_repo_root(Path(__file__).resolve())
    styling_path = _find_existing_file(
        repo_root,
        "src/qfield/styling.py",
        "qfield/styling.py",
    )

    spec = spec_from_file_location("qfield_styling_test_runtime", styling_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)

    fake_core = SimpleNamespace(
        Qgis=SimpleNamespace(
            GeometryType=SimpleNamespace(Polygon="polygon", Line="line"),
            LabelPlacement=SimpleNamespace(OverPoint="over-point"),
            MapLayerFlag=SimpleNamespace(Identifiable=0b0010),
        ),
        QgsFillSymbol=_FakeQgsFillSymbol,
        QgsLineSymbol=_FakeQgsLineSymbol,
        QgsMarkerSymbol=_FakeQgsMarkerSymbol,
        QgsPalLayerSettings=_FakePalLayerSettings,
        QgsTextBufferSettings=_FakeTextBufferSettings,
        QgsTextFormat=_FakeTextFormat,
        QgsVectorLayerSimpleLabeling=_FakeVectorLayerSimpleLabeling,
    )
    fake_qt_gui = SimpleNamespace(QColor=_FakeQColor, QFont=_FakeQFont)

    monkeypatch.setitem(
        __import__("sys").modules, "qgis", SimpleNamespace(core=fake_core)
    )
    monkeypatch.setitem(__import__("sys").modules, "qgis.core", fake_core)
    monkeypatch.setitem(
        __import__("sys").modules, "qgis.PyQt", SimpleNamespace(QtGui=fake_qt_gui)
    )
    monkeypatch.setitem(__import__("sys").modules, "qgis.PyQt.QtGui", fake_qt_gui)

    spec.loader.exec_module(module)
    return module


def test_configure_task_layer_style_sets_blue_stroke_and_non_identifiable(
    monkeypatch,
):
    """Task style uses transparent fill, blue stroke, and disables identify."""
    styling = _load_styling_module_with_fakes(monkeypatch)
    layer = _FakeLayerForStyling()

    styling.configure_task_layer_style(layer, logging.getLogger(__name__))

    symbol_props = layer.renderer().symbol.symbolLayer(0).properties()
    assert symbol_props["color"] == "0,0,0,0"
    assert symbol_props["outline_color"] == "66,133,244,255"
    assert layer.flags() == 0b1101


def test_configure_survey_layer_style_sets_transparent_fill_grey_stroke(monkeypatch):
    """Survey style uses transparent fill with grey stroke."""
    styling = _load_styling_module_with_fakes(monkeypatch)
    layer = _FakeLayerForStyling()

    styling.configure_survey_layer_style(layer, logging.getLogger(__name__))

    symbol_props = layer.renderer().symbol.symbolLayer(0).properties()
    assert symbol_props["color"] == "0,0,0,0"
    assert symbol_props["outline_color"] == "64,66,72,255"
