# Split by Roads

`SPLIT_BY_ROADS`. Uses [step 1](../pipeline.md#step-1-split-the-aoi-by-linear-features)
of the pipeline directly.

SQL: `algorithms/split_by_roads.sql`.

## Idea

Some projects collect street-level data (imagery, road condition
surveys) rather than per-building data. Mappers walk or cycle roads,
so task boundaries should follow the street layout, not building
density. There's no need to cluster buildings or run Voronoi/Straight
Skeleton at all — the road-bounded polygons that
`common/1-linear-features.sql` already produces as an intermediate
step are the final output.

## Steps

1. `common/1-linear-features.sql`: same as for the building-based
   algorithms — union roads, rivers, railways, aeroways and
   non-traversable barriers with the AOI boundary, then
   `ST_Polygonize` to get `polygonsnocount`, one polygon per
   road-enclosed area. Falls back to the whole AOI as a single polygon
   if no linear features intersect it.

2. `split_by_roads.sql`: return `polygonsnocount` directly as a
   GeoJSON `FeatureCollection`, with `building_count` computed against
   `ways_poly` for informational purposes only (it plays no part in
   how the polygons are drawn).

## Downsides

- No control over task size — a polygon between two motorway
  junctions can be much larger or smaller than one between two
  residential streets.
- No SFCGAL dependency; runs on any PostGIS install with the standard
  extensions.

Prefer one of the [Voronoi](voronoi.md) or
[straight skeleton](straight-skeleton.md) algorithms when the goal is
even building coverage rather than street coverage.
