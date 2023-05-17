/*
Takes a layer of points and a layer of polygons.
Counts the number of points in each polygon.
*/

select poly._uid_, poly.geom, count(cent.geom) as numpoints
from islingtonsplitpolygons poly
left join islingtonbuildingcentroids cent 
on st_contains(poly.geom,cent.geom)
group by poly._uid_
