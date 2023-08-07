/*
Create a specified number of clusters from any geometry
(tested with points and polygons, no idea what it does with lines)
Simply adds a "cid" column to all features, with the same
value for all features in each cluster
*/

/*
-- Version that does not retain attributes
select st_clusterkmeans(geom, 200) --creates 200 clusters
over () 
as cid, geom 
from features
*/

-- This version retains attributes
select *, st_clusterkmeans(geom, 200) --creates 200 clusters
over ()  
as cid 
from features

