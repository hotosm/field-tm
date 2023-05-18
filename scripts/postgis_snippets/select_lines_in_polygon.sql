/*
Selects all lines for which any portion falls within a given polygon.
*/

select lines.*
from "AOI_Polygon" poly, "OSM_lines" lines
where st_intersects(lines.geom, poly.geom)
