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

PANDOC = /usr/bin/pandoc
PFLAGS = --from=markdown_mmd+yaml_metadata_block+smart \
	--standalone \
	--metadata keywords='ODK OpenDataKit OSM OpenStreetMap ODKCollect' \
	--metadata author='Rob Savoye'
WK = /usr/bin/wkhtmltopdf
WKFLAGS = -B 25mm -T 25mm -L 25mm -R 25mm -q -s Letter
CSS ?= /home/slowe/Documents/std-styles.css

DOCS = $(wildcard *.md)
HTML = $(DOCS:.md=.html)
PDF = $(DOCS:.md=.pdf)

all: $(HTML) $(PDF)
	@echo "Producing output files..."

%.html: %.md
	@title="$(shell grep "^#" $< | head -1 | tr -d '#')"; \
	$(PANDOC) $(PFLAGS) --to=html --toc $< -N --metadata title="$${title}" -o $*.html
	@echo "Wrote $*.html"

%.pdf: %.md
	@title="$(shell grep "^#" $< | head -1 | tr -d '#')"; \
	$(PANDOC) $(PFLAGS) --toc --to=pdf $<  --metadata title="$${title}" -o $*.pdf
	@echo "Wrote $*.pdf"

clean: force
	@rm -f $(HTML) $(PDF)

force:
.SUFFIXES: .md .html .pdf
