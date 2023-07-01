/*
Task polygons made by creating and merging Voronoi polygons have lots of jagged edges. Simplifying them makes them both nicer to look at, and easier to render on a map. 

The problem is that the polygons seem not to perfectly tile the plane; there are centimeter-level slivers. So when simplified, the adjacent polygons don't simplify in exactly the same way, creating big visible gaps. 

When the polygons are converted to lines and then to line segments, each line segment seems to have at least one near-exact duplicate; near enough to be visibly indistinguishable, but not precisely equal according to PostGIS when trying to select distinct or otherwise get rid of duplicate geometries.
*/

-- Convert all polygons into boundary lines
with lines as (
  select st_boundary(tp.geom) as geom, 
  row_number () over () as gid
  from taskpolygons as tp
)
-- Break the lines into segments
,segments AS (
  SELECT gid, ST_Astext(ST_MakeLine(lag((pt).geom, 1, NULL) 
  OVER (PARTITION BY gid ORDER BY gid, (pt).path), (pt).geom)) 
  AS geom
  FROM (SELECT gid, ST_DumpPoints(geom) AS pt FROM lines) as dumps
)
-- Select distinct (unique) segments (DOESN'T WORK CORRECTLY)
select distinct on(ST_AsBinary(geom)) geom, geom as geomstring 
from segments 
where geom is not null;

-- If you load up the resulting layer, the individual line segments all seem to have a twin.
