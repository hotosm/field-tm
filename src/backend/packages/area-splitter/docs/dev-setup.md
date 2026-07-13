# Dev Setup

Notes for working on the algorithms locally, outside the Field-TM
stack.

## Running bleeding-edge PostGIS

`AVG_BUILDING_SKELETON` needs SFCGAL for `CG_StraightSkeleton`, and
that has historically needed a recent PostGIS build. Easiest way to
get one:

```bash
docker run --name area-splitter-db --detach \
  -p 5432:5432 -v ./db_data:/var/lib/postgresql/data/  \
  -e POSTGRES_USER=hotosm \
  -e POSTGRES_PASSWORD=hotosm \
  -e POSTGRES_DB=splitter \
  docker.io/postgis/postgis:17-master \
&& sleep 5 \
&& docker exec area-splitter-db psql -d splitter -U hotosm -c \
  'CREATE EXTENSION IF NOT EXISTS postgis_sfcgal WITH SCHEMA public;'
```

Connection: `postgresql://hotosm:hotosm@localhost:5432/splitter`.

## Importing OSM data for testing

Get the raw-data-api Lua import script:

```bash
curl -LO https://raw.githubusercontent.com/hotosm/osm-rawdata/refs/heads/main/osm_rawdata/import/raw.lua
```

Grab a PBF from <https://download.geofabrik.de> for the area you
want to test, then import it:

```bash
osm2pgsql --create -H localhost -U hotosm -P 5432 -d splitter \
  -W --extra-attributes --output=flex --style ./raw.lua \
  ./your-region.osm.pbf
```

## Stepping through the SQL in QGIS

Install the QGIS DB Manager plugin and connect to the container.
The pipeline SQL files are in `area_splitter/algorithms/`, in
numbered order. Running them one at a time lets you view the
intermediate tables (`polygonsnocount`, `splitpolygons`,
`clusteredbuildings`, `taskpolygons`) on the map as you go.

Before running the SQL you need to seed the two GUCs and the input
tables. The easiest way is to run the Python splitter once with
logging on, dump the tables, and inspect from there. Or set the GUCs
by hand:

```sql
SET area_splitter.num_buildings = 50;
SET area_splitter.num_enumerators = 0;
```

## Running the test suite

```bash
cd src/backend/packages/area-splitter
uv sync
uv run pytest
```

Tests use a real Postgres (see `tests/conftest.py`), not a mock.
