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

import geojson
import pytest

from area_splitter.splitter import (
    FMTMSplitter,
    main,
    split_by_features,
    split_by_sql,
    split_by_square,
)

log = logging.getLogger(__name__)
TESTDATA_DIR = str(Path(__file__).parent / "testdata")


def test_init_splitter_types(aoi_json):
    """Test parsing different types with FMTMSplitter."""
    # FeatureCollection
    FMTMSplitter(aoi_json)
    # GeoJSON String
    geojson_str = geojson.dumps(aoi_json)
    FMTMSplitter(geojson_str)
    # GeoJSON File
    FMTMSplitter(f"{TESTDATA_DIR}/kathmandu.geojson")
    # GeoJSON Dict FeatureCollection
    geojson_dict = dict(aoi_json)
    FMTMSplitter(geojson_dict)
    # GeoJSON Dict Feature
    feature = geojson_dict.get("features")[0]
    FMTMSplitter(feature)
    # GeoJSON Dict Polygon
    polygon = feature.get("geometry")
    FMTMSplitter(polygon)
    # FeatureCollection multiple geoms (4 polygons)
    with pytest.raises(ValueError) as error:
        FMTMSplitter(f"{TESTDATA_DIR}/kathmandu_split.geojson")
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
        geojson.dumps(aoi_json.get("features")[0]),
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
            output_geojson = geojson.load(jsonfile)
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
            assert Path(f"{Path(outfile).stem}_{index}.geojson)").exists()
    finally:
        Path(outfile).unlink()


def test_split_by_features_geojson(aoi_json):
    """Test divide by square from geojson file.

    kathmandu_split.json contains 4 polygons inside the kathmandu.json area.
    """
    features = split_by_features(
        aoi_json,
        geojson_input=f"{TESTDATA_DIR}/kathmandu_split.geojson",
    )
    assert len(features.get("features")) == 4


async def test_split_by_sql_fmtm_with_extract(db, aoi_json, extract_json, output_json):
    """Test divide by square from geojson file."""
    features = await split_by_sql(
        aoi_json,
        db,
        num_buildings=5,
        osm_extract=extract_json,
    )
    assert len(features.get("features")) == 68
    assert sorted(features) == sorted(output_json)


async def test_split_by_sql_fmtm_no_extract(aoi_json):
    """Test FMTM splitting algorithm, with no data extract."""
    features = await split_by_sql(
        aoi_json,
        # Use separate db connection for longer running test
        "postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
        num_buildings=5,
    )
    # NOTE This may change over time as it calls the live API
    # so we set to > the output from test_split_by_sql_fmtm_with_extract
    assert len(features.get("features")) >= 60


async def test_split_by_sql_fmtm_multi_geom(extract_json):
    """Test divide by square from geojson file with multiple geometries."""
    with open(f"{TESTDATA_DIR}/kathmandu_split.geojson") as jsonfile:
        parsed_featcol = geojson.load(jsonfile)
    features = await split_by_sql(
        aoi=parsed_featcol,
        db="postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
        num_buildings=10,
        osm_extract=extract_json,
    )

    assert isinstance(features, geojson.feature.FeatureCollection)
    assert isinstance(features.get("features"), list)
    assert isinstance(features.get("features")[0], dict)
    assert len(features.get("features")) == 22

    # Check that all generates features are polygons
    polygons = [
        feature
        for feature in features.get("features", [])
        if feature.get("geometry").get("type") == "Polygon"
    ]
    assert len(polygons) == 22

    polygon_feat = geojson.loads(json.dumps(polygons[0]))
    assert isinstance(polygon_feat, geojson.Feature)

    polygon = geojson.loads(json.dumps(polygons[0].get("geometry")))
    assert isinstance(polygon, geojson.geometry.Polygon)


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
                "postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
                "--meters",
                "100",
                "--extract",
                str(extract_geojson),
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as jsonfile:
            output_geojson = geojson.load(jsonfile)

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
            output_geojson = geojson.load(jsonfile)

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
                "postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
                "--number",
                "10",
                "--extract",
                str(extract_geojson),
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as jsonfile:
            output_geojson = geojson.load(jsonfile)

        assert len(output_geojson.get("features")) == 44
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
                "postgresql://fmtm:fmtm@fmtm-db:5432/fmtm",
                "--number",
                "10",
                "--outfile",
                str(outfile),
            ]
        )
        with open(outfile) as geojson_out:
            output_geojson = geojson.load(geojson_out)

        # NOTE This may change over time as it calls the live API
        # so we set to >= the output from test_split_by_sql_cli
        assert len(output_geojson.get("features")) >= 40
    finally:
        Path(outfile).unlink()
