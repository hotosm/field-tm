import datetime
import os
import subprocess

def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh timestamp when new models initialised"""
    return datetime.datetime.utcnow()

# TODO: does this work and what's the right sql query??
def convert_geojson_to_postgis(folder, db):
    # folder=r'path'
    # db_connection="host=localhost dbname=hmm user=postgres password=apassword"

    # QUERY FROM STACK OVERFLOW Example
    # cmd='ogr2ogr -f "FileGDB" --config OGR_TRUNCATE YES "{0}" PG:"{1}" -sql "select geom from my table" -t_srs EPSG:3424 -nlt MULTIPOLYGON -overwrite -nln exported_table'.format(folder,db)
   
    # ROBS Querry
    cmd = 'ogr2ogr -skipfailures -progress -overwrite -f PostgreSQL PG:dbname=fmtm -nlt POLYGON Naivasha.geojson -lco COLUMN_TYPES=other_tags=hstore'
    subprocess.Popen(cmd, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()