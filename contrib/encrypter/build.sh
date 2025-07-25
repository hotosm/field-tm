#!/bin/bash

docker build . -t ghcr.io/hotosm/field-tm/encrypter:latest

docker push ghcr.io/hotosm/field-tm/encrypter:latest
