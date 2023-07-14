/*
Selects all features (points, lines, or polygons) 
for which any portion falls within a given polygon.
*/

select features.*
from "AOI_Polygon" poly, "OSM_features" features
where st_intersects(features.geom, poly.geom)
