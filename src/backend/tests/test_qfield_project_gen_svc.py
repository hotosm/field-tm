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

    sanitize_spec = spec_from_file_location("qfield_sanitize", sanitize_path)
    assert sanitize_spec is not None and sanitize_spec.loader is not None

    sanitize_module = module_from_spec(sanitize_spec)
    sanitize_spec.loader.exec_module(sanitize_module)

    return SimpleNamespace(
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
            apply_styles_from_dir=lambda *args, **kwargs: set(),
            set_layer_not_identifiable=lambda *args, **kwargs: None,
            unpack_plugin_zip=lambda *args, **kwargs: None,
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


def test_write_job_outputs_preserves_subdirectory_paths(monkeypatch, tmp_path):
    """Plugin tree (``plugins/livefield/main.qml`` etc.) must survive the DB roundtrip.

    Regression: ``_write_job_outputs`` previously used ``iterdir`` and keyed by
    ``file_path.name``, so QField companion plugins under ``plugins/`` were
    silently dropped before upload to QFieldCloud.
    """
    import base64
    import json

    field_project = _load_field_project_module()

    final_dir = tmp_path / "final"
    final_dir.mkdir()
    (final_dir / "project.qgz").write_bytes(b"qgz body")
    (final_dir / "project.qml").write_bytes(b"plugin body")
    (final_dir / "styles").mkdir()
    (final_dir / "styles" / "tasks.qml").write_bytes(b"<qgis tasks/>")
    (final_dir / "plugins" / "livefield").mkdir(parents=True)
    (final_dir / "plugins" / "livefield" / "main.qml").write_bytes(b"livefield body")
    (final_dir / "plugins" / "livefield" / "metadata.txt").write_bytes(b"meta")
    (final_dir / "plugins" / "next-theme").mkdir(parents=True)
    (final_dir / "plugins" / "next-theme" / "main.qml").write_bytes(b"next-theme body")
    (final_dir / "skipme.mbtiles").write_bytes(b"large")

    captured: dict = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query, params):
            captured["payload"] = params[0]
            captured["job_id"] = params[1]

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            return None

    monkeypatch.setattr(field_project.psycopg, "connect", lambda _db_url: FakeConn())

    num_files = field_project._write_job_outputs(
        "db-url",
        "job-1",
        final_dir,
        field_project.logging.getLogger(__name__),
        excluded_suffixes=(".mbtiles",),
    )

    output_files = json.loads(captured["payload"])
    assert num_files == len(output_files)
    assert set(output_files.keys()) == {
        "project.qgz",
        "project.qml",
        "styles/tasks.qml",
        "plugins/livefield/main.qml",
        "plugins/livefield/metadata.txt",
        "plugins/next-theme/main.qml",
    }
    assert (
        base64.b64decode(output_files["plugins/livefield/main.qml"])
        == b"livefield body"
    )
    assert (
        base64.b64decode(output_files["plugins/next-theme/main.qml"])
        == b"next-theme body"
    )


def test_register_plugin_data_dirs_adds_top_level_subdirs_to_project_entry(tmp_path):
    """QFieldSync/dataDirs must list every unpacked plugin subdir.

    Without this entry, libqfieldsync's OfflineConverter strips plugin
    subdirs (``plugins/``, ``styles/``) during QFieldCloud packaging --
    only the .qgz and the ``{basename}.qml`` project plugin survive --
    so QField's plugin loader on the device hits "file doesn't exist".
    """
    field_project = _load_field_project_module()

    (tmp_path / "project.qgz").write_bytes(b"qgz body")
    (tmp_path / "project.qml").write_bytes(b"plugin body")
    (tmp_path / "plugins" / "livefield").mkdir(parents=True)
    (tmp_path / "plugins" / "livefield" / "main.qml").write_bytes(b"livefield")
    (tmp_path / "plugins" / "next-theme").mkdir(parents=True)
    (tmp_path / "plugins" / "next-theme" / "main.qml").write_bytes(b"next-theme")
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "tasks.qml").write_bytes(b"<qgis/>")

    written: dict = {}

    class FakeProject:
        def readListEntry(self, scope, key, default):  # noqa: N802
            return list(default), True

        def writeEntry(self, scope, key, value):  # noqa: N802
            written[(scope, key)] = value
            return True

    field_project._register_plugin_data_dirs(
        FakeProject(), tmp_path, field_project.logging.getLogger(__name__)
    )

    assert written.get(("QFieldSync", "dataDirs")) == ["plugins", "styles"]


