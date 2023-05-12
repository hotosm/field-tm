select p._uid_, p.geom, count(c.geom) as numpoints
from islingtonsplitpolygons p
left join islingtonbuildingcentroids c 
on st_contains(p.geom,c.geom)
group by p._uid_
