/*
Selects every building within a set of OSM polygons that has a tag, any tag,
in addition to 'building'. 

This is a very rough proxy for buildings that have been field mapped. It's 
rough because many buildings have tags other than 'building' that have 
only been remotely mapped. Still, it's useful because most buildings that
have only been digitized in JOSM/ID only have the tag 'building'='yes'.
This filters all of those out.

Works on OSM extracts converted to PostGIS layers using the Underpass 
database schema: 

https://github.com/hotosm/underpass/blob/master/utils/raw.lua

which converts all tags into a jsonb object in a 'tags' column.
*/


with tagsarrayed as
(
select
*,
array(select jsonb_object_keys(tags)) as keys
from "ways_poly"
where tags->>'building' is not null
),
tagscounted as
(
select *, array_length(keys, 1) as numkeys
from tagsarrayed
)
select *
from tagscounted
where numkeys > 1
