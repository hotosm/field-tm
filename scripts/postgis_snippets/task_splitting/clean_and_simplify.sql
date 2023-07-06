/*
Task polygons made by creating and merging Voronoi polygons have lots of jagged edges. Simplifying them makes them both nicer to look at, and easier to render on a map. 

At the moment the algorithm is working, except that the 
*/

-- convert task polygon boundaries to linestrings
with rawlines as (
   select tp.clusteruid, st_boundary(tp.geom) as geom
   from taskpolygons as tp 
)
-- Union, which eliminates duplicates from adjacent polygon boundaries
,unionlines as (
  select st_union(l.geom) as geom from rawlines l
)
-- Dump, which gives unique segments.
,dumpedlinesegments as (
  select (st_dump(l.geom)).geom as geom
  from unionlines l 
)
-- TODO: this step using st_union, st_unaryunion, st_collect, st_node,
-- and maybe a few others I've tried to dissolve the line segments
-- appears to work, but the resulting multiline geometry fails to simplify.
-- On the other hand, the QGIS Dissolve tool works, and produces multiline
-- geometry that simplifies nicely.
-- QGIS Multipart to Singleparts does something arguably even better: it
-- unions all of the segments between intersections.
,dissolved as (
  select st_collect(l.geom) as geom from dumpedlinesegments l
)
-- Cheating by loading an external layer because QGIS dissolve works.
-- I'm loading the dumpedlinesegements to the QGIS canvas, dissolving them,
-- and pulling that layer back into the DB as dissolvedfromdumpedlinesegments,
-- which st_simplify appears happy with.
,simplified as (
  select st_simplify(l.geom, 0.000075) 
  as geom from dissolvedfromdumpedlinesegements l -- import from QGIS
)
-- Rehydrate the task areas after simplification
select (st_dump(st_polygonize(s.geom))).geom as geom from simplified s
