-- simple version (does not retain attributes)
/*
SELECT st_centroid(geom) as geom
FROM "osm_polygons" where building is not null;
*/

-- composed version (also does not retain attributes)
/*
with buildings as (
    select * 
    from "OSM_polygons"
    where building is not null
    )
select st_centroid(geom) as geom
from buildings;
*/

-- composed version that retains attributes
with buildings as (
    select * 
	from "OSM_polygons"
	where building is not null
    )
select *, st_centroid(geom) as centroid_geom
from buildings;
