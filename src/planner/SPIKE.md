<!-- markdownlint-disable MD013 -->

# PGlite + PostGIS spike

**Result: go.** `@electric-sql/pglite` 0.5.10 + `@electric-sql/pglite-postgis`
0.2.10 (PostGIS 3.6.2, GEOS 3.14) run the backend's splitting SQL unchanged,
in Node and in the browser (Web Worker).

## What runs

| Algorithm                   | SQL                                                      | Status                        |
| --------------------------- | -------------------------------------------------------- | ----------------------------- |
| Square grid                 | small TS port of `splitBySquare`                         | works                         |
| Split by roads              | `common/1-linear-features.sql` + `split_by_roads.sql`    | works, unchanged              |
| Average buildings (Voronoi) | `common/1..3`, `avg_building_voronoi.sql`, `common/5..6` | works, unchanged              |
| Straight skeleton           | needs SFCGAL                                             | not available, skipped for v1 |

PL/pgSQL `DO` blocks, `ST_ClusterKMeans`, `ST_VoronoiPolygons`,
`current_setting('area_splitter.*')` and `%(param)s` substitution all behave as
on the server.

## Timings (Node 24, one thread; `tests/spike.test.ts`)

| Input                               | Step                  | Time   | Result                       |
| ----------------------------------- | --------------------- | ------ | ---------------------------- |
| —                                   | PGlite + PostGIS init | 7.5 s  |                              |
| Kathmandu test data (667 buildings) | grid 50 m             | 0.4 s  | 70 tasks                     |
|                                     | roads                 | 0.1 s  | 1 task (only short footways) |
|                                     | Voronoi, 5/task       | 1.4 s  | 80 tasks                     |
|                                     | Voronoi, 100/task     | 1.0 s  | 6 tasks                      |
| Synthetic 10k buildings, 6 roads    | grid 50 m             | 0.7 s  | 1681 tasks                   |
|                                     | roads                 | 0.6 s  | 16 tasks                     |
|                                     | Voronoi, 5/task       | 12.4 s | 1752 tasks                   |
|                                     | Voronoi, 100/task     | 11.3 s | 94 tasks                     |

In headless Chromium the first Kathmandu Voronoi split took ~10 s including
engine download and init; later splits reuse the worker.

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
