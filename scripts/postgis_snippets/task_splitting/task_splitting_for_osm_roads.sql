 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

This script splits an Area of Interest into task polygons based on OpenStreetMap lines (roads, waterways, and railways) for the purposes of adding information (tags) to road segments.
*/
/*
--*************************Extract road segments***********************
-- Nuke whatever was there before
DROP TABLE IF EXISTS roadsdissolved;
-- Create a new polygon layer of splits by lines
CREATE TABLE roadsdissolved AS (
  -- The Area of Interest provided by the person creating the project
    WITH aoi AS (
    SELECT * FROM "project-aoi"
  )
  -- Grab all roads within the AOI
  ,roadlines AS (
    SELECT ST_Collect(l.geom) AS geom
    FROM aoi a, "ways_line" l
    WHERE ST_Intersects(a.geom, l.geom)
    AND tags->>'highway' IS NOT NULL
  )
  -- Grab the roads that are polygons in OSM ("Closed ways" with highway tags)
  ,roadpolystolines AS (
    SELECT ST_Collect(ST_Boundary(p.geom)) AS geom
    FROM aoi a, "ways_poly" p
    WHERE ST_Intersects(a.geom, p.geom)
    AND tags->>'highway' IS NOT NULL
  )
  -- Merge the roads from lines with the roads from polys
  ,merged AS (
    SELECT ST_Union(ml.geom, mp.geom) as geom
    FROM roadlines ml, roadpolystolines mp
  )
  SELECT *
  FROM merged mr
);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX roadsdissolved_idx
  ON roadsdissolved
  USING GIST (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
VACUUM ANALYZE roadsdissolved;

--**************************MISSING BIT********************************
-- Here we use QGIS multipart to singleparts, which splits the roads
-- on all intersections into sensible parts. Need to implement in PostGIS.
-- Output here is a line layer table called roadparts which consists of one
-- linestring for each portion of a road between any and all intersections.

-- *****************Re-associate parts with OSM ID and tags*************
*/

DROP TABLE IF EXISTS roadpartstagged;
CREATE TABLE roadpartstagged AS (
  SELECT 
    wl.osm_id, 
    wl.tags, 
    l.geom as geom 
  FROM "ways_line" wl, roadparts l
  -- Funky hack here: checking if a roadpart is a subset of an OSM way is
  -- terribly slow if you check for a line intersection, but if you check for
  -- any intersection it'll often return the attributes of an intersecting road.
  -- If you check for intersection with the start and end nodes, sometimes
  -- cresecent roads (which touch another road at start and end) get the
  -- attributes from the road that they touch.
  -- So we check for intersection of the first and second nodes in the part
  -- (if there are only two, they're the start and end by definition, but they
  -- also can't be a crescent so that's ok). 
  WHERE st_intersects(st_startpoint(l.geom), wl.geom) 
  AND ST_Intersects(st_pointn(l.geom, 2), wl.geom)
);
CREATE INDEX roadpartstagged_idx
  ON roadpartstagged
  USING GIST (geom);
VACUUM ANALYZE roadpartstagged;

--****************Cluster roadparts*************************************
DROP TABLE IF EXISTS clusteredroadparts;
CREATE TABLE clusteredroadparts AS (
  SELECT *,
    -- TODO: replace 4500 with count of roadparts
    ST_ClusterKMeans(geom, cast((4500 / 20) + 1 as integer))
    over () as cid
  FROM roadpartstagged rp
);  
CREATE INDEX clusteredroadparts_idx
  ON clusteredroadparts
  USING GIST (geom);
VACUUM ANALYZE clusteredroadparts;

/*
--*****************Densify dumped building nodes******************
DROP TABLE IF EXISTS dumpedpoints;
CREATE TABLE dumpedpoints AS (
  SELECT cb.osm_id, cb.polyid, cb.cid, cb.clusteruid,
  -- POSSIBLE BUG: PostGIS' Voronoi implementation seems to panic
  -- with segments less than 0.00004 degrees.
  -- Should probably use geography instead of geometry
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

*/
