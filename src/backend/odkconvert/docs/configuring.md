# Configuring the Data Conversion

ODKConvert uses a YAML based configuration file that controls the
conversion process. While ideally the tags in the XForm are a match
for OSM tags, some survey questions generate very different primary
tags. All of the strings in this file are lower case, as when
processing the CSV file, everything is forced to be lower case.

YAML is a simple syntax, and most of the config options are simply
lists. For example:

    # All of the data that goes in a different non-OSM file
    private:
      - income
      - age
      - gender
 
There are 3 section in the config file, *ignore*, *convert*, and
*private*. Anything in the *ignore* section gets left out of all data
processing and output files. Anything in the *private* section is kept
out of the OXM output file, but included in a separate GeoJson
formatted file. That file contains all the data by whomever is
organizing this mapping campaign. There are often data items like
*gender* that doesn't belong in OSM, but that information is useful
to the organizers. Anything in the *convert* section is the real
control of the conversion process.

Both ODK and OSM use a *tag/value* pair. In OSM, the tags and values
are documented, and the mapping community prefers people use the
commonly accepted values. In ODK, the tags and values can be anything
the developer of the XLSForm chooses. Depending on the answer to the
survey question, that may be convert to a variety of OSM tags and
values. 

For this example, the value used in the **name** column of the XLSForm
*survey* sheet is *waterpoint*. It has several values listed
underneath. Each of those is for the answer given to the waterpoint
survey question. If the answer matches the value, it returns both the
tag and the value for OSM. An equal sign is used to deliminate them.

	- waterpoint:
      - well: man_made=water_well
      - natural: natural=water

Some features have multiple OSM tags for a single survey question
answer. To handle this case, all entries are deliminated by a comma.

	- power:
      - solar: generator::source=solar,power=generator
      - wind: generator::source=wind,power=generator
      - hydro: generator::source=hydro,power=generator
      - geothermal: generator::source=geothermal,power=generator
      - grid: generator::source=electricity_network,power=generator
