# Deprecated; now using pg_dump

Import the GeoJSON file to PostGIS. To function in the same way as a layer directly imported from OSM using osm2psql, the ```tags``` column needs to be jsonb type.

There probably is a simple way to combine changing the column type and casting the json string to the actual jsonb type, but I don't know how to do it. So here's the workaround:

- Rename the tags column to tagsvarchar

```
alter table "Islington_AOI_polygons"
rename column tags to tagsvarchar;
```

- create a new tags column with the correct type

```
alter table "Islington_AOI_polygons"
add column tags jsonb
```

- Cast the json strings to jsonb and copy them over

```
update "Islington_AOI_polygons"
set tags = tagsvarchar::jsonb
```

- Nuke the renamed column with the varchar, leaving only the ```tags``` column with the jsonb type

```
alter table "Islington_AOI_polygons"
drop column tagsvarchar
```
