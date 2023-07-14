 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

This script splits an Area of Interest into task polygons based on OpenStreetMap lines (roads, waterways, and railways) for the purposes of adding information (tags) to road segments.
*/

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
  SELECT ST_Union(ml.geom, mp.geom) as geom
  FROM roadlines ml, roadpolystolines mp
);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX roadsdissolved_idx
  ON 
  USING GIST (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
VACUUM ANALYZE roadsdissolved;

/*
--**************************Count features in polygons*****************
DROP TABLE IF EXISTS splitpolygons;
CREATE TABLE splitpolygons AS (
  WITH polygonsfeaturecount AS (
    SELECT sp.polyid,
           sp.geom,
	   sp.geog,
           count(b.geom) AS numfeatures,
	   ST_Area(sp.geog) AS area
    FROM polygonsnocount sp
    LEFT JOIN "buildings" b
    ON sp.polyid = b.polyid
    GROUP BY sp.polyid, sp.geom
  )
  SELECT * from polygonsfeaturecount
);
ALTER TABLE splitpolygons ADD PRIMARY KEY(polyid);
SELECT Populate_Geometry_Columns('public.splitpolygons'::regclass);
CREATE INDEX splitpolygons_idx
  ON splitpolygons
  USING GIST (geom);
VACUUM ANALYZE splitpolygons;

DROP TABLE polygonsnocount;

DROP TABLE IF EXISTS lowfeaturecountpolygons;
CREATE TABLE lowfeaturecountpolygons AS (
  -- Grab the polygons with fewer than the requisite number of features
  WITH lowfeaturecountpolys as (
    SELECT *
    FROM splitpolygons AS p
    -- TODO: feature count should not be hard-coded
    WHERE p.numfeatures < 20  
  ), 
  -- Find the neighbors of the low-feature-count polygons
  -- Store their ids as n_polyid, numfeatures as n_numfeatures, etc
  allneighborlist AS (
    SELECT p.*, 
      pf.polyid AS n_polyid,
      pf.area AS n_area, 
      p.numfeatures AS n_numfeatures,
      -- length of shared boundary to make nice merge decisions 
      st_length2d(st_intersection(p.geom, pf.geom)) as sharedbound
    FROM lowfeaturecountpolys AS p 
    INNER JOIN splitpolygons AS pf 
    -- Anything that touches
    ON st_touches(p.geom, pf.geom) 
    -- But eliminate those whose intersection is a point, because
    -- polygons that only touch at a corner shouldn't be merged
    AND st_geometrytype(st_intersection(p.geom, pf.geom)) != 'ST_Point'
    -- Sort first by polyid of the low-feature-count polygons
    -- Then by descending featurecount and area of the 
    -- high-feature-count neighbors (area is in case of equal 
    -- featurecounts, we'll just pick the biggest to add to)
    ORDER BY p.polyid, p.numfeatures DESC, pf.area DESC
    -- OR, maybe for more aesthetic merges:
    -- order by p.polyid, sharedbound desc
  )
  SELECT DISTINCT ON (a.polyid) * FROM allneighborlist AS a
);  
ALTER TABLE lowfeaturecountpolygons ADD PRIMARY KEY(polyid);
SELECT Populate_Geometry_Columns('public.lowfeaturecountpolygons'::regclass);
CREATE INDEX lowfeaturecountpolygons_idx
  ON lowfeaturecountpolygons
  USING GIST (geom);
VACUUM ANALYZE lowfeaturecountpolygons;

--****************Merge low feature count polygons with neighbors*******



--****************Cluster buildings*************************************
DROP TABLE IF EXISTS clusteredbuildings;
CREATE TABLE clusteredbuildings AS (
  WITH splitpolygonswithcontents AS (
    SELECT *
    FROM splitpolygons sp
    WHERE sp.numfeatures > 0
  )
  -- Add the count of features in the splitpolygon each building belongs to
  -- to the buildings table; sets us up to be able to run the clustering.
  ,buildingswithcount AS (
    SELECT b.*, p.numfeatures
    FROM buildings b 
    LEFT JOIN splitpolygons p
    ON b.polyid = p.polyid
  )
  -- Cluster the buildings within each splitpolygon. The second term in the
  -- call to the ST_ClusterKMeans function is the number of clusters to create,
  -- so we're dividing the number of features by a constant (10 in this case)
  -- to get the number of clusters required to get close to the right number
  -- of features per cluster.
  -- TODO: This should certainly not be a hardcoded, the number of features
  --       per cluster should come from a project configuration table
  ,buildingstocluster as (
    SELECT * FROM buildingswithcount bc
    WHERE bc.numfeatures > 0
  )
  ,clusteredbuildingsnocombineduid AS (
  SELECT *,
    ST_ClusterKMeans(geom, cast((b.numfeatures / 20) + 1 as integer))
    over (partition by polyid) as cid
  FROM buildingstocluster b
  )
  -- uid combining the id of the outer splitpolygon and inner cluster
  ,clusteredbuildings as (
    select *, 
    polyid::text || '-' || cid as clusteruid
    from clusteredbuildingsnocombineduid
  )
  SELECT * FROM clusteredbuildings
);  
ALTER TABLE clusteredbuildings ADD PRIMARY KEY(osm_id);
SELECT Populate_Geometry_Columns('public.clusteredbuildings'::regclass);
CREATE INDEX clusteredbuildings_idx
  ON clusteredbuildings
  USING GIST (geom);
VACUUM ANALYZE clusteredbuildings;

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
