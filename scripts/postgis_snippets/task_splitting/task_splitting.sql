/*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>

This script divides an area into smaller areas suitable for field mapping as part of the HOT Field Mapping Tasking Manager.

It takes four inputs, all of which are tables in a Postgresql database with 
the PostGIS extension enabled. The first three are PostGIS layers in
an EPSG:4326 projection.

1) "project_aoi", a polygon layer with a single-feature Area of Interest 
2) "ways_line", a line layer, usually from OpenStreetMap, covering the AOI
3) "ways_poly", a polygon layer, usually from OSM, covering the AOI
4) "project_config", a table with parameters for the splitting
    - A desired number of features per task polygon
    - A set of tags indicating what features should be included in the line 
      polygon layers
    - Maybe other stuff. I don't know yet; I haven't implemented this table yet.

TODO: implement the config table
*/

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
  -- A selection of highways, waterways, and all railways
  /*
  AND (tags->>'highway' = 'trunk'
    OR tags->>'highway' = 'primary'
    OR tags->>'highway' = 'secondary'
    OR tags->>'highway' = 'tertiary'
    OR tags->>'highway' = 'residential'
    OR tags->>'highway' = 'unclassified'
    OR tags->>'waterway' = 'river'
    OR tags->>'waterway' = 'drain'
    OR tags->>'railway' IS NOT NULL
    )
  */
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
-- Create a polygon for each area enclosed by the splitlines
,splitpolysnoindex AS (
  SELECT (ST_Dump(ST_Polygonize(comb.geom))).geom as geom
  FROM comb
)
-- Add an index column to the split polygons
-- Row numbers can function as temporary unique IDs for our new polygons
,splitpolygons AS(
SELECT row_number () over () as polyid, * 
from splitpolysnoindex
)
-- Grab the buildings.
-- While we're at it, grab the ID of the polygon the buildings fall within.
-- TODO: at the moment this uses ST_Intersects, which is fine except when
--   buildings cross polygon boundaries (which definitely happens in OSM).
-- In that case, the building should probably be placed in the polygon
--   where the largest proportion of its area falls. At the moment it
--   duplicates the building in 2 polygons, which is bad!
-- There's definitely a way to calculate which of several polygons the largest
--   proportion of a building falls, that's what we should do.
-- Doing it as a left join would also be better.
-- Using the intersection of the centroid would also avoid duplication,
--   but sometimes causes weird placements.
,buildings AS (
  SELECT b.*, polys.polyid 
  FROM "ways_poly" b, splitpolygons polys
  WHERE ST_Intersects(polys.geom, b.geom)
  AND b.tags->>'building' IS NOT NULL
)
-- Count the features in each polygon split by line features.
,polygonsfeaturecount AS (
  SELECT sp.polyid, sp.geom, count(b.geom) AS numfeatures
  FROM "splitpolygons" sp
  LEFT JOIN "buildings" b
  ON sp.polyid = b.polyid
  GROUP BY sp.polyid, sp.geom
)
-- Filter out polygons with no features in them
-- TODO: Merge the empty ones into their neighbors and replace the UIDs
--       with consecutive integers for only the polygons with contents
,splitpolygonswithcontents AS (
  SELECT *
  FROM polygonsfeaturecount pfc
  WHERE pfc.numfeatures > 0
)
/*******************************************************************************
-- Uncomment this and stop here for split polygons before clustering
SELECT * FROM splitpolygonswithcontents
*******************************************************************************/

-- Add the count of features in the splitpolygon each building belongs to
--   to the buildings table; sets us up to be able to run the clustering.
,buildingswithcount AS (
  SELECT b.*, p.numfeatures
  FROM buildings b 
  LEFT JOIN polygonsfeaturecount p
  ON b.polyid = p.polyid
)
-- Cluster the buildings within each splitpolygon. The second term in the
-- call to the ST_ClusterKMeans function is the number of clusters to create,
-- so we're dividing the number of features by a constant (10 in this case)
-- to get the number of clusters required to get close to the right number
-- of features per cluster.
-- TODO: This should certainly not be a hardcoded, the number of features
--       per cluster should come from a project configuration table
-- TODO; CRITICAL: Sets of buildings in polygons with less than twice the
--                 number of desired buildings plus one
--                 per task must be excluded from this operation
,buildingstocluster as (
  SELECT * FROM buildingswithcount bc
  WHERE bc.numfeatures > 21
)
,clusteredbuildingsnocombineduid AS (
SELECT *,
  ST_ClusterKMeans(geom, cast((b.numfeatures / 10) + 1 as integer))
  over (partition by polyid) as cid
FROM buildingstocluster b
)
-- uid combining the id of the outer splitpolygon and inner cluster
,clusteredbuildings as (
  select *, 
  polyid::text || '-' || cid as clusteruid
  from clusteredbuildingsnocombineduid
)
/*******************************************************************************
-- Uncomment this and stop here for clustered buildings
SELECT * FROM clusteredbuildings
*******************************************************************************/

