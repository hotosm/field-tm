#!/bin/bash

set -eo pipefail

docker build --push \
    -t ghcr.io/hotosm/fmtm/backend:ci \
    --target ci \
    --build-arg APP_VERSION=ci \
    ./src/backend
