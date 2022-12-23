# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

#!/bin/bash

# Crash Bash on error
# set -e

echo probably requires a linux user called fmtm
#TODO figure out if this is the case

if [ -x nginx ]
then
    echo nginx is already installed
else
    echo installing nginx because why not
    sudo apt install nginx
fi

echo making sure we have pip3 and venv
if [ -x pip3 ]
then
    echo pip3 already installed
else
    echo pip3 was not installed, probably installing
    sudo apt install python3-pip -y >> logs/setup.log 2>> logs/error.log
fi

echo Installing Wheel on base python I guess
pip3 install wheel >> logs/setup.log 2>> logs/error.log
pip3 install virtualenv >> logs/setup.log 2>> logs/error.log
if [ -d venv ]
then
    echo venv was already present, hope it is the right one
else
    echo Installing venv
    sudo apt install python3-venv -y >> logs/setup.log 2>> logs/error.log
    python3 -m venv venv
fi
source venv/bin/activate
echo Installing Wheel on venv python I guess
pip install wheel >> logs/setup.log 2>> logs/error.log
sudo apt install python3-pip -y >> logs/setup.log 2>> logs/error.log

echo installing GDAL
sudo apt install -y gdal-bin libgdal-dev >> logs/setup.log 2>> logs/error.log
echo setting up python hooks for GDAL, pygdal.
echo Doing so via a horrible hack using a Python script to extract the latest
echo version of pygdal compatible with the specific GDAL installed. 
gdalversion=$(gdal-config --version)
echo $gdalversion
GDALERROR=$((pip install pygdal==$gdalversion) 2>&1)
# echo $GDALERROR
python3 scripts/parse_pip_error.py "$GDALERROR" "$gdalversion"
pygdalversion=$(<pygdalversion.txt)
echo
echo installing pygdal version $pygdalversion
pip install pygdal==$pygdalversion >> logs/setup.log 2>> logs/error.log
rm pygdalversion.txt

echo installing nodejs and npm
sudo apt install -y nodejs npm >> logs/setup.log 2>> logs/error.log
echo installing osmtogeojson 
sudo npm install -g osmtogeojson >> logs/setup.log 2>> logs/error.log


echo installing postgres from default Ubuntu repo
echo as per https://www.digitalocean.com/community/tutorials/how-to-install-postgresql-on-ubuntu-22-04-quickstart

if [ -x psql ]
then
    echo Postgres already installed
else
    echo  Postgres was not installed, probably installing
    sudo apt install -y postgresql postgresql-contrib libpq-dev >> logs/setup.log 2>> logs/error.log
fi

echo installing postgis
sudo apt install -y postgis postgresql-14-postgis-3 >> logs/setup.log 2>> logs/error.log

echo starting postgresql service
sudo systemctl start postgresql.service

# TODO This is a pretty obvious password (it's md5 hashed).
# TODO would be better to use SHA256 anyway
# Generate another one using bash:
# echo -n passwordusername | md5sum
# and paste the result into the following command
# with the prefix 'md5' (the hash below begins with 540e)

echo Creating role postgres user fmtm
sudo -u postgres psql -c "CREATE ROLE fmtm WITH PASSWORD 'md5540e7aa2739a14c6f2e6f07fd09c67f1';"
echo Giving fmtm login rights
sudo -u postgres psql -c "ALTER ROLE fmtm WITH LOGIN"
echo Giving fmtm superuser rights
sudo -u postgres psql -c "ALTER ROLE fmtm WITH SUPERUSER"
echo Creating database fmtm
sudo -u postgres psql -c "CREATE DATABASE fmtm WITH OWNER fmtm;"
echo creating postgis extension
sudo -u fmtm psql -c "CREATE EXTENSION postgis;"

echo Done.
echo To use the utilities here, activate the virtual environment with:
echo source venv/bin/activate
echo
echo And type deactivate to get out when you are done.
