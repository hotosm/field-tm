#!/bin/bash

set -eo pipefail

while !</dev/tcp/${FMTM_DB_HOST:-fmtm-db}/5432;
do
    sleep 1;
done;

exec "$@"
