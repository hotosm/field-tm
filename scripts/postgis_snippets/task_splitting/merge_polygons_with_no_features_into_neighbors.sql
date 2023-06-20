/*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>

This script divides an layer of buildings into clusters suitable for field 
mapping as part of the HOT Field Mapping Tasking Manager.
*/

-- Grab the areas with fewer than the requisite number of features
with lowfeaturecountpolys as (
  select *, st_area(p.geom) 
  as area   
  from "polys-with-count" as p
  -- TODO: feature count should not be hard-coded
  where p.numfeatures < 5   
), 
-- Grab a reference to all of the polygons with area (for sorting)
allpolys as (
   select *, st_area(p.geom) as area
   from "polys-with-count" as p
),
-- Find the neighbors of the low-feature-count polygons
-- Store their ids as n_polyid, numfeatures as n_numfeatures, etc
allneighborlist as (
  select p.*, 
    pf.polyid as n_polyid,
    pf.area as n_area, 
    pf.numfeatures as n_numfeatures
    -- length of shared boundary to make nice merge decisions 
    st_length2d(st_intersection(p.geom, pf.geom)) as sharedbound
  from lowfeaturecountpolys as p 
  inner join allpolys as pf 
  -- Anything that touches
  on st_touches(p.geom, pf.geom) 
  -- But eliminate those whose intersection is a point, because
  -- polygons that only touch at a corner shouldn't be merged
  and st_geometrytype(st_intersection(p.geom, pf.geom)) != 'ST_Point'
  -- Sort first by polyid of the low-feature-count polygons
  -- Then by descending featurecount and area of the 
  -- high-feature-count neighbors (area is in case of equal 
  -- featurecounts, we'll just pick the biggest to add to)
  order by p.polyid, pf.numfeatures desc, pf.area desc
  -- OR, maybe for more aesthetic merges:
  -- order by p.polyid, sharedbound desc
)

select distinct on (a.polyid) * from allneighborlist as a
