select p._uid_, count(c.geom) as numpoints
from OSM_polygons p
left join OSM_Building_centroids c 
on st_contains(p.geom,c.geom)
group by p._uid_
