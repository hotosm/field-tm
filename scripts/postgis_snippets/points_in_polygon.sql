/*
Takes a layer of points and a layer of polygons.
Counts the number of points in each polygon.
*/

select poly._uid_, poly.geom, count(cent.geom) as numpoints
from islingtonsplitpolygons poly
left join islingtonbuildingcentroids cent 
on st_contains(poly.geom,cent.geom)
group by poly._uid_

-- Count with intersect instead
/*
select sp.polyid, sp.geom, count(b.geom) as numfeatures
from "splitpolys" sp
left join "buildings" b
on st_intersects(sp.geom,b.geom)
group by sp.polyid, sp.geom
*/
