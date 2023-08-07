 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

Part 01 of FMTM task splitting.

This script splits an Area of Interest into polygons based on OpenStreetMap lines (roads, waterways, and railways). It doesn't take features into account.

It takes three inputs, all PostGIS layers:
1) A polygon layer called project-aoi
2) A line layer formatted like OSM extracts with the Underpass schema (tags in a jsonb object) called ways_line
3) A polygon layer formatted like OSM extracts with the Underpass schema (tags in a jsonb object) called ways_poly

It outputs a single PostGIS polygon layer called polygonsnocount (the "nocount" bit refers to the fact that at this stage we haven't determined if there's anything inside of these polygons; soon we'll count the features to be mapped within them, normally to split further). This layer should be considered a temporary product, but is the input to the next stage of the splitting algorithm. 

More information in the adjacent file task_splitting_readme.md.
*/

/*
***************************PARAMETERS FOR ROB************************
- At the moment I split on anything with a highway, waterway, or railway tag of any kind. We'll probably want to allow users to configure which lines they actually use as splitting boundaries. 
- At the moment it always uses the AOI polygon itself as a splitline. That should be optional.
*/

-- If this table already exists, clobber it
DROP TABLE IF EXISTS polygonsnocount;
-- Create a new polygon layer of splits by lines
CREATE TABLE polygonsnocount AS (
  -- The Area of Interest provided by the person creating the project
  WITH aoi AS (
    SELECT * FROM "project-aoi"
  )
  -- Extract all lines to be used as splitlines from a table of lines
  -- with the schema from Underpass (all tags as jsonb column called 'tags')
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
  ,partlymerged AS (
    SELECT ST_LineMerge(ST_Union(splitlines.geom)) AS geom
    FROM splitlines
  )
  -- Add closed ways (polygons) that are actually roads (like roundabouts)
  ,polyroads AS (
    SELECT ST_Boundary(wp.geom) AS geom
    FROM aoi a, "ways_poly" wp
    WHERE ST_Intersects(a.geom, wp.geom)
    AND tags->>'highway' IS NOT NULL
  )
  -- Merge all the lines from closed ways
  ,prmerged AS (
    SELECT ST_LineMerge(ST_Union(polyroads.geom)) AS geom
    from polyroads
  )
  -- Add them to the merged lines from the open ways
  ,merged AS (
    SELECT ST_Union(partlymerged.geom, prmerged.geom) AS geom
    FROM partlymerged, prmerged
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
