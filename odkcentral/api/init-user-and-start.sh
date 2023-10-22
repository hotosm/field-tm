#!/bin/bash

set -eo pipefail

# Wait for database to be available
wait-for-it "${CENTRAL_DB_HOST:-central-db}:5432"

### Init, generate config, migrate db ###
echo "Stripping pm2 exec command from start-odk.sh script (last 2 lines)"
head -n -2 ./start-odk.sh > ./init-odk-db.sh
chmod +x ./init-odk-db.sh

echo "Running ODKCentral start script to init environment and migrate DB"
echo "The server will not start on this run"
./init-odk-db.sh

### Create admin user ###
echo "Creating test user ${SYSADMIN_EMAIL} with password ***${SYSADMIN_PASSWD: -3}"
echo "${SYSADMIN_PASSWD}" | odk-cmd --email "${SYSADMIN_EMAIL}" user-create || true

echo "Elevating user to admin"
odk-cmd --email "${SYSADMIN_EMAIL}" user-promote || true

### Run server (hardcode WORKER_COUNT=1 for dev) ###
export WORKER_COUNT=1
echo "Starting server."
exec npx pm2-runtime ./pm2.config.js
