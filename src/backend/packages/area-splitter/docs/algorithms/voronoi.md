# Voronoi (v1)

`AVG_BUILDING_VORONOI`. Step 4 of the [pipeline](../pipeline.md).

SQL: `algorithms/avg_building_voronoi.sql`.

## Idea

A Voronoi diagram divides a plane into regions, one per input point,
where every location in a region is closer to that region's point
than to any other. If we drop points along the outlines of the
clustered buildings and run Voronoi over them, the region boundaries
form a natural bisector between neighbouring clusters.

Since PostGIS Voronoi works on points, not polygons, the buildings
have to be dumped into points first.

## Steps

1. `dumpedpoints`: densify each building outline with
   `ST_Segmentize(geom, 0.00004)`, then `ST_DumpPoints` to convert
   the outlines into a point cloud. The 0.00004 degree limit works
   around a PostGIS bug where Voronoi panics on very short segments.

2. `voronoids`: run `ST_VoronoiPolygons` on the collected points,
   grouped by the containing step-1 polygon, then intersect with
   that polygon to clip to the local area.

3. `voronois`: attach each Voronoi cell back to the `clusteruid` of
   the building point that produced it.

4. `unsimplifiedtaskpolygons`: `ST_Union` the cells per
   `clusteruid`. This gives one polygon per cluster.

5. `taskpolygons`: extract the boundary linestrings, union to
   deduplicate shared edges, simplify with tolerance `0.000075`, and
   `ST_Polygonize` back into polygons. This removes the jagged
   staircase edges left by the point-based Voronoi.

## Downsides

- Voronoi over points produces wavy or staircase edges between
  clusters, especially where clusters interleave. The simplify pass
  helps but doesn't fully fix it.
- The 0.00004 degree segment limit is a workaround, not a fix. On
  small or very dense clusters it can leave gaps.
- No SFCGAL dependency, so it will run on any PostGIS install with
  the standard extensions.

Prefer the [straight skeleton](straight-skeleton.md) algorithm
unless you specifically need Voronoi output.
