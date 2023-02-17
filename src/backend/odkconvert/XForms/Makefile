# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

# The Rob project on odk.hotosm.org
PROJECT=19

XLSFILES = buildings.xls
POLY=university.geojson

XXXXLSFILES = \
    buildings.xls \
    cemeteries.xls \
    education.xls \
    healthcare.xls \
    landuse.xls \
    natural.xls \
    place.xls \
    regilious.xls \
    school.xls \
    toilets.xls \
    waste.xls \
    waterways.xls

XMLFILES = $(XLSFILES:.xls=.xml)

all: $(XMLFILES)

EXTRACT = make_data_extract.py

%.xml : %.xls
	xls2xform --pretty_print $<
	@xml=$(subst .xls,.xml,$<);

# A simple naming convention is used to make it possible to automate as
# much as possible. The basename of the XLSForm file matches the form_id
# column in the settings sheet. The make_data_extract.py also uses the
# same value in the category options.
# Any associated data extract file from OSM is uploaded as well if it
# exists. Note that when using an external geojson file, Enketo doesn't
# support that. It only works on a device.
upload: $(XMLFILES)
	@target=$(<:.xml=); \
	if test -e $${target}.geojson; then \
	  datafiles="$(DATAFILES) $${target}.geojson"; \
	else \
	  datafiles="$(DATAFILES)"; \
	fi; \
	odk_client.py -i $(PROJECT) -f $${target} -x create $< $${datafiles}

xform: $(XMLFILES)
	target=$(<:.xml=); \
	base=$(basename $(notdir $(POLY))); \
	sed -e "s:<data id=\"[a-zA-Z0-9_]*\":<data id=\"$${base} $${target}\":" \
		-e "s/<h:title>[a-zA-Z0-9_]*</<h:title>$${base} $${target}</" \
		-e "s,jr://file/[a-zA-Z0-9_]*.geojson,jr://file/$${base}$${target}.geojson," $< > $${base}$${target}.xml

force:

clean:
	rm -f *.xml

.PHONEY: upload
