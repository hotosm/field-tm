# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Osm-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

# All python source files
# MDS := $(wildcard ./docs/*.md)
MDS := \
	docs/DEV-1.-Getting-Started.md \
	docs/DEV-2.-Backend.md \
	docs/DEV-3.-Frontend.md \
	docs/DEV-4.-Database-Tips.md \
	docs/DEV-5.-Docker-Tips.md \
	docs/DEV-6.-Production-Deployment.md \
	docs/User-Manual-For-Project-Managers.md

PDFS := $(MDS:.md=.pdf)

all:
	@echo "Targets are:"
	@echo "	clean - remove generated files"
	@echo "	apidoc - generate Doxygen API docs"
	@echo "	check - run the tests"
	@echo "	uml - generate UML diagrams"

clean:
	@rm -fr docs/{apidocs,html,docbook,man} docs/packages.png docs/classes.png

uml:
	cd docs && pyreverse -o png ../src/backend/app

apidoc: force
	cd docs && doxygen

# Strip any unicode out of the markdown file before converting to PDF
pdf: $(PDFS)
%.pdf: %.md
	@echo "Converting $< to a PDF"
	@new=$(notdir $(basename $<)); \
	iconv -f utf-8 -t US $< -c | \
	pandoc $< -f markdown -t pdf -s -o /tmp/$$new.pdf

.SUFFIXES: .md .pdf

.PHONY: apidoc

force:
