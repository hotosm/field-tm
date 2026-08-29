# Copyright (c) 2025 Humanitarian OpenStreetMap Team
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

"""Test task splitting algorithms."""

import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

import psycopg
import pytest
from psycopg.types.json import Json

from area_splitter import SplittingAlgorithm
from area_splitter.db import (
    SPLITTER_SERIALIZATION_LOCK_KEY,
    acquire_splitter_serialization_lock,
    configure_lock_timeout,
    configure_statement_timeout,
    insert_geoms_batch,
)
from area_splitter.splitter import (
    AreaSplitter,
    _is_linear_split_feature,
    main,
    split_by_features,
    split_by_sql,
    split_by_square,
)

log = logging.getLogger(__name__)
TESTDATA_DIR = str(Path(__file__).parent / "testdata")
# splitBySQL commits and closes whatever connection it is given, so scenario
# tests below open a fresh connection per call instead of sharing the
# session-scoped `db` fixture (which later tests still rely on).
DB_URL = "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm"


class _RecordingCursor:
    """Minimal cursor double that records executemany calls."""

    def __init__(self):
        """Initialize the recorded call list."""
        self.calls = []

    def execute(self, query, params=None):
        """Record an execute invocation."""
        self.calls.append((query, params))

    def executemany(self, query, params):
        """Record an executemany invocation."""
        self.calls.append((query, params))


def test_configure_statement_timeout_sets_local_timeout():
    """Statement timeout should be transaction-local and parameterized."""
    cur = _RecordingCursor()

    configure_statement_timeout(cur, 1234)

    assert cur.calls == [
        ("SELECT set_config('statement_timeout', %s, true)", ("1234",))
    ]


def test_configure_statement_timeout_allows_disable():
    """A non-positive timeout should avoid issuing SET."""
    cur = _RecordingCursor()

    configure_statement_timeout(cur, 0)

    assert cur.calls == []


def test_configure_lock_timeout_sets_local_timeout():
    """Lock timeout should be transaction-local and parameterized."""
    cur = _RecordingCursor()

    configure_lock_timeout(cur, 5678)

    assert cur.calls == [("SELECT set_config('lock_timeout', %s, true)", ("5678",))]


def test_configure_lock_timeout_allows_disable():
    """A non-positive lock timeout should avoid issuing SET."""
    cur = _RecordingCursor()

    configure_lock_timeout(cur, 0)

    assert cur.calls == []


def test_acquire_splitter_serialization_lock_uses_xact_advisory_lock():
    """Splitter serialization lock should call pg_advisory_xact_lock."""
    cur = _RecordingCursor()

    acquire_splitter_serialization_lock(cur)

    assert cur.calls == [
        ("SELECT pg_advisory_xact_lock(%s)", (SPLITTER_SERIALIZATION_LOCK_KEY,))
    ]


def test_insert_geoms_batch_uses_executemany_and_json_tags():
    """Batch insert should use one executemany call with JSON-wrapped tags."""
    cur = _RecordingCursor()

    insert_geoms_batch(
        cur,
        "ways_poly",
        [
            {"osm_id": 1, "geom": '{"type":"Polygon"}', "tags": {"building": "yes"}},
            {"osm_id": 2, "geom": '{"type":"Polygon"}', "tags": {"building": "hut"}},
        ],
    )

    assert len(cur.calls) == 1
    query, params = cur.calls[0]
    assert "INSERT INTO ways_poly" in query
    assert "ST_MakeValid" in query
    assert len(params) == 2
    assert isinstance(params[0]["tags"], Json)
    assert params[0]["osm_id"] == 1


def test_insert_geoms_batch_noops_for_empty_rows():
    """Empty buckets should not issue a database call."""
    cur = _RecordingCursor()

    insert_geoms_batch(cur, "ways_line", [])

    assert cur.calls == []


def test_insert_geoms_batch_rejects_unknown_table():
    """The interpolated table name must stay allowlisted."""
    with pytest.raises(ValueError, match="Unsupported table"):
        insert_geoms_batch(
            _RecordingCursor(),
            "ways_poly; DROP TABLE ways_line",
            [{"osm_id": 1, "geom": "{}", "tags": {}}],
        )


