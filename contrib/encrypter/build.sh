#!/bin/bash

docker build . -t ghcr.io/hotosm/fmtm/encrypter:latest

docker push ghcr.io/hotosm/fmtm/encrypter:latest
