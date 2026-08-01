# The Splitting Pipeline

The SQL-based algorithms (`AVG_BUILDING_VORONOI`,
`AVG_BUILDING_SKELETON`, `TOTAL_TASKS`) share the same six-step
pipeline. Steps 1-3, 5, and 6 are identical. Step 4 is the algorithm
itself and swaps between Voronoi and Straight Skeleton.

SQL files live in `area_splitter/algorithms/`:

```text
common/
  1-linear-features.sql
  2-group-buildings.sql
  3-cluster-buildings.sql
  5-alignment.sql
  6-extract.sql
avg_building_voronoi.sql             # step 4, v1
avg_building_straight_skeleton.sql   # step 4, v2 (default)
```

`splitter.py::_run_split_sql_files` runs them in order.

## Inputs

Before the pipeline starts, `splitter.py` loads:

- The AOI polygon into `project_aoi`.
- The OSM extract into `ways_poly` (building polygons) and
  `ways_line` (roads, rivers, railways, aeroways, and non-traversable
  barriers). See `_insert_split_sql_extract` for the tag filter.

Two settings are passed through as PostgreSQL GUCs:

- `area_splitter.num_buildings`: target buildings per task.
- `area_splitter.num_enumerators`: target task count.

Exactly one is set to a non-zero value depending on the chosen
algorithm.

## Step 1: Split the AOI by linear features

`common/1-linear-features.sql`.

Polygonises the linear features intersecting the AOI and clips them
to the AOI. Small polygons or polygons with too few buildings get
merged into neighbours.

Output: a set of polygons covering the AOI, bounded by roads and
rivers.

## Step 2: Group buildings by polygon

`common/2-group-buildings.sql`.

For each building, finds which step-1 polygon contains its centroid.
Records the building count and polygon area in `splitpolygons`.

Output: buildings tagged with their containing polygon ID, plus
per-polygon counts.

## Step 3: Cluster buildings

`common/3-cluster-buildings.sql`.

For each polygon, runs K-Means to make X clusters where:

```text
X = ceil(numfeatures / features_per_cluster)
features_per_cluster = num_buildings   (v1, v2)
                     = total_buildings / num_enumerators  (TOTAL_TASKS)
```

When `num_enumerators` is set, the SQL then increments or decrements
per-partition task counts until the total matches the requested
count exactly, biased towards partitions with the highest building
density.

Each cluster gets a `clusteruid` of `polygonid-clusterid`, for
example `377-0`, `377-1`, `377-2`.

Output: `clusteredbuildings`, one row per building with its cluster
UID.

## Step 4: Enclose the clusters

This is the pluggable step. See:

- [Voronoi](algorithms/voronoi.md)
- [Straight Skeleton](algorithms/straight-skeleton.md)

Both produce `taskpolygons`: one polygon per cluster, covering the
AOI with no gaps or overlaps.

## Step 5: Alignment

`common/5-alignment.sql`.

Task edges may have drifted off the linear features during step 4.
Re-runs the split logic per cluster to nudge boundaries back onto
roads and rivers.

Output: `taskpolygons` with edges better aligned to the input linear
features.

## Step 6: Extract

`common/6-extract.sql`.

Returns the final task polygons as a GeoJSON FeatureCollection.

## Split by roads

`SPLIT_BY_ROADS` only runs step 1, then its own extract query
(`split_by_roads.sql`) instead of steps 2-6. It returns the
road-bounded polygons from step 1 (`polygonsnocount`) directly, with
no building clustering or edge alignment. See
[docs/algorithms/roads.md](algorithms/roads.md).

## Non-SQL algorithms

`NO_SPLITTING` and `DIVIDE_BY_SQUARE` do not use the pipeline above.

- `NO_SPLITTING` returns the AOI as a single task.
- `DIVIDE_BY_SQUARE` is implemented in `splitter.py::splitBySquare`.
  It builds a lat/lon grid, clips cells to the AOI, and merges cells
  smaller than 35% of the target area into their largest neighbour.