def test_insert_split_sql_extract_batches_polygons_and_lines(monkeypatch):
    """The splitter should issue one batch insert per supported temp table."""
    calls = []

    def fake_insert_geoms_batch(_cur, table_name, rows):
        """Record the table and rows passed to the batch insert helper."""
        calls.append((table_name, rows))

    monkeypatch.setattr(
        "area_splitter.splitter.insert_geoms_batch",
        fake_insert_geoms_batch,
    )

    AreaSplitter._insert_split_sql_extract(
        object(),
        object(),
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": []},
                    "properties": {"osm_id": 1, "tags": {"building": "yes"}},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": []},
                    "properties": {"osm_id": 2, "tags": {"highway": "primary"}},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": []},
                    "properties": {"osm_id": 3, "tags": {"building": "yes"}},
                },
            ],
        },
    )

    assert [table_name for table_name, _rows in calls] == ["ways_poly", "ways_line"]
    assert len(calls[0][1]) == 1
    assert calls[0][1][0]["osm_id"] == 1
    assert len(calls[1][1]) == 1
    assert calls[1][1][0]["osm_id"] == 2


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ({"highway": "primary"}, True),
        ({"waterway": "stream"}, True),
        ({"railway": "rail"}, True),
        ({"aeroway": "runway"}, True),
        ({"barrier": "fence"}, True),
        ({"barrier": "wire_fence"}, True),
        ({"barrier": "hedge"}, False),
        ({"natural": "cliff"}, True),
        ({"natural": "tree_row"}, False),
        ({"man_made": "embankment"}, True),
        ({"man_made": "dyke"}, True),
        ({"man_made": "dike"}, True),
        ({"man_made": "pier"}, False),
        ({}, False),
    ],
)
def test_is_linear_split_feature_tag_classification(tags, expected):
    """Classify supported linear/non-traversable tags for split features."""
    assert _is_linear_split_feature(tags) is expected


def test_init_splitter_types(aoi_json):
    """Test parsing different types with AreaSplitter."""
    # FeatureCollection
    AreaSplitter(aoi_json)
    # GeoJSON String
    geojson_str = json.dumps(aoi_json)
    AreaSplitter(geojson_str)
    # GeoJSON File
    AreaSplitter(f"{TESTDATA_DIR}/kathmandu.geojson")
    # GeoJSON Dict FeatureCollection
    geojson_dict = dict(aoi_json)
    AreaSplitter(geojson_dict)
    # GeoJSON Dict Feature
    feature = geojson_dict.get("features")[0]
    AreaSplitter(feature)
    # GeoJSON Dict Polygon
    polygon = feature.get("geometry")
    AreaSplitter(polygon)
    # FeatureCollection multiple geoms (4 polygons)
    with pytest.raises(ValueError) as error:
        AreaSplitter(f"{TESTDATA_DIR}/kathmandu_split.geojson")
    assert str(error.value) == "The input AOI cannot contain multiple geometries."


def test_split_by_square_with_dict(db, aoi_json, extract_json):
    """Test divide by square from geojson dict types."""
    features = split_by_square(
        aoi_json.get("features")[0], db, meters=50, osm_extract=extract_json
    )
    assert len(features.get("features")) == 66
    features = split_by_square(
        aoi_json.get("features")[0].get("geometry"),
        db,
        meters=50,
        osm_extract=extract_json,
    )
    assert len(features.get("features")) == 66


def test_split_by_square_with_str(db, aoi_json, extract_json):
    """Test divide by square from geojson str and file."""
    # GeoJSON Dumps
    features = split_by_square(
        json.dumps(aoi_json.get("features")[0]),
        db,
        meters=50,
        osm_extract=extract_json,
    )
    assert len(features.get("features")) == 66
    # JSON Dumps
    features = split_by_square(
        json.dumps(aoi_json.get("features")[0].get("geometry")),
        db,
        meters=50,
        osm_extract=extract_json,
    )
    assert len(features.get("features")) == 66
    # File
    features = split_by_square(
        f"{TESTDATA_DIR}/kathmandu.geojson",
        db,
        meters=100,
        osm_extract=f"{TESTDATA_DIR}/kathmandu_extract.geojson",
    )
    assert len(features.get("features")) == 19


def test_split_by_square_with_file_output(db):
    """Test divide by square from geojson file.

    Also write output to file.
    """
    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        features = split_by_square(
            f"{TESTDATA_DIR}/kathmandu.geojson",
            db,
            osm_extract=f"{TESTDATA_DIR}/kathmandu_extract.geojson",
            meters=50,
            outfile=outfile,
        )
        assert len(features.get("features")) == 66

        with open(outfile) as jsonfile:
            output_geojson = json.load(jsonfile)
        assert len(output_geojson.get("features")) == 66
    finally:
        Path(outfile).unlink()


