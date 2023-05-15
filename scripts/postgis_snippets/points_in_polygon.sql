/*
Takes a layer of points and a layer of polygons.
Counts the number of points in each polygon.
*/

select p._uid_, p.geom, count(c.geom) as numpoints
from islingtonsplitpolygons p
left join islingtonbuildingcentroids c 
on st_contains(p.geom,c.geom)
group by p._uid_
