 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
*/

--*************************Split by OSM lines***********************
-- Nuke whatever was there before
DROP TABLE IF EXISTS polygonsnocount;
-- Create a new polygon layer of splits by lines
CREATE TABLE polygonsnocount AS (
  -- The Area of Interest provided by the person creating the project
  WITH aoi AS (
    SELECT * FROM "project-aoi"
  )
  -- Extract all lines to be used as splitlines from a table of lines
  -- with the schema from Underpass (all tags as jsonb column called 'tags')
  -- TODO: add polygons (closed ways in OSM) with a 'highway' tag;
  -- some features such as roundabouts appear as polygons.
  -- TODO: add waterway polygons; now a beach doesn't show up as a splitline.
  -- TODO: these tags should come from another table rather than hardcoded
  -- so that they're easily configured during project creation.
  ,splitlines AS (
    SELECT ST_Intersection(a.geom, l.geom) AS geom
    FROM aoi a, "ways_line" l
    WHERE ST_Intersects(a.geom, l.geom)
    -- TODO: these tags should come from a config table
    -- All highways, waterways, and railways
    AND (tags->>'highway' IS NOT NULL
      OR tags->>'waterway' IS NOT NULL
      OR tags->>'railway' IS NOT NULL
      )
  )
  -- Merge all lines, necessary so that the polygonize function works later
  ,merged AS (
    SELECT ST_LineMerge(ST_Union(splitlines.geom)) AS geom
    FROM splitlines
  )
  -- Combine the boundary of the AOI with the splitlines
  -- First extract the Area of Interest boundary as a line
  ,boundary AS (
    SELECT ST_Boundary(geom) AS geom
    FROM aoi
  )
  -- Then combine it with the splitlines
  ,comb AS (
    SELECT ST_Union(boundary.geom, merged.geom) AS geom
    FROM boundary, merged
  )
  -- TODO add closed ways from OSM to lines (roundabouts etc)
  -- Create a polygon for each area enclosed by the splitlines
  ,splitpolysnoindex AS (
    SELECT (ST_Dump(ST_Polygonize(comb.geom))).geom as geom
    FROM comb
  )
  -- Add an index column to the split polygons
  ,splitpolygons AS(
    SELECT
      row_number () over () as polyid,
      ST_Transform(spni.geom,4326)::geography AS geog,
      spni.* 
    from splitpolysnoindex spni
  )
  SELECT * FROM splitpolygons
);
-- Make that index column a primary key
ALTER TABLE polygonsnocount ADD PRIMARY KEY(polyid);
-- Properly register geometry column (makes QGIS happy)
SELECT Populate_Geometry_Columns('public.polygonsnocount'::regclass);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX polygonsnocount_idx
  ON polygonsnocount
  USING GIST (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
VACUUM ANALYZE polygonsnocount;

-- ************************Grab the buildings**************************
-- While we're at it, grab the ID of the polygon the buildings fall within.
-- TODO add outer rings of buildings from relations table of OSM export
DROP TABLE IF EXISTS buildings;
CREATE TABLE buildings AS (
  SELECT b.*, polys.polyid 
  FROM "ways_poly" b, polygonsnocount polys
  WHERE ST_Intersects(polys.geom, ST_Centroid(b.geom))
  AND b.tags->>'building' IS NOT NULL
);
ALTER TABLE buildings ADD PRIMARY KEY(osm_id);
-- Properly register geometry column (makes QGIS happy)
SELECT Populate_Geometry_Columns('public.buildings'::regclass);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX buildings_idx
  ON buildings
  USING GIST (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
VACUUM ANALYZE buildings;

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
DROP TABLE IF EXISTS taskpolysegments;
CREATE TABLE taskpolysegments AS (
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
  SELECT (st_dump(l.geom)).geom AS geom
  FROM unionlines l 
);
ALTER TABLE taskpolysegments
  ALTER COLUMN geom
    TYPE geometry(LineString, 4326)
    USING ST_SetSRID(geom, 4326);
CREATE INDEX taskpolysegments_idx
  ON taskpolysegments
  USING GIST (geom);
VACUUM ANALYZE taskpolysegments;

-- Dissolve the segments

-- Simplify

-- Rehydrate back into polygons

-- Clean results (nuke or merge polygons without features in them)

