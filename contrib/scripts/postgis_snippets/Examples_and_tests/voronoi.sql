/*
Creates Voronoi polygons from a layer of points. From inside to out:
- Collects the points layer into a single multipoint geometry (st_collect)
- Creates voronoi polygons (st_voronoipolygons)
- Dumps them to separate features (st_dump)

Caution: Does NOT retain the original UIDs of the points. You get a number of 
Voronoi polygons equal to the original number of points, but the IDs of the 
points don't match those of the polygons they fall within.
*/

with voronoi (v) as
    (select st_dump(st_voronoipolygons(st_collect(geom))) 
	as geom from points)
select (v).geom from voronoi;
