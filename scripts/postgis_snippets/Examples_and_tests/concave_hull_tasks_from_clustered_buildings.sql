WITH clusteredbuildings AS (
  select * from "clustered-buildings"
)

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