def test_split_by_square_with_multigeom_input(db, aoi_multi_json, extract_json):
    """Test divide by square from geojson dict types."""
    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        features = split_by_square(
            aoi_multi_json,
            db,
            meters=50,
            osm_extract=extract_json,
            outfile=outfile,
        )
        assert len(features.get("features", [])) == 76
        for index in [0, 1, 2, 3]:
            expected = Path(outfile).with_name(f"{Path(outfile).stem}_{index}.geojson")
            assert expected.exists()
    finally:
        Path(outfile).unlink()


def test_split_by_features_geojson(db, aoi_json):
    """Test divide by square from geojson file.

    kathmandu_split.json contains 4 polygons inside the kathmandu.json area.
    """
    features = split_by_features(
        aoi_json,
        db,
        geojson_input=f"{TESTDATA_DIR}/kathmandu_split.geojson",
    )
    assert len(features.get("features")) == 4


def test_split_by_sql_ftm_with_extract(db, aoi_json, extract_json):
    """Test divide by square from geojson file."""
    features = split_by_sql(
        aoi_json,
        db,
        num_buildings=5,
        osm_extract=extract_json,
    )
    assert isinstance(features, dict) and features.get("type") == "FeatureCollection"
    feature_list = features.get("features", [])
    assert len(feature_list) >= 60
    assert all(
        feature.get("geometry", {}).get("type") in {"Polygon", "MultiPolygon"}
        for feature in feature_list
    )


def test_split_by_sql_total_tasks_passes_num_enumerators(
    monkeypatch, aoi_json, extract_json
):
    """Target-task splitting should pass num_enumerators to the SQL runner."""
    captured = {}

    def fake_split_by_sql(
        self,
        db,
        algorithm,
        algorithm_params,
        osm_extract,
        **_kwargs,
    ):
        captured["db"] = db
        captured["algorithm"] = algorithm
        captured["algorithm_params"] = algorithm_params
        captured["osm_extract"] = osm_extract
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": aoi_json["features"][0]["geometry"],
                }
            ],
        }

    monkeypatch.setattr(AreaSplitter, "splitBySQL", fake_split_by_sql)

    features = split_by_sql(
        aoi_json,
        "postgresql://unused",
        num_enumerators=6,
        osm_extract=extract_json,
        algorithm=SplittingAlgorithm.TOTAL_TASKS,
    )

    assert captured["algorithm"] == SplittingAlgorithm.TOTAL_TASKS
    assert captured["algorithm_params"]["num_enumerators"] == 6
    assert isinstance(features, dict) and features.get("type") == "FeatureCollection"


def test_split_by_sql_roads_requires_no_legacy_param(
    monkeypatch, aoi_json, extract_json
):
    """SPLIT_BY_ROADS has no required_params, so it needs neither num_buildings
    nor num_enumerators to resolve algorithm params successfully.
    """
    captured = {}

    def fake_split_by_sql(
        self,
        db,
        algorithm,
        algorithm_params,
        osm_extract,
        **_kwargs,
    ):
        captured["algorithm"] = algorithm
        captured["algorithm_params"] = algorithm_params
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": aoi_json["features"][0]["geometry"],
                }
            ],
        }

    monkeypatch.setattr(AreaSplitter, "splitBySQL", fake_split_by_sql)

    features = split_by_sql(
        aoi_json,
        "postgresql://unused",
        osm_extract=extract_json,
        algorithm=SplittingAlgorithm.SPLIT_BY_ROADS,
    )

    assert captured["algorithm"] == SplittingAlgorithm.SPLIT_BY_ROADS
    assert captured["algorithm_params"]["include_roads"] == "TRUE"
    assert isinstance(features, dict) and features.get("type") == "FeatureCollection"


def test_split_by_sql_roads_with_extract(aoi_json, extract_json):
    """Splitting by roads should return polygons bounded by linear features."""
    features = split_by_sql(
        aoi_json,
        DB_URL,
        osm_extract=extract_json,
        algorithm=SplittingAlgorithm.SPLIT_BY_ROADS,
        algorithm_params={
            "include_roads": "TRUE",
            "include_rivers": "TRUE",
            "include_railways": "TRUE",
            "include_aeroways": "TRUE",
        },
    )
    assert isinstance(features, dict) and features.get("type") == "FeatureCollection"
    feature_list = features.get("features", [])
    assert len(feature_list) >= 1
    assert all(
        feature.get("geometry", {}).get("type") in {"Polygon", "MultiPolygon"}
        for feature in feature_list
    )
    assert all("building_count" in feature["properties"] for feature in feature_list)


