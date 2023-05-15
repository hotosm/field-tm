/*
Create a specified number of clusters 

*/
select st_clusterkmeans(geom, 100) --creates 100 clusters
over () 
as cid, geom from points
