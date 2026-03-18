#!/bin/bash

docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/hotosm/lightningcss:1.31.1 --push .
