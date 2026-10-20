<!-- markdownlint-disable MD013 -->

# PGlite + PostGIS spike

**Result: go.** `@electric-sql/pglite` 0.5.10 + `@electric-sql/pglite-postgis`
0.2.10 (PostGIS 3.6.2, GEOS 3.14) run the backend's splitting SQL unchanged,
in Node and in the browser (Web Worker).

## What runs

| Algorithm                   | SQL                                                      | Status                                         |
| --------------------------- | -------------------------------------------------------- | ---------------------------------------------- |
| Square grid                 | small TS port of `splitBySquare`                         | works                                          |
| Split by roads              | `common/1-linear-features.sql` + `split_by_roads.sql`    | works, unchanged                               |
| Average buildings (Voronoi) | `common/1..3`, `avg_building_voronoi.sql`, `common/5..6` | works, unchanged                               |
| Straight skeleton           | `common/1..3`, skeleton SQL in two passes, `common/5..6` | works, `CG_StraightSkeleton` in JS (see below) |

PL/pgSQL `DO` blocks, `ST_ClusterKMeans`, `ST_VoronoiPolygons`,
`current_setting('area_splitter.*')` and `%(param)s` substitution all behave as
on the server.

## Timings (Node 24, one thread; `tests/spike.test.ts`)

| Input                               | Step                  | Time   | Result                       |
| ----------------------------------- | --------------------- | ------ | ---------------------------- |
| -                                   | PGlite + PostGIS init | 7.5 s  |                              |
| Kathmandu test data (667 buildings) | grid 50 m             | 0.4 s  | 70 tasks                     |
|                                     | roads                 | 0.1 s  | 1 task (only short footways) |
|                                     | Voronoi, 5/task       | 1.4 s  | 80 tasks                     |
|                                     | Voronoi, 100/task     | 1.0 s  | 6 tasks                      |
| Synthetic 10k buildings, 6 roads    | grid 50 m             | 0.7 s  | 1681 tasks                   |
|                                     | roads                 | 0.6 s  | 16 tasks                     |
|                                     | Voronoi, 5/task       | 12.4 s | 1752 tasks                   |
|                                     | Voronoi, 100/task     | 11.3 s | 94 tasks                     |
| Kathmandu                           | skeleton, 5/task      | 30 s   | 110 tasks                    |
|                                     | skeleton, 10/task     | 15 s   | 56 tasks                     |
|                                     | skeleton, 100/task    | 2.5 s  | 6 tasks                      |
| Synthetic 2k buildings              | skeleton, 20/task     | 31 s   | 92 tasks                     |
|                                     | skeleton, 100/task    | 6.8 s  | 28 tasks                     |
| Synthetic 5k buildings              | skeleton, 100/task    | 19 s   | 59 tasks                     |
|                                     | skeleton, 20/task     | 187 s  | 220 tasks                    |

In headless Chromium the first Kathmandu Voronoi split took ~10 s including
engine download and init; later splits reuse the worker.

## Straight skeleton

PGlite's PostGIS has no SFCGAL. `straight-skeleton` 3.0.0 (MIT; CGAL's
Straight_skeleton_2 compiled to wasm, GPL-3.0-or-later, ~1 MB JS with inline
wasm) replaces `CG_StraightSkeleton`. `sql.ts` cuts the backend SQL at the
`aoi_minus_hulls` CTE, JS computes the skeleton of those polygons, and the
rest of the SQL reads the lines from a temp table. Notes:

- Almost all the time is CGAL, and it grows faster than linearly with the
  number of clusters (holes in the polygon), i.e. buildings / buildings per
  task. Limited to 5000 buildings, as in the backend's simple flow, and to
  about 250 tasks.
- CGAL returned no result for Kathmandu at 5/task until the rings were
  simplified by 1e-7° (~1 cm); a 1e-6° retry follows.
- PGlite's GEOS hung forever on the `clipped_hulls` union (Kathmandu,
  100/task); a 1e-9° grid size on that one `ST_Union` fixes it. The client
  also stops the worker after 10 minutes.
- Results meet the backend's expectations: ≥ 60 tasks at 5/task (110), all
  buildings counted, tasks valid and non-overlapping, < 2 % outside the AOI.

## Comparison with the server

Not run side by side (no server PostGIS in the spike environment). Results
match the backend test expectations for the same fixtures: Voronoi with 5
buildings/task gives ≥ 60 tasks (80); grid 50 m gives 65 non-empty cells
(server drops empty cells and asserts 66; the planner keeps empty cells so the
grid covers the whole area). Next step: run `tests/testdata` through both in CI.

## Costs

- First split downloads ~36 MB (pglite.wasm 10.5 MB, 3.7 MB gzipped;
  pglite.data 6.2 MB; postgis.tar.gz 19.5 MB). Lazy-loaded, then browser-cached.
- Main app bundle ~1.4 MB (375 kB gzipped), mostly MapLibre.
- PostGIS wasm is GPL-2.0-or-later; fine for this AGPL project.
