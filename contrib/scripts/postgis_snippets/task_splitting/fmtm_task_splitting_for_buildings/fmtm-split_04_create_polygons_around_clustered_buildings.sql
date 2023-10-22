 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

Inputs:

Outputs:
- Point layer dumpedpoints (building perimeters chopped into small segments and all nodes converted to points)
- Polygon layer voronoids (Voronoi polygons from the building segment points, only geometry without attributes because PostGIS is annoying on that score)
- Polygon layer voronois (the Voronoi polygons from the previous layer, re-associated with the ID of the points they were created from)
- Polygon layer taskpolygons (polygons mostly enclosing each task, made by dissolving the voronois by clusteruid)
- Polygon layer simplifiedpolygons (the polygons from above simplified to make them less jagged, easier to display, and smaller memory footprint)

*/

/*
***************************PARAMETERS FOR ROB**********************
- Line 28: Segment length to chop up the building perimeters. Currently 0.00001 degrees (about a meter near the equator). When there are buildings very close together, this value needs to be small to reduce task polygons poking into buildings from neighboring tasks. When buildings are well-spaced, this value can be bigger to save on performance overhead.
- Line 101: Simplification tolerance. Currently 0.000075 (about 7.5 meters near the equator). The larger this value, the more smoothing of Voronoi jaggies happens, but the more likely task perimeters are to intersect buildings from neighboring tasks.
*/

--*****************Densify dumped building nodes******************
DROP TABLE IF EXISTS dumpedpoints;
CREATE TABLE dumpedpoints AS (
  SELECT cb.osm_id, cb.polyid, cb.cid, cb.clusteruid,
  -- POSSIBLE BUG: PostGIS' Voronoi implementation sometimes panics
  -- with segments less than 0.00004 degrees.
  (st_dumppoints(ST_Segmentize(geom, 0.00001))).geom
  FROM clusteredbuildings cb
);
SELECT Populate_Geometry_Columns('public.dumpedpoints'::regclass);
CREATE INDEX dumpedpoints_idx
  ON dumpedpoints
  USING GIST (geom);
VACUUM ANALYZE dumpedpoints;

--*******************voronoia****************************************
DROP TABLE IF EXISTS voronoids;
CREATE TABLE voronoids AS (
  SELECT
    st_intersection((ST_Dump(ST_VoronoiPolygons(
 		ST_Collect(points.geom)
 		))).geom, 
                sp.geom) as geom
    FROM dumpedpoints as points, 
    splitpolygons as sp
    where st_contains(sp.geom, points.geom)
    group by sp.geom
);
CREATE INDEX voronoids_idx
  ON voronoids
  USING GIST (geom);
VACUUM ANALYZE voronoids;

DROP TABLE IF EXISTS voronois;
CREATE TABLE voronois AS (
  SELECT p.clusteruid, v.geom
  FROM voronoids v, dumpedpoints p
  WHERE st_within(p.geom, v.geom)
);
CREATE INDEX voronois_idx
  ON voronois
  USING GIST (geom);
VACUUM ANALYZE voronois;
DROP TABLE voronoids;

DROP TABLE IF EXISTS taskpolygons;
CREATE TABLE taskpolygons AS (
  SELECT ST_Union(geom) as geom, clusteruid
  FROM voronois
  GROUP BY clusteruid
);
CREATE INDEX taskpolygons_idx
  ON taskpolygons
  USING GIST (geom);
VACUUM ANALYZE taskpolygons;

--*****************************Simplify*******************************
-- Extract unique line segments
DROP TABLE IF EXISTS simplifiedpolygons;
CREATE TABLE simplifiedpolygons AS (
  --Convert task polygon boundaries to linestrings
  WITH rawlines AS (
    SELECT tp.clusteruid, st_boundary(tp.geom) AS geom
    FROM taskpolygons AS tp 
  )
  -- Union, which eliminates duplicates from adjacent polygon boundaries
  ,unionlines AS (
    SELECT st_union(l.geom) AS geom FROM rawlines l
  )
  -- Dump, which gives unique segments.
  ,segments AS (
    SELECT (st_dump(l.geom)).geom AS geom
    FROM unionlines l
  )
  ,agglomerated AS (
    SELECT st_linemerge(st_unaryunion(st_collect(s.geom))) AS geom
    FROM segments s
  )
  ,simplifiedlines AS (
    SELECT st_simplify(a.geom, 0.000075) AS geom
    FROM agglomerated a
  )
  SELECT (st_dump(st_polygonize(s.geom))).geom AS geom
  FROM simplifiedlines s
);
CREATE INDEX simplifiedpolygons_idx
  ON simplifiedpolygons
  USING GIST (geom);
VACUUM ANALYZE simplifiedpolygons;

-- Clean results (nuke or merge polygons without features in them)

