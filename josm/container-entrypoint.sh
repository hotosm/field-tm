#!/bin/bash

# Start JOSM as nginx (unpriv) user
gosu nginx josm &

exec nginx -g "daemon off;"
