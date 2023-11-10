#!/bin/bash

# Dev certs init
echo "Building proxy:certs-init-development"
docker build nginx \
    --tag "ghcr.io/hotosm/fmtm/proxy:certs-init-development" \
    --target certs-init-development \
    --build-arg NGINX_TAG="${NGINX_TAG:-1.25.2}"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:certs-init-development"
fi

# Staging certs init
echo "Tagging proxy:certs-init-staging"
docker tag "ghcr.io/hotosm/fmtm/proxy:certs-init-development" \
    "ghcr.io/hotosm/fmtm/proxy:certs-init-staging"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:certs-init-staging"
fi

# Main certs init
echo "Building proxy:certs-init-main"
docker build nginx \
    --tag "ghcr.io/hotosm/fmtm/proxy:certs-init-main" \
    --target certs-init-main \
    --build-arg NGINX_TAG="${NGINX_TAG:-1.25.2}"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:certs-init-main"
fi

# Dev proxy
echo "Building proxy:development"
docker build nginx \
    --tag "ghcr.io/hotosm/fmtm/proxy:development" \
    --target development \
    --build-arg NGINX_TAG="${NGINX_TAG:-1.25.2}"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:development"
fi

# Staging proxy
echo "Tagging proxy:staging"
docker tag "ghcr.io/hotosm/fmtm/proxy:development" \
    "ghcr.io/hotosm/fmtm/proxy:staging"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:staging"
fi

# Main proxy
echo "Building proxy:main"
docker build nginx \
    --tag "ghcr.io/hotosm/fmtm/proxy:main" \
    --target main \
    --build-arg NGINX_TAG="${NGINX_TAG:-1.25.2}"

if [[ -n "$PUSH_IMGS" ]]; then
    docker push "ghcr.io/hotosm/fmtm/proxy:main"
fi
