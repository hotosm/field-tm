#!/bin/bash

set -eo pipefail

docker build \
    -t ghcr.io/hotosm/fmtm/backend:ci \
    --target ci \
    --build-arg APP_VERSION=ci \
    ./src/backend

docker push ghcr.io/hotosm/fmtm/backend:ci
