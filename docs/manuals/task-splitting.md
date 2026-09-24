# Task Splitting

When you set up a project, Field-TM cuts the AOI into smaller task
areas. Each task gets assigned to one mapper. Good splits mean less
walking between tasks, no gaps or overlaps, and a roughly even
workload per mapper.

Field-TM has a few options. Pick one when creating a project.

## Options

### No Splitting

Use the whole AOI as one task. Fine for very small areas or solo
mapping.

Needs: AOI polygon.

### Split by Square

Divide the AOI into a grid of squares (50m by default,
configurable). Squares outside the AOI are dropped, edge squares are
clipped to the AOI boundary.

Best when you don't have OSM data for the area, or the area has very
few buildings.

Needs: AOI polygon. Optionally an OSM extract to skip empty cells.

[More details about how this algorithm works](https://github.com/hotosm/field-tm/blob/dev/src/backend/packages/area-splitter/docs/pipeline.md#non-sql-algorithms).

### Average Buildings v1 (Voronoi)

Splits along roads, rivers, railways, aeroways, and non-traversable
barriers (walls, fences, cliffs, embankments). Groups buildings so
each task contains roughly the target number of buildings. Uses a
Voronoi diagram to draw task boundaries.

Older algorithm. Kept for backwards compatibility. Prefer v2 unless
you have a reason not to.

Needs: AOI polygon, OSM extract, target buildings per task.

[More details about how this algorithm works](https://github.com/hotosm/field-tm/blob/dev/src/backend/packages/area-splitter/docs/algorithms/voronoi.md).

### Average Buildings v2 (Straight Skeleton, default)

Same idea as v1 but uses the straight skeleton algorithm to fill the
space between building clusters. Cleaner task edges and less jagged
boundaries.

Best general-purpose option when the area has OSM data.

Needs: AOI polygon, OSM extract, target buildings per task.

[More details about how this algorithm works](https://github.com/hotosm/field-tm/blob/dev/src/backend/packages/area-splitter/docs/algorithms/straight-skeleton.md).

### Split by Specific Number of Tasks

Same pipeline as v2, but you give the total number of tasks (usually
matching your enumerator count) instead of buildings per task.
Field-TM works out the split from the extract.

Needs: AOI polygon, OSM extract, target number of tasks.

[More details about how this algorithm works](https://github.com/hotosm/field-tm/blob/dev/src/backend/packages/area-splitter/docs/algorithms/straight-skeleton.md).

### Split by Roads

Task boundaries are exactly the polygons enclosed by roads, rivers,
railways, aeroways, and non-traversable barriers — no building
clustering. Each task is bounded by the streets around it.

Best for street-level data collection (e.g. imagery capture) where
mappers walk or cycle roads rather than visiting individual buildings.
Task size isn't controllable — it follows however dense the street
network is.

Needs: AOI polygon, OSM extract with roads.

[More details about how this algorithm works](https://github.com/hotosm/field-tm/blob/dev/src/backend/packages/area-splitter/docs/algorithms/roads.md).

## Which one to pick

| Situation                               | Use                      |
| --------------------------------------- | ------------------------ |
| Very small AOI, one mapper              | No Splitting             |
| No OSM data, or a sparse area           | Split by Square          |
| You know how many mappers you have      | Specific Number of Tasks |
| Standard case, building-dense area      | Average Buildings v2     |
| Reproducing an older project            | Average Buildings v1     |
| Street-level mapping (walk/cycle roads) | Split by Roads           |

## What the feature-based options do

- Task boundaries follow roads and rivers where possible, so mappers
  don't cross busy roads or water to reach the next building.
- Buildings inside each task are grouped by proximity, so mappers
  walk shorter distances between them.
- Sparse areas can still end up with large tasks. If a task looks
  too big, reduce the target buildings per task, or split the AOI
  by hand first.

For the algorithm internals, see the
[area-splitter package docs](https://github.com/hotosm/field-tm/tree/dev/src/backend/packages/area-splitter/docs).