def test_register_plugin_data_dirs_merges_existing_and_skips_unchanged_write(
    tmp_path,
):
    """Existing dataDirs are preserved; no write happens when nothing new is added."""
    field_project = _load_field_project_module()

    (tmp_path / "plugins").mkdir()
    (tmp_path / "styles").mkdir()

    write_calls: list = []

    class FakeProject:
        def __init__(self, existing):
            self.existing = existing

        def readListEntry(self, scope, key, default):  # noqa: N802
            return list(self.existing), True

        def writeEntry(self, scope, key, value):  # noqa: N802
            write_calls.append((scope, key, value))
            return True

    field_project._register_plugin_data_dirs(
        FakeProject(["DCIM"]), tmp_path, field_project.logging.getLogger(__name__)
    )
    assert write_calls == [("QFieldSync", "dataDirs", ["DCIM", "plugins", "styles"])]

    write_calls.clear()
    field_project._register_plugin_data_dirs(
        FakeProject(["plugins", "styles"]),
        tmp_path,
        field_project.logging.getLogger(__name__),
    )
    assert write_calls == []


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
        SimpleNamespace(
            apply_styles_from_dir=lambda *args, **kwargs: set(),
            set_layer_not_identifiable=lambda *args, **kwargs: None,
            unpack_plugin_zip=lambda *args, **kwargs: None,
        ),
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
            MapLayerFlag=SimpleNamespace(Identifiable=0b0010),
        ),
        QgsMapLayer=SimpleNamespace(
            StyleCategory=SimpleNamespace(Labeling=0b01, Symbology=0b10),
        ),
    )

    monkeypatch.setitem(
        __import__("sys").modules, "qgis", SimpleNamespace(core=fake_core)
    )
    monkeypatch.setitem(__import__("sys").modules, "qgis.core", fake_core)

    spec.loader.exec_module(module)
    return module


def test_unpack_plugin_zip_renames_main_qml_and_returns_styles_dir(
    monkeypatch, tmp_path
):
    """``main.qml`` is renamed to ``{basename}.qml`` and styles/ is reported."""
    import io
    import zipfile

    styling = _load_styling_module_with_fakes(monkeypatch)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.qml", "plugin body")
        zf.writestr("styles/tasks.qml", "<qgis/>")
        zf.writestr("styles/survey.qml", "<qgis/>")

    styles_dir = styling.unpack_plugin_zip(
        buf.getvalue(), tmp_path, "myproject", logging.getLogger(__name__)
    )

    assert (tmp_path / "myproject.qml").read_text() == "plugin body"
    assert not (tmp_path / "main.qml").exists()
    assert styles_dir == tmp_path / "styles"
    assert (styles_dir / "tasks.qml").is_file()


def test_unpack_plugin_zip_strips_wrapping_directory(monkeypatch, tmp_path):
    """A single wrapping directory inside the zip is stripped on unpack."""
    import io
    import zipfile

    styling = _load_styling_module_with_fakes(monkeypatch)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("qfield-plugin/main.qml", "plugin body")
        zf.writestr("qfield-plugin/styles/tasks.qml", "<qgis/>")

    styling.unpack_plugin_zip(
        buf.getvalue(), tmp_path, "p", logging.getLogger(__name__)
    )

    assert (tmp_path / "p.qml").is_file()
    assert (tmp_path / "styles" / "tasks.qml").is_file()
    assert not (tmp_path / "qfield-plugin").exists()


def test_apply_styles_from_dir_calls_load_named_style_for_matching_layers(
    monkeypatch, tmp_path
):
    """Each ``{layer}.qml`` is applied to the layer with that name."""
    styling = _load_styling_module_with_fakes(monkeypatch)

    (tmp_path / "tasks.qml").write_text("<qgis/>")
    (tmp_path / "project-area.qml").write_text("<qgis/>")
    (tmp_path / "no-such-layer.qml").write_text("<qgis/>")

    calls: list[tuple[str, str]] = []

    class _FakeStyledLayer:
        def __init__(self, name: str) -> None:
            self._name = name

        def name(self) -> str:
            return self._name

        def loadNamedStyle(self, path, default, categories):  # noqa: N802
            calls.append((self._name, path))
            return ("", True)

        def triggerRepaint(self):  # noqa: N802
            return None

    layers = {
        "tasks": _FakeStyledLayer("tasks"),
        "project-area": _FakeStyledLayer("project-area"),
    }

    class _FakeProject:
        def mapLayersByName(self, name):  # noqa: N802
            return [layers[name]] if name in layers else []

    styled = styling.apply_styles_from_dir(
        _FakeProject(), tmp_path, logging.getLogger(__name__)
    )

    assert styled == {"tasks", "project-area"}
    called_layers = {name for name, _ in calls}
    assert called_layers == {"tasks", "project-area"}