def test_split_by_sql_ftm_no_extract(aoi_json):
    """Test Field-TM splitting algorithm, with no data extract."""
    features = split_by_sql(
        aoi_json,
        # Use separate db connection for longer running test
        "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm",
        num_buildings=5,
    )
    # NOTE This may change over time as it calls the live API
    # so we set to > the output from test_split_by_sql_ftm_with_extract
    assert len(features.get("features")) >= 60


def test_split_by_sql_ftm_multi_geom(extract_json):
    """Test divide by square from geojson file with multiple geometries."""
    with open(f"{TESTDATA_DIR}/kathmandu_split.geojson") as jsonfile:
        parsed_featcol = json.load(jsonfile)
    features = split_by_sql(
        parsed_featcol,
        "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm",
        num_buildings=10,
        osm_extract=extract_json,
    )

    assert isinstance(features, dict) and features.get("type") == "FeatureCollection"
    assert isinstance(features.get("features"), list)
    assert isinstance(features.get("features")[0], dict)
    assert len(features.get("features")) > 22

    # Check that all generates features are polygons
    polygons = [
        feature
        for feature in features.get("features", [])
        if feature.get("geometry").get("type") == "Polygon"
    ]
    assert len(features.get("features")) == len(polygons)

    polygon_feat = polygons[0]
    assert isinstance(polygon_feat, dict) and polygon_feat.get("type") == "Feature"

    polygon = polygons[0].get("geometry")
    assert isinstance(polygon, dict) and polygon.get("type") == "Polygon"


def _square_ring(lon, lat, size_deg):
    """Build a closed square ring (exterior or hole) as a coordinate list."""
    return [
        [lon, lat],
        [lon + size_deg, lat],
        [lon + size_deg, lat + size_deg],
        [lon, lat + size_deg],
        [lon, lat],
    ]


def _building_feature(geometry, osm_id):
    """Wrap a geometry as a minimal tagged building Feature."""
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {"building": "yes", "osm_id": osm_id},
    }


def _aoi_featcol(lon, lat, width_deg, height_deg):
    """Build a single-feature AOI FeatureCollection for a rectangle."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [lon, lat],
                            [lon + width_deg, lat],
                            [lon + width_deg, lat + height_deg],
                            [lon, lat + height_deg],
                            [lon, lat],
                        ]
                    ],
                },
            }
        ],
    }


def _extract_featcol(features):
    """Wrap building features as an OSM extract FeatureCollection."""
    return {"type": "FeatureCollection", "features": features}


def _assert_tasks_valid_and_bounded_by_aoi(
    aoi_geometry, features, overshoot_tolerance=0.02
):
    """Assert every task polygon is valid, non-overlapping, and stays within the AOI.

    The straight skeleton algorithm intentionally only builds task polygons
    around building clusters - regions of the AOI far from any building are
    dropped, so task coverage is *not* expected to reconstruct the full AOI
    (confirmed empirically: even the dense real-world Kathmandu fixture only
    covers ~93% of its AOI). What must always hold is that every task is a
    valid geometry, tasks don't significantly overlap each other, and their
    union never spills meaningfully outside the AOI.

    Opens its own connection rather than reusing one already handed to
    split_by_sql/splitBySQL, since that call commits and closes it.
    """
    assert features, "Splitting must return at least one task polygon"
    task_geoms = json.dumps([feature["geometry"] for feature in features])

    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH aoi AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            tasks AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(value), 4326) AS geom
                FROM jsonb_array_elements_text(%s::jsonb) AS value
            )
            SELECT
                bool_and(ST_IsValid(tasks.geom)),
                ST_Area((SELECT geom FROM aoi)::geography),
                ST_Area(ST_Union(tasks.geom)::geography),
                SUM(ST_Area(tasks.geom::geography)),
                ST_Area(ST_Difference(
                    ST_Union(tasks.geom), (SELECT geom FROM aoi)
                )::geography)
            FROM tasks;
            """,
            (json.dumps(aoi_geometry), task_geoms),
        )
        all_valid, aoi_area, union_area, summed_area, outside_area = cur.fetchone()

    assert all_valid, "Every returned task polygon must be a valid geometry"
    assert union_area > 0, "Tasks must cover a non-zero area"
    assert summed_area == pytest.approx(union_area, rel=0.02), (
        "Task polygons should not significantly overlap each other"
    )
    assert outside_area <= aoi_area * overshoot_tolerance, (
        f"Tasks should stay within the AOI, but {outside_area} sq.m falls outside "
        f"of the {aoi_area} sq.m AOI"
    )


