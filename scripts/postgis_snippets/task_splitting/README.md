# Task Splitting

The file ```task_splitting_optimized.sql``` is a spatial Structured Query Language (SQL) script to split an area of interest for field mapping into small "task" areas.

It operates within a Postgresql database with the the spatial extension PostGIS enabled. It requires write access to the database for performance reasons (there is another version without the suffice "_optimized" that doesn't require write access, but it's not likely to ever work well enough for production.

It takes into account roads, waterways, and railways to avoid forcing mappers to cross such features during mapping.

It uses a clustering algorithm to divide the area into discrete polygons containing an average number of tasks.

## Inputs (tables/layers)
This script takes 4 inputs, all of which are Postgresql/PostGIS tables/layers.
- ```project-aoi```, a PostGIS polygon layer containing a single feature: a polygon containing the Area of Interest.
- ```ways_line```, a  PostGIS line layer containing all OpenStreetMap "open ways" (the OSM term for linestrings) in the Area of Interest.
- ```ways_poly```, a Postgis polygon layer containing all OpenSTreetMap "closed ways" (the OSM term for polygons) in the AOI.
- ```project-config```, a Postgresql table containing settings (for example, the average number of features desired per task). _This isn't yet implemented; these settings are hard-coded for the moment. The script runs without a ```project-config``` table, but the number of features per task needs to be tweaked within the code._

OSM data (```ways-line``` and ```ways_poly```) can be loaded into a PostGIS database using the [Underpass](https://github.com/hotosm/underpass) configuration file [raw.lua](https://github.com/hotosm/underpass/blob/master/utils/raw.lua). If these two layers are present in the same database and schema as the ```project-aoi``` layer, the script will make use of them automatically (non-desctructively; it doesn't modify any tables other than the ones it creates unless you're unlucky enough to have tables matching the very specific names I'm using, which I'll later change to names that should avoid all realistically possible collisions).

## Running the script
You need a Postgresql database with PostGIS extension enabled. If both Postgresql and PostGIS are installed and you have permissions set up properly (doing both of those things is way beyond scope here), this should do the trick (choose whatever database name you want):

```
createdb [databasename] -O [username]
```
```
psql  -U [username] -d [databasename] -c 'CREATE EXTENSION POSTGIS'
```

Now you need to get some OSM data in there. You can get OSM data from the GeoFabrik download tool or the HOT export tool in ```.pbf``` format.

If you have your own way of getting the OSM data into the database, as long as it'll create the ```ways_line``` and ```ways_poly``` layers, go for it. Here's ho I'm doing it:

```
osm2pgsql --create -H localhost -U [username] -P 5432 -d [database name] -W --extra-attributes --output=flex --style /path/to/git/underpass/utils/raw.lua /path/to/my_extract.osm.pbf 
```

Now you need an AOI. I'm using QGIS connect to the database using the Database Manager, then creating a polygon layer (make a "Temporary scratch layer' with polygon geometry, draw an AOI, and import that layer into the database using the Database Manager). If you don't want to use QGIS, you can get a GeoJSON polygon some other way ([geojson.io](geojson.io) comes to mind) and shove it into the database using ogr2ogr or some other tool. Whatever. Just ensure it's a polygon layer in EPSG:4326 and it's called ```project-aoi```. 

```
psql -U [username] -d [database name] -f path/to/fmtm/scripts/postgis_snippets/task_splitting/task_splitting_optimized.sql
```

If all is set up correctly, that'll run and spit out some console output. It's moderately likely to include some warning messages due to messy OSM data, and will very likely complain that some tables do not exist (that's because I clobber any tables with colliding names before creating my own tables; don't run this script on random production databases until I collision-proof the names, and probably not even then).

## Outputs
You should now have the following useful layers in your Postgresql/PostGIS database:
- clusteredbuildings
- taskpolygons

As well as the following non-useful layers (well, they're useful for debugging, but not for end users' purposes):
- buildings
- dumpedpoints
- lowfeaturecountpolygons
- splitpolygons
- voronois

The ```taskpolygons``` layer can be exported as GeoJSON and used as a task to upload to the FMTM. This works in at least some cases; I'm not sure if there are cases where whatever was in the AOI and OSM layers causes outputs that break somehow (there are definitely some cases where building footprints in OSM are sufficiently messed up that they create weird task geometries, but so far these haven't actually broken anything). 

## Next steps

It's working OK now, but needs more work.
- Still simply discards polygon delineated by roads/waterways/railways rather than merging them into neighbors, which causes the task polygons to not tile the full AOI. This isn't necessarily always a problem, but it would be better to have the option to merge rather than discard those areas.
- Task polygon edges can be rough, often jagged, occasionally poking into buildings from adjacent polygons (though never, I think to the centroid). Working on simplifying/smoothing these, but there are some complications...
- Task polygon edges can contain closed-off loops unconnected to their main bodies. May need to increase density of segmentation of buildings in some places.
- Clustering is really pretty good, but not very strict at keeping similar numbers of features per cluster; you get a bit of a range of task sizes (though much, much better than anything we've had previously). I think it's possible to tweak this, though I think it might be expensive in terms of performance.


