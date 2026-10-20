# Split by Roads

`SPLIT_BY_ROADS`. Uses [step 1](../pipeline.md#step-1-split-the-aoi-by-linear-features)
of the pipeline directly.

SQL: `algorithms/split_by_roads.sql`.

## Idea

For street-level surveys, use road-bounded polygons as tasks without
clustering buildings. The output comes directly from
`common/1-linear-features.sql`.

## Steps

1. `common/1-linear-features.sql`: same as for the building-based
   algorithms - union roads, rivers, railways, aeroways and
   non-traversable barriers with the AOI boundary, then
   `ST_Polygonize` to get `polygonsnocount`, one polygon per
   road-enclosed area. Falls back to the whole AOI as a single polygon
   if no linear features intersect it.

2. `split_by_roads.sql`: return `polygonsnocount` directly as a
   GeoJSON `FeatureCollection`, with `building_count` computed against
   `ways_poly` for informational purposes only (it plays no part in
   how the polygons are drawn).

## Tradeoffs

- Task size follows the street layout and cannot be controlled.
- Runs on standard PostGIS without SFCGAL.

Prefer one of the [Voronoi](voronoi.md) or
[straight skeleton](straight-skeleton.md) algorithms when the goal is
even building coverage rather than street coverage.