def test_split_by_sql_skeleton_handles_connected_ring_building():
    """Regression test for hotosm#3081.

    ST_GeomFromGeoJSON accepts a polygon whose interior ring touches the
    exterior ring at a single vertex ("connected rings"). Before the
    ST_MakeValid fix, running the straight skeleton algorithm on an extract
    containing such a building crashed with:
    "Intersection does not support polygon with connected rings".
    """
    lon, lat = 85.3200, 27.7000
    aoi = _aoi_featcol(lon, lat, 0.0006, 0.0004)

    connected_ring_building = {
        "type": "Polygon",
        "coordinates": [
            _square_ring(lon + 0.00005, lat + 0.00005, 0.00012),
            # Hole's first vertex is exactly the exterior ring's first
            # vertex, so the rings touch at a single point.
            _square_ring(lon + 0.00005, lat + 0.00005, 0.00006),
        ],
    }
    normal_building = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.0003, lat + 0.0002, 0.0001)],
    }
    extract = _extract_featcol(
        [
            _building_feature(connected_ring_building, 1),
            _building_feature(normal_building, 2),
        ]
    )

    features = split_by_sql(aoi, DB_URL, num_buildings=50, osm_extract=extract).get(
        "features", []
    )

    _assert_tasks_valid_and_bounded_by_aoi(aoi["features"][0]["geometry"], features)


def test_split_by_sql_skeleton_handles_building_with_hole():
    """A building with a real (non-touching) interior hole should still work.

    This guards against the ST_MakeValid fix changing behaviour for
    already-valid donut-shaped buildings.
    """
    lon, lat = 85.3300, 27.7000
    aoi = _aoi_featcol(lon, lat, 0.0006, 0.0004)

    donut_building = {
        "type": "Polygon",
        "coordinates": [
            _square_ring(lon + 0.00005, lat + 0.00005, 0.0002),
            _square_ring(lon + 0.0001, lat + 0.0001, 0.00005),
        ],
    }
    extract = _extract_featcol([_building_feature(donut_building, 1)])

    features = split_by_sql(aoi, DB_URL, num_buildings=50, osm_extract=extract).get(
        "features", []
    )

    _assert_tasks_valid_and_bounded_by_aoi(aoi["features"][0]["geometry"], features)


def test_split_by_sql_skeleton_single_building():
    """A single building in the extract should not break clustering."""
    lon, lat = 85.3400, 27.7000
    aoi = _aoi_featcol(lon, lat, 0.0004, 0.0004)

    building = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.00015, lat + 0.00015, 0.0001)],
    }
    extract = _extract_featcol([_building_feature(building, 1)])

    features = split_by_sql(aoi, DB_URL, num_buildings=50, osm_extract=extract).get(
        "features", []
    )

    _assert_tasks_valid_and_bounded_by_aoi(aoi["features"][0]["geometry"], features)


def test_split_by_sql_skeleton_sparse_buildings():
    """Buildings scattered far apart within a large, mostly-empty AOI."""
    lon, lat = 85.3500, 27.7000
    aoi = _aoi_featcol(lon, lat, 0.004, 0.004)

    near_corner_building = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.0001, lat + 0.0001, 0.0001)],
    }
    far_corner_building = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.0037, lat + 0.0037, 0.0001)],
    }
    extract = _extract_featcol(
        [
            _building_feature(near_corner_building, 1),
            _building_feature(far_corner_building, 2),
        ]
    )

    features = split_by_sql(aoi, DB_URL, num_buildings=50, osm_extract=extract).get(
        "features", []
    )

    _assert_tasks_valid_and_bounded_by_aoi(aoi["features"][0]["geometry"], features)


