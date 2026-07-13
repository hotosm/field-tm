# Area Splitter

<!-- markdownlint-disable -->
<p align="center">
  <img src="https://raw.githubusercontent.com/hotosm/field-tm/main/docs/images/hot_logo.png" style="width: 200px;" alt="HOT"></a>
</p>
<p align="center">
  <em>A utility for splitting an AOI into multiple tasks.</em>
</p>
<p align="center">
  <a href="https://pypi.org/project/area-splitter" target="_blank">
      <img src="https://img.shields.io/pypi/v/area-splitter?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/area-splitter" target="_blank">
      <img src="https://img.shields.io/pypi/dm/area-splitter.svg" alt="Downloads">
  </a>
  <a href="https://github.com/hotosm/field-tm/blob/main/src/backend/packages/area-splitter/LICENSE.md" target="_blank">
      <img src="https://img.shields.io/badge/license-GPL%203.0-orange.svg" alt="License">
  </a>
</p>

---

📖 **Documentation**: <a href="https://hotosm.github.io/area-splitter/" target="_blank">https://hotosm.github.io/area-splitter/</a>

🖥️ **Source Code**: <a href="https://github.com/hotosm/field-tm/blob/main/src/backend/packages/area-splitter" target="_blank">https://github.com/hotosm/field-tm/blob/main/src/backend/packages/area-splitter</a>

---

<!-- markdownlint-enable -->

This is a program to split polygons into tasks using a variety of
algorithms. It is a class that can be used by other projects, but also
a standalone program. It was originally developed for the
[Field-TM](https://github.com/hotosm/field-tm/wiki) project, but then
converted so it can be used by multiple projects.

The class takes GeoJson Polygon as an input, and returns a GeoJson
file Multipolygon of all the task boundaries.

## Installation

```bash
pip install area-splitter
```

> Note Postgis should have SFCGAL enabled:
>
> ```sql
> CREATE EXTENSION IF NOT EXISTS postgis_sfcgal WITH SCHEMA public;
> ```

## Splitting Options

Five algorithms are available via the `SplittingAlgorithm` enum:

- `NO_SPLITTING`: return the AOI as one task.
- `DIVIDE_BY_SQUARE`: grid of squares clipped to the AOI (default
  50m). No OSM data required.
- `AVG_BUILDING_VORONOI` (v1): split along roads/rivers/etc, cluster
  buildings, enclose with Voronoi. Kept for compatibility.
- `AVG_BUILDING_SKELETON` (v2, default): same as v1 but uses
  `CG_StraightSkeleton` for cleaner task edges. Needs SFCGAL.
- `TOTAL_TASKS`: same SQL as v2, but sized by target task count
  instead of buildings per task.

The three SQL-based algorithms share a six-step pipeline. See
[docs/pipeline.md](docs/pipeline.md) for the full walkthrough, and
[docs/algorithms/](docs/algorithms/) for what makes each one
different.

For a user-facing overview (which one to pick for a project), see
the [Task Splitting manual](../../../docs/manuals/task-splitting.md).

## Usage In Code

- Either the AreaSplitter class can be used directly, or the wrapper/
  helper functions can be used for splitting.

By square:

```python
import json
from area_splitter.splitter import split_by_square

aoi = json.load("/path/to/file.geojson")

split_features = split_by_square(
    aoi,
    meters=100,
)
```

The Field-TM splitter algorithm:

```python
import json
from area_splitter.splitter import split_by_sql

aoi = json.load("/path/to/file.geojson")
osm_extracts = json.load("/path/to/file.geojson")
db = "postgresql://postgres:postgres@localhost/postgres"

split_features = split_by_sql(
    aoi,
    db,
    num_buildings=50,
    osm_extract=osm_extracts,
)
```

### Database Connections

- The db parameter can be a connection string to start a new connection.
- Or an existing database connection can be reused.
- To do this, either the psycopg connection, or a DBAPI connection string
  must be passed:

psycopg example:

```python
import psycopg
from area_splitter.splitter import split_by_sql

db = psycopg.connect("postgresql://postgres:postgres@localhost/postgres")

split_features = split_by_sql(
    aoi,
    db,
    num_buildings=50,
    osm_extract=osm_extracts,
)
```

## Usage Via CLI

Options:

```bash
-h, --help                       show this help message and exit
-v, --verbose                    verbose output
-o OUTFILE, --outfile OUTFILE    Output file from splitting
-m METERS, --meters METERS       Size in meters if using square splitting
-b BOUNDARY, --boundary BOUNDARY Polygon AOI
-s SOURCE, --source SOURCE       Source data, Geojson or PG:[dbname]
-c CUSTOM, --custom CUSTOM       Custom SQL query for database
```

This program splits a Polygon (the Area Of Interest)
The data source for existing data can'be either the data extract
used by the XLSForm, or a postgresql database.

Examples:

```bash
area-splitter -b AOI
area-splitter -v -b AOI -s data.geojson
area-splitter -v -b AOI -s PG:colorado

# Where AOI is the boundary of the project as a polygon
# And OUTFILE is a MultiPolygon output file,which defaults to field-tm.geojson
# The task splitting defaults to squares, 50 meters across
```
