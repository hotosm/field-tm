#!/bin/bash

set -euo pipefail

cleanup_and_exit() {
    echo
    echo "CTRL+C received, exiting..."
    exit 1
}

# Capture CTRL+C
trap cleanup_and_exit INT

# Prompt the user for input and set the BRANCH_NAME variable
read -erp "Enter the environment (dev/staging/prod): " ENVIRONMENT

case "$ENVIRONMENT" in
    dev)
        BRANCH_NAME="development"
        ;;
    staging)
        BRANCH_NAME="staging"
        ;;
    prod)
        BRANCH_NAME="main"
        ;;
    *)
        echo "Invalid environment. Please enter dev, staging, or prod."
        exit 1
        ;;
esac

# Check if any containers using the 'ghcr.io/hotosm/fmtm/proxy:${BRANCH_NAME}' image are running
if [[ -z $(docker ps -q -f "ancestor=ghcr.io/hotosm/fmtm/proxy:${BRANCH_NAME}") ]]; then
    echo "No containers using the 'ghcr.io/hotosm/fmtm/proxy:${BRANCH_NAME}' image are running."
    echo "You must first start the containers using:"
    echo
    echo "docker-compose -f deploy/compose.${BRANCH_NAME}.yaml up -d"
    echo
    exit 1
fi

# Execute the Docker Compose command with the determined BRANCH_NAME
docker compose exec "fmtm-$BRANCH_NAME" certbot --non-interactive renew
