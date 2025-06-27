#!/bin/bash

docker build . -t ghcr.io/hotosm/field-tm/qrcodes:latest

docker push ghcr.io/hotosm/field-tm/qrcodes:latest
