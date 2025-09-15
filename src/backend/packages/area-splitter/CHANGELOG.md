# CHANGELOG

## 2.0.0 (2024-12-12)

### Feat

- merge polygons smaller than 35% of perfect square polygon to neighbouring polygon

### Fix

- Update command line args
- Update usage message for current reality

## 1.5.1 (2024-10-30)

### Fix

- typo in fmtm_splitter sql num_buildings substitution

## 1.5.0 (2024-10-30)

### Feat

- use geodetic conversion of meters to degrees

### Fix

- precommit errors
- updated the tasks count in test cases of split by square
- add type int in argument
- avoid appending empty clipped polygons

### Refactor

- merge least feature count polygons with neighbouring polygons

## 1.4.0 (2024-10-24)

### Fix

- add missed unsimplifiedtaskpolygons to table drop

### Refactor

- remove support for sqlalchemy connections (psycopg2 driver only)

## 1.3.2 (2024-10-14)

### Fix

- remove osm-extracts from split by square
- invalid inclusion of alias to get num_buildings by pre-commit

### Refactor

- move old splitting algorithm parts --> postgis_snippets

## 1.3.1 (2024-09-22)

### Fix

- merge holes with neighboring polygons
- If --extract is used, it needs to be passed to split_by_square()

### Refactor

- pass args.data_extract and have parsing function handle it

## 1.3.0 (2024-07-12)

### Feat

- added data extracts to avoid creating tasks with no features

### Fix

- precommit
- check the lines count excluding minor highway tags

### Refactor

- use default line length 88 (over 132)

## 1.2.2 (2024-06-05)

### Refactor

- run sqlfluff and format sql files
- simplified the boundary of splitted ploygons and removed hardcoded buildings number
- removed redundant sql
- updated algorithm to split aoi when no linear features, by clustering

## 1.2.1 (2024-03-21)

### Fix

- clip square grid with AOI

## 1.2.0 (2024-03-08)

### Feat

- refactor out geopandas entirely, use shapely

## 1.1.2 (2024-02-15)

### Fix

- add useStWithin=False for polyline extracts
- add aeroway tag for linestring extract generation
- add railway tag to generated data extracts
- selecting all geometries if no data extract included
- more flexible parsing of extract tags
- update ST_Contains --> ST_Intersects for polylines view
- improve error handling if json file input invalid
- merge aoi geoms prior to data extract generation
- bug parsing geojson tags key if string

### Refactor

- remove ValueError if no geoms generated

## 1.1.1 (2024-02-11)

### Fix

- allow for automatic data extract generation
- more flexible parsing of aoi for split_by_sql

## 1.1.0 (2024-02-08)

### Feat

- parse multigeom aois with convex hull

### Fix

- command line usage of split by sql algo

### Refactor

- replace data extract parsing with staticmethod

## 1.0.0 (2024-01-30)

### Fix

- also accept sqlalchemy.orm.Session objects
- num_buildings is int type (not str)

### Refactor

- suppress geopandas 'column does not contain geometry'

## 1.0.0rc0 (2024-01-21)

### Feat

- remove sqlalchemy and geoalchemy, use psycopg2 directly

### Fix

- cleanup view lines_view after splitting complete

### Refactor

- fix all linting errors for pre-commit

## 0.2.6 (2024-01-18)

### Fix

- invalid tag json parsing PR (#20)

## 0.2.5 (2023-12-16)

### Fix

- improve handling of tags as json str
- return error on empty or invalid data extract

## 0.2.4 (2023-12-07)

### Fix

- run drop_all for tables prior to create_all (if exist)
- split_by_sql if no data extract provided

## 0.2.3 (2023-12-06)

### Fix

- handle multiple geoms if within FeatureCollection
- correctly handle file context for outputGeojson
- fix parsing of Feature type, improve logging
- prevent attempting to parse paths >250 chars (i.e. geojson)

## 0.2.2 (2023-12-05)

### Fix

- pass geojson as features, not geopandas df
- manage aoi parsing: geom, feat, featcol
- correct parsing of dict aoi objects

### Refactor

- reduce verbosity of logging when parsing geojsons
- merge dict and str aoi parsing

## 0.2.1 (2023-12-05)

### Refactor

- add comment to remove geopandas

## 0.2.0 (2023-12-04)

### Feat

- split by sql use osm_extracts and init db tables
- add helper functions for each split type
- add outputGeojson method

### Fix

- fix passing osm_extract via cmd line + api
- handle case where tags key is nested
- drop timestamp field is parsed in geojson
- sql splitting, commit transactions
- fix parsing of osm tags for db insert
- use gpd.read_file over GeoDataFrame.from_file
- add osm_id to ways_lines + ways_poly
- correctly pass args.dburl on cmd line
- correct extract highways into ways_lines
- drop of geojson type field if not exists
- use same session for all db queries
- refactor FMTMSplitter init to set aoi
- add db models to repo for generating tables
- update project_aoi geometry field --> geom

### Refactor

- command line to use helper functions
- split by feature
- split by square

## 0.1.0 (2023-10-25)

### Fix

- Add Doxygen and pvreverse support
- Add mkdocs config file
- Add mkdocs commentss to all classes and methods
- Add mkdocstrings-python to dependencies
- Ad dminimal doc support for mkdocs
- Add initial doc for the fmtm-splitter client
- Add workflow to update the wiki, probably won't work yet
- Supply the number of buildings per task at runtime
- Make the number of buildings parameter configurable at runtime
- Add something to the README.md doc
- Add screenshot of task splitting by feature
- standalone class & script to genersate tasks within an AOI
- Add support to be installed by pip
- Add basic documentation files

### Refactor

- rename LICENSE.md --> LICENSE
- rename build-ci workflow build_ci
- remove refs to wiki
