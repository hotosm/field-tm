# Dealing with External Data in ODK

## External Datasets

[ODK Collect](https://www.getodk.org) has recently gained the ability
to load an external data file in GeoJson format of existing data. It's
then possible to select existing data and then import it's values into
the XForm as default values. This lets the mapper use the XForm to
change the existing data, or add to it. Any changes will need to be
conflated later, that'll be another document.

Why do I want to use ODK Collect to edit map data ? Much of what is
currently in [OpenStreetMap](https:www.openstreetmap.org) is lacking
metadata, or the data has changed, like when a restaurant changes
owners and gets a new name. Also most all remote mapping using
satellite imagery lacks tags beyond *building=yes*. When we are doing
a ground data collection project, we want to add useful tags like the
building material, or whether it's a cafe or a hospital. 

Old imports also bring in problems, for example the infamous [TIGER
import](https://wiki.openstreetmap.org/wiki/TIGER). Mappers have been
cleaning that mess up for over a decade. But an old import may have a
weird value for an OSM tag, and it's usually better to update to a
more community approved data model. The beauty and the curse of OSM
data is it's wonderful flexibility. People do invent new tags for a
specific mapping campaign or import that and escape being reviewed.
There are also typographical mistakes, weird capitalization, embedded
quote marks, all sorts of weird values worth correcting.

## Creating the GeoJson file

While there are a multitude of places to get data from, since I'm
using OSM data, I can either download a database dump from
[GeoFabrik](http://download.geofabrik.de/index.html), and use that as
a flat file or import it into a database. Or use Overpass Turbo. I
prefer using the datafile from GeoFabrik, and importing it into a
database.

There is a translation between the column names one gets when querying the
data and how ODK Collect sees it. There is the following translation
from ODK to OSM as well, and they all have to work together for a clean
data flow. I like to keep all the tag and values as similar as
possible, cause otherwise it's easy to get lost. The rough rule of
thumb is to make sure that all names are unique. As I'm using
[ogr2ogr](https://gdal.org/programs/ogr2ogr.html) to do data extracts
from a postgres database, I have a little more control than when
using Overpass. Plus I can process much larger datasets than Overpass
can. 

For my database SQL queries, I use the *AS* keyword to redefine the
output column name, so I can use the OSM standard name in the survey
and choices sheets. That makes the next translation step much
cleaner. I try to be consistent so it's easier to follow the data
flow. My currrent technique is to append an x to the end of each
column, so *healthcare* becomes *healthcarex*.

Then in the XLSForm, I can use *healthcarex* for the instance, and
then I'll use *xhealthcare* as the value for the *calculation* column
in the survey sheet. Then the value in the *name* column of the survey
sheet is just *healthcare*, as that'll translate directly into it's
OSM tag equivalant.

If use use a *text* type in your XLSForm, you can support most any
weird value. But as we are aiming for tag validation and tag
completeness, we prefer to have an approved value. If using a data
model, the the list of choices for a tag is defined. Anything outside
of that is not part of the data model, and will cause an
error. That's documented later in this doc. Currently unless you are
very careful with what columns you return from the SQL query, you will
get XPATH erros in ODK Collect.

Currently if a weird value is found in the data extract that continues
to break ODK Collect, it must be removed. In that case it must be
manually edited, and the weird values changed or deleted. At some
point I may write a filter program that uses the data model as defined
in a YAML file, but I'm not there yet.

## Debugging select_from file with GeoJson

Debugging complex interactions between the XLSForm, my
external data files, and ODK Collect often has left me scratching my
head more than once. Here's a few tricks to help debug what is going
on.

### Disable the map appearance

Most of the time when using external data you have the *map* value in
the *appearance* column of the survey sheet. That's how we want to use
it in the field. But it slows down the repetitious process of
debugging everything. I turn off *map* values, and then I just have
the select menu, which is more efficient. That works especially well
if you have a small data file for testing, because then it's easy to
cycle between them.

To use the placement map, here's an example.

| type|name|label|appearance|
|-----|----|-----|----------|
|select_one_from_file camp_sites.geojson|existing|Existing Campsites|map|

And an example were there values in the data file are an inline select
menu instead.

| type|name|label|appearance|
|-----|----|-----|----------|
|select_one_from_file camp_sites.geojson|existing|Existing Campsites|minimal|


### Display calculated values

Often the bug you are trying to find is obscure, you just don't see
any of the data file values being propogated into ODK Collect, when
that was working previously. In that case I just add a text survey
question, whose entire purpose is to display any of the values 

| type|name|label|calculation|trigger|
|-----|----|-----|-----------|-------|
|calculate|xid|OSM ID|instance(“camp_sites”)/root/item[id=${existing}]/id|
|calculate|xlabel|Get the label|instance(“camp_sites”)/root/item[id=${existing}]/title||
|calculate|xref|Reference number|instance(“camp_sites”)/root/item[id=${existing}]/ref||
|calculate|xlocation|Location|instance(“camp_sites”)/root/item[id=${existing}]/geometry||
|calculate|xtourism|camping type|instance(“camp_sites”)/root/item[id=${existing}]/tourism||
|calculate|xleisure|leisure type|instance(“camp_sites”)/root/item[id=${existing}]/leisure||
|text|debug1|Leisure|${xleisure}|${existing}
|text|debug2|OSM ID|${xid}|${existing}|
|text|debug3|Ref number|${xref}|${existing}
|text|debug4|Tourism|${xtourism}|${existing}

### Error Dialog

Assuming xls2xform is happy, sometimes you get this error message in
ODK Collect when switching screens. You'll see this when you have a
value in your data file for a *select_one* survey question, but that
value not in the list of values in the choices sheet for that tag. In
this example, there is no *doctor* value in the *healthcare*
selection in the choices sheet.

![XPath Error](xlsimages/image1.jpg){width=500}