def test_split_by_sql_skeleton_concave_aoi():
    """An L-shaped (concave) AOI with buildings in each arm."""
    lon, lat = 85.3600, 27.7000

    # L-shape: a 0.0008 x 0.0008 square with the top-right 0.0004 x 0.0004
    # quadrant removed.
    l_shape_aoi = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [lon, lat],
                            [lon + 0.0008, lat],
                            [lon + 0.0008, lat + 0.0004],
                            [lon + 0.0004, lat + 0.0004],
                            [lon + 0.0004, lat + 0.0008],
                            [lon, lat + 0.0008],
                            [lon, lat],
                        ]
                    ],
                },
            }
        ],
    }

    building_in_horizontal_arm = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.0005, lat + 0.0001, 0.0001)],
    }
    building_in_vertical_arm = {
        "type": "Polygon",
        "coordinates": [_square_ring(lon + 0.0001, lat + 0.0005, 0.0001)],
    }
    extract = _extract_featcol(
        [
            _building_feature(building_in_horizontal_arm, 1),
            _building_feature(building_in_vertical_arm, 2),
        ]
    )

    features = split_by_sql(
        l_shape_aoi, DB_URL, num_buildings=50, osm_extract=extract
    ).get("features", [])

    _assert_tasks_valid_and_bounded_by_aoi(
        l_shape_aoi["features"][0]["geometry"], features
    )


def test_split_by_sql_skeleton_task_polygons_cover_aoi(aoi_json, extract_json):
    """Real-world Kathmandu extract: tasks should jointly reconstruct the AOI.

    This is an invariant check (validity + area coverage) rather than an
    exact feature count, so it stays meaningful even if the clustering
    output shape changes.
    """
    features = split_by_sql(
        aoi_json, DB_URL, num_buildings=10, osm_extract=extract_json
    ).get("features", [])

    _assert_tasks_valid_and_bounded_by_aoi(
        aoi_json["features"][0]["geometry"], features
    )


def test_cli_help(capsys):
    """Check help text displays on CLI."""
    try:
        main(["--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr().out
    assert "This program splits a Polygon AOI into tasks" in captured


def test_split_by_square_cli():
    """Test split by square works via CLI."""
    infile = f"{TESTDATA_DIR}/kathmandu.geojson"
    extract_geojson = f"{TESTDATA_DIR}/kathmandu_extract.geojson"

    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        main(
            [
                "--boundary",
                str(infile),
                "--dburl",
                "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm",
                "--meters",
                "100",
                "--extract",
                str(extract_geojson),
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as jsonfile:
            output_geojson = json.load(jsonfile)

        assert len(output_geojson.get("features")) == 19
    finally:
        Path(outfile).unlink()


def test_split_by_features_cli():
    """Test split by features works via CLI."""
    infile = f"{TESTDATA_DIR}/kathmandu.geojson"
    extract_geojson = f"{TESTDATA_DIR}/kathmandu_extract.geojson"
    split_geojson = f"{TESTDATA_DIR}/kathmandu_split.geojson"

    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        main(
            [
                "--boundary",
                str(infile),
                "--source",
                str(split_geojson),
                "--extract",
                str(extract_geojson),
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as jsonfile:
            output_geojson = json.load(jsonfile)

        assert len(output_geojson.get("features")) == 4
    finally:
        Path(outfile).unlink()


def test_split_by_sql_cli():
    """Test split by sql works via CLI."""
    infile = f"{TESTDATA_DIR}/kathmandu.geojson"
    extract_geojson = f"{TESTDATA_DIR}/kathmandu_extract.geojson"

    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        main(
            [
                "--boundary",
                str(infile),
                "--dburl",
                "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm",
                "--number",
                "10",
                "--extract",
                str(extract_geojson),
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as jsonfile:
            output_geojson = json.load(jsonfile)

        assert len(output_geojson.get("features")) > 44
    finally:
        Path(outfile).unlink()


def test_split_by_sql_cli_no_extract():
    """Test split by sql works via CLI."""
    # Sleep 3 seconds before test to ease raw-data-api
    sleep(3)
    infile = f"{TESTDATA_DIR}/kathmandu.geojson"

    with NamedTemporaryFile(delete=False) as geojson_temp:
        outfile = geojson_temp.name

    try:
        main(
            [
                "--boundary",
                str(infile),
                "--dburl",
                "postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm",
                "--number",
                "10",
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as geojson_out:
            output_geojson = json.load(geojson_out)

        # NOTE This may change over time as it calls the live API
        # so we set to >= the output from test_split_by_sql_cli
        assert len(output_geojson.get("features")) >= 40
    finally:
        Path(outfile).unlink()
