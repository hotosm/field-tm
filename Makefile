# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

# All python source files
# MDS := $(wildcard ./docs/*.md)
MDS := \
	docs/dev/Backend.md \
	docs/dev/Database-Tips.md \
	docs/dev/Deployment-Flow.md \
	docs/dev/Frontend.md \
	docs/dev/Production.md \
	docs/dev/Version-Control.md \
	docs/dev/Setup.md \
	docs/dev/Troubleshooting.md \

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
