-- This is a placeholder to insert the algorithms code from one directory higher.
-- E.g. ../avg_building_voronoi.sql

-- There are many ideas for potential algorithms to implement, but little time do to do!
-- PRs always welcome 🙏

-- For each task polygon, subtract the features, leaving a negative space
-- Then create a straight skeleton framework inside of that
SELECT CG_StraightSkeleton(geom, true) geom from negspace;
