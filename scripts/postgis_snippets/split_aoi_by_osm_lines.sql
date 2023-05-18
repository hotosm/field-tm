/*
This incorporates a number of the other scripts into one that accepts:
- A layer of OSM lines from osm2pgsql* 
- A single AOI polygon.

It splits the AOI into multiple polygons based on the roads, waterways, and 
railways contained in the OSM line layer.

* It is important to use a line layer from osm2pgsql, because this script
assumes that the lines have tags as JSON blobs in a single column called tags.
*/

with splitlines as(
  select lines.* 
  from "AOI" poly, ways_line lines 
  where st_intersects(lines.geom, poly.geom)
  and (tags->>'highway' is not null
       or tags->>'waterway' is not null
       or tags->>'railway' is not null)
)

  SELECT (ST_Dump(ST_Polygonize(ST_Node(multi_geom)))).geom
  FROM   (
    SELECT ST_Collect(s.geom) AS multi_geom
    FROM splitlines s
) splitpolys;
