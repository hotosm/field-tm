# Straight Skeleton (v2, default)

`AVG_BUILDING_SKELETON` and `TOTAL_TASKS`. Step 4 of the
[pipeline](../pipeline.md).

SQL: `algorithms/avg_building_straight_skeleton.sql`.

## Idea

A straight skeleton is the set of lines you get by shrinking a
polygon's edges inward at equal speed until they meet. Run over the
empty space between building clusters, it produces clean bisector
polygons that respect the shape of the clusters (unlike Voronoi,
which only respects distance to points).

Running the skeleton over every individual building is slow. So we
first bundle each cluster into a convex hull and run the skeleton
over the space between hulls. This is roughly 7x faster than running
it over raw buildings.

Requires PostGIS with SFCGAL enabled (`postgis_sfcgal`), because
`CG_StraightSkeleton` lives in SFCGAL.

## Steps

1. `convex_hulls`: one convex hull per cluster, plus a
   `buildings_union` of the raw buildings in that cluster (needed
   later for clipped buildings).

2. `intersections_union`: hulls of neighbouring clusters can
   overlap. Compute the pairwise intersections, buffer each by 1% of
   the hull's max diagonal so touching-only intersections become
   real regions, and group by cluster.

3. `clipped_hulls`: subtract the intersection region from each hull,
   then union with the original `buildings_union` to restore any
   buildings that got clipped away. A cluster whose hull was
   entirely inside another's intersection can end up as a
   MultiPolygon here.

4. `final_hulls`: `ST_Dump` the MultiPolygons into simple polygons.

5. `touching_regions` + `final_hulls_untouched`: even after step 3
   two hulls can share an edge or vertex, which
   `CG_StraightSkeleton` cannot handle. Clip a very thin region
   (0.0000005 buffer) off each hull to break the touch.

6. `aoi_minus_hulls`: `ST_Difference` the AOI against the union of
   all final hulls. This is the empty space we want to fill.

7. `skeleton_polygons`: run `CG_StraightSkeleton` on the empty
   space, unioned with the AOI boundary so hulls at the AOI edge
   get closed off. `ST_Polygonize` on the resulting lines produces
   one polygon per hull. Grid-snap with `ST_UnaryUnion(geom,
0.0000001)` before polygonizing to close tiny gaps at vertices.

8. `skeleton_clusters`: match each skeleton polygon to a cluster by
   checking which hull centroid falls inside it. Centroid rather
   than `ST_Within` because the grid snap can push hull edges
   slightly outside the polygon.

9. `taskpolygons`: `ST_Union` each cluster's hull with its skeleton
   polygon. Any buildings that got clipped out entirely in step 3
   are picked up here because the skeleton drew a polygon around
   them, and that polygon lands in the same cluster.

## Notes

- The 1% buffer in step 2 is a knob. Too small and touching
  vertices remain, too large and hulls lose useful area.
- `ST_UnaryUnion(..., 0.0000001)` in step 7 snaps to a grid roughly
  1cm at the equator. Line segments finer than this get merged.
- The one-to-one mapping between hulls and skeleton polygons is
  guaranteed by construction: each hull sits in exactly one
  connected component of the empty space.

## Why this is the default

- Cleaner task boundaries than Voronoi, no staircase edges.
- Respects cluster shape rather than just distance to points.
- Faster than running the skeleton over raw buildings.

The tradeoff is the SFCGAL dependency. Field-TM's Docker image ships
SFCGAL, so this is transparent for the hosted product but matters
if you self-host or reuse the package elsewhere.
