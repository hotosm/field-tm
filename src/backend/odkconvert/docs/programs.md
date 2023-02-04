# ODK Convert Utility Programs

ODK Convert contains a few standalone utility programs for converting
data from ODK Collect and the ODK Central server, and a few support
modules.

## make_data_extract.py

To use the new select_one_from_file for editing existing OSM data you
need to produce a data extract from OSM. This can be done several
ways, but needed to be automated to be used for FMTM.

	options:
		-h, --help            show this help message and exit
		-v, --verbose         verbose output
		-o, --overpass        Use Overpass Turbo
		-p, --postgres        Use a postgres database
		-g GEOJSON, --geojson GEOJSON Name of the GeoJson output file
	    -i INFILE, --infile INFILE  Use a data file
		-dn DBNAME, --dbname DBNAME Database name
		-dh DBHOST, --dbhost DBHOST Database host
		-b BOUNDARY, --boundary BOUNDARY  Boundary polygon to limit the data size
		-c {buildings,amenities}, --category {buildings,amenities}
                        Which category to extract

For example,

	./make_data_extract.py --overpass --boundary mycounty.geojson

will use Overpass Turbo to extract data within the boundary. By
default, buildings are extracted.

Or this example:

	./make_data_extract.py --postgres -dn colorado --category amenities --boundary mycounty.geojson

Which will extract the data from postgres. By default *localhost* is
used, but that can be changed with --dbhost. This will use the
database *colorado*, and extract all the amenities.


## File Formats

OpenDataKit has 3 file formats. The primary one is the source file,
which is in XLSX format, and follows the XLSXForm specification. This
file is edited using a spreadsheet program, and convert using the
xls2xform program. That conversion products an ODK XML file. That file
is used by ODK Collect to create the input forms for the mobile
app. When using ODK Collect, the output file is another XML format,
unique to ODK Collect. These are the data collection instances.

The ODK server, ODK Central supports the downloading of XForms to the
mobile app, and also supports downloading the collected data. The only
output format is CSV.

## CSVDump.py
CSVDump.py converts a CSV downloaded from ODK Central to OSM XML.

	options:
		-h, --help                   - show this help message and exit
		-v, --verbose                - verbose output
		-i CSVFILE, --infile CSVFILE - The input file downloaded from ODK Central

## odk2csv.py
odk2csv.py converts an ODK XML instance file to the same CSV format
used by ODK Central.

	options:
		-h, --help                       - show this help message and exit
		-v, --verbose                    - verbose output
		-i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

These are the modules containing support functions. These need to be
loaded into the python package managber, pip, before they can be
used. For debugging purposes these can be run from the command line as
well.

To install these from the source tree, you can either install
manually,

		pip install -e .
or run the python setup program

		python setup.py install

## ODKDump.py
	options:
		-h, --help              - show this help message and exit
		-v, --verbose           - verbose output
		-i, --instance INSTANCE - The instance file from ODK Collect
		-x, --xform XFORM       - Load an alternal conversion file
		-o, --outdir            - The directory for the output file

## ODKForm.py

ODKForm.py parses the ODK XML XForm, and creates a data structure so
any code using this class can access the data types of each input
field. It can be run standalone from the command line, but this is
only for debugging purposes.

	options:
		-h, --help                           - show this help message and exit
		-v, --verbose,                       - verbose output
		-i, --infile XFORM, --instance XFORM - The definition file from ODK Collect

## ODKInstance.py

ODKInstance.py parses the ODK Collect instanceXML file, and creates a
data structure so any code using this class can access the collected
data values. It can be run standalone from the command line, but this is
only for debugging purposes.

	options:
		-h, --help                       - show this help message and exit
		-v, --verbose                    - verbose output
		-i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

## convert.py
This module uses the yaml config file to handle the conversion
process.

## osmfile.py
This module write OSM XML format output file.

## yamlfile.py
This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion.