/*********************Magic approach******************************************
-- Magic function that Steve is writing
-- This may prevent us from needing to write tables or queries to the db.
,hulls AS(
  select Ivan_Hull(ST_Collect(clb.geom), clb.clusteruid, pwc.geom) as geom
  from clusteredbuildings clb
  LEFT JOIN splitpolygonswithcontents pwc ON clb.polyid = pwc.polyid
)
select * from hulls
******************************************************************************/

--******************Concave Hull approach**************************************
,hulls AS(
  -- Using a very high param_pctconvex value; smaller values often produce
  -- self-intersections and crash. It seems that anything below 1 produces
  -- something massively better than 1 (which is just a convex hull) but
  -- no different (i.e. 0.99 produces the same thing as 0.9999), so
  -- there's nothing to lose choosing a value a miniscule fraction less than 1.
  select clb.polyid, clb.cid, clb.clusteruid, 
		 ST_ConcaveHull(ST_Collect(clb.geom), 0.9999) as geom
  from clusteredbuildings clb
  group by clb.clusteruid, clb.polyid, clb.cid
)
-- Now we need to:
-- - Get rid of the overlapping areas of the hulls
--   - Create intersections for the hulls so all overlapping bits are separated
--   - Check what's inside of the overlapping bits
--     - If it's only stuff belonging to one of the original hulls, give that
--       bit to the hull it belongs to
--     - If the overlapping are contains stuff belonging to more than one hull,
--       somehow split the overlapping bit such that each piece only contains
--       stuff from one or another parent hull. Then merge them back.
-- - Do something Voronoi-esque to expand the hulls until they tile the
--   entire AOI, creating task polygons with no gaps
select * from hulls
--*****************************************************************************/

/******************Voronoi approach********************************************
-- This actually generates pretty good boundaries (not perfect, but not bad).
--   They'd be better if we segmentized the buildings first.
-- The problem is that it is unacceptably slow on big datasets, due to the
--   lack of a spatial index on the building nodes and voronoi polygons.
--   This could be solved by creating tables and indexes as we go, but
--   then we don't have a nice pure query that doesn't modify the database.
--   If only there were a way to retain the uid of the point each Voronoi
--   polygon was created from...

-- Extract all of the nodes in the buildings as points
-- TODO: segmentize them first so that the points are denser and make nicer
--       Voronoi polygons that don't poke into their neighbor's buildings
,dumpedpoints AS (
  SELECT cb.osm_id, cb.polyid, cb.cid, cb.clusteruid,
  (st_dumppoints(geom)).geom
  FROM clusteredbuildings cb
)
-- Aggregate the points by the unique ids of the clusters so that the next
-- step (Voronoi polygons) can treat each cluster as a discrete dataset
,dumpedpointsuid as (
  SELECT dp.clusteruid, dp.geom
  FROM dumpedpoints dp
  GROUP by dp.geom, dp.clusteruid
)

-- Generate a set of voronoi polygons for each splitpolygon, so that the
--   Voronois tile each splitpolygon but don't poke out of them
,voronoisnoid as (  
  SELECT
    st_intersection((ST_Dump(ST_VoronoiPolygons(
			ST_Collect(points.geom)
			))).geom, 
	             sp.geom) as geom
	FROM dumpedpoints as points, 
	splitpolygonswithcontents as sp
	where st_contains(sp.geom, points.geom)
	group by sp.geom
)
-- Re-associate each Voronoi polygon with the point it was created from.
-- TODO: This has major performance issues because there's no spatial index
--       on the points or Voronoi polygons. On a big dataset it can take hours.
--       There are only three possible solutions that I can see:
--         - Write the points and Voronoi polygons as tables and index them
--         - Find a way to retain the IDs of the points when creating Voronoi
--           polygons from them
--         - Wait for Steve to write a magic function
,voronois as (
  select p.clusteruid, v.geom
  from voronoisnoid v, dumpedpoints p
  WHERE st_within(p.geom, v.geom)
)
select *
from voronois v
*****************************************************************************/

