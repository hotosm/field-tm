set -eo pipefail

### Init, generate config, migrate db
echo "Stripping pm2 exec command from start-odk.sh script (last 2 lines)"
head -n -2 ./start-odk.sh > ./init-odk-db.sh
chmod +x ./init-odk-db.sh

echo "Running ODKCentral start script to init environment and migrate DB"
echo "The server will not start on this run"
./init-odk-db.sh


### Create admin user
echo "Creating test user ${SYSADMIN_EMAIL} with password ${SYSADMIN_PASSWD}"
echo "${SYSADMIN_PASSWD}" | odk-cmd --email "${SYSADMIN_EMAIL}" user-create || true

echo "Elevating user to admin"
odk-cmd --email "${SYSADMIN_EMAIL}" user-promote || true


### Run server
MEMTOT=$(vmstat -s | grep 'total memory' | awk '{ print $1 }')
if [ "$MEMTOT" -gt "1100000" ]
then
  export WORKER_COUNT=4
else
  export WORKER_COUNT=1
fi
echo "using $WORKER_COUNT worker(s) based on available memory ($MEMTOT).."

echo "Starting server"
exec pm2-runtime ./pm2.config.js
