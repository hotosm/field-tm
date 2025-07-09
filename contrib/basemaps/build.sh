#!/bin/bash

IMAGE_NAME=ghcr.io/hotosm/field-tm/basemap-generator:0.4.0

echo "Building ${IMAGE_NAME}"
docker build . --tag "${IMAGE_NAME}"

if [[ -n "$PUSH_IMG" ]]; then
    docker push "${IMAGE_NAME}"
fi
