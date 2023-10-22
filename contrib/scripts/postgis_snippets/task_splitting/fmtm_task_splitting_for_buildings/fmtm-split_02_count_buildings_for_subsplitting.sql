 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

Inputs:
- Polygon layer polygonsnocount from previous fmtm-split step
- Polygon layer ways_poly formatted like OSM data from Underpass (tags in jsonb object)

Outputs:
- Polygon layer buildings (OSM buildings with original tags plus the id of the polygon they are found in)
- Polygon layer splitpolygons (the polygons from the previous step, but now with a column with the count of the buildings found within each polygon)
- Polygon layer lowfeaturecountpolygons (All of the polygons with less than a specified number of buildings within them. These are also present in the splitpolygons layer; the idea is to merge them with neighbors, not implemented yet).
*/

/*
**************************PARAMETERS FOR ROB***************************
- Line 70: The number of buildings desired per task (for now determines which polygons get added to the lowfeaturecountpolygons layer).
*/

-- Grab the buildings
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
-- NOT IMPLEMENTED YET; not absolutely essential but highly desirable
