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

"""Configuration and fixtures for PyTest."""

import logging
import sys
from pathlib import Path

import geojson
import psycopg
import pytest

logging.basicConfig(
    level="DEBUG",
    format=(
        "%(asctime)s.%(msecs)03d [%(levelname)s] "
        "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def db():
    """Existing psycopg connection."""
    return psycopg.connect("postgresql://fieldtm:fieldtm@fieldtm-db:5432/fieldtm")


@pytest.fixture(scope="session")
def aoi_json():
    """Dummy AOI GeoJSON."""
    path = Path(__file__).parent / "testdata" / "kathmandu.geojson"
    with open(path) as jsonfile:
        return geojson.load(jsonfile)


@pytest.fixture(scope="session")
def aoi_multi_json():
    """Dummy AOI GeoJSON, composed of multiple geometries.

    This takes the standard kathmandu AOI, splits into 4 equal squares.
    The result when merged should equal the original AOI.
    """
    path = Path(__file__).parent / "testdata" / "kathmandu.geojson"
    with open(path) as jsonfile:
        parsed_geojson = geojson.load(jsonfile)
    outer_ring = (
        parsed_geojson.get("features")[0].get("geometry").get("coordinates", [[]])[0]
    )
    lons = [c[0] for c in outer_ring]
    lats = [c[1] for c in outer_ring]
    minx, miny, maxx, maxy = min(lons), min(lats), max(lons), max(lats)

    # Divide the bounding box into four equal squares
    width = (maxx - minx) / 2
    height = (maxy - miny) / 2

    squares = []
    for i in range(2):
        for j in range(2):
            # Calculate coordinates for each square
            x1 = minx + i * width
            y1 = miny + j * height
            x2 = minx + (i + 1) * width
            y2 = miny + (j + 1) * height

            square_geom = {
                "type": "Polygon",
                "coordinates": [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]],
            }
            squares.append(geojson.Feature(geometry=square_geom))

    return geojson.FeatureCollection(features=squares)


@pytest.fixture(scope="session")
def extract_json():
    """Dummy data extract GeoJSON."""
    # # Get the extract geojson
    # import requests
    # import json
    # query = {
    #     "filters": {
    #         "tags": {
    #             "all_geometry": {
    #                 "join_or": {"building": [], "highway": [], "waterway": []}
    #             }
    #         }
    #     }
    # }
    # path = Path(__file__).parent / "testdata" / "kathmandu.geojson"
    # jsonfile = open(path, "r")
    # json_boundary = geojson.load(jsonfile)
    # query["geometry"] = json_boundary.get("features", None)[0].get("geometry")
    # query["fileName"] = "extract"
    # query["outputType"] = "geojson"
    # print(query)
    # query_url = f"https://api-prod.raw-data.hotosm.org/v1/snapshot/"
    # headers = {"accept": "application/json", "Content-Type": "application/json"}
    # result = requests.post(query_url, data=json.dumps(query), headers=headers)
    # print(result.status_code)
    # print(result)
    # task_id = result.json()["task_id"]
    # print(task_id)
    path = Path(__file__).parent / "testdata" / "kathmandu_extract.geojson"
    with open(path) as jsonfile:
        return geojson.load(jsonfile)


@pytest.fixture(scope="session")
def output_json():
    """Processed JSON using Field-TM algo on dummy AOI."""
    path = Path(__file__).parent / "testdata" / "kathmandu_processed.geojson"
    with open(path) as jsonfile:
        return geojson.load(jsonfile)
