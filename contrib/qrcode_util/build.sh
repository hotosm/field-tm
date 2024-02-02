#!/bin/bash

docker build . -t ghcr.io/hotosm/fmtm/qrcodes:latest

docker push ghcr.io/hotosm/fmtm/qrcodes:latest
