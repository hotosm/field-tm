#!/bin/bash

install_envsubst_if_missing() {
    if ! command -v curl &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y curl
    fi

    echo
    # Get a8m/envsubst (required for default vals syntax ${VAR:-default})
    # Use local version, as envsubst may be installed on system already
    if [ -f ./envsubst ]; then
        echo "envsubst already exists. Continuing."
    else
        echo "Downloading a8m/envsubst"
        echo
        curl -L "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-$(uname -s)-$(uname -m)" -o envsubst
        chmod +x envsubst
    fi
}

gen_current_env() {
    # Generate a .env file from .env.example and export to the environment
    while IFS= read -r line; do
        echo "${line?}"
    done < <(./envsubst -i .env.example | grep -vE '^\s*#|^\s*$')

    # Override exported env vars with any in the .env file
    if [ -f .env ]; then
        while IFS= read -r line; do
            # Remove surrounding quotes (single or double)
            clean_line=$(echo "$line" | sed -E 's/^([^=]+)=(["'\'']?)(.*)\2$/\1=\3/')
            export "${clean_line?}"
        done < <(grep -vE '^\s*#|^\s*$' .env)
    fi

    # Generate compose file (default dev, but can be overridden)
    export GIT_BRANCH="${GIT_BRANCH:-dev}"
    echo ""
    echo "Generated compose file:"
    echo ""
    ./envsubst -i deploy/compose.sub.yaml
}

handle_favicon_override() {
    # Copy favicon to required directories, if present
    if [ -f favicon.svg ]; then
        # Pull ImageMagick container if not already present
        docker pull dpokidov/imagemagick:7.1.1-47

        # Convert SVG to PNG (32x32, aspect ratio preserved, transparent padding)
        docker run --rm -v "$PWD":/repo --workdir /repo --entrypoint=/bin/sh \
            dpokidov/imagemagick:7.1.1-47 \
            -c "magick favicon.svg -resize 32x32 -background none -gravity center -extent 32x32 favicon.png"

        # Copy to frontend and mapper static content
        cp favicon.svg src/frontend/public/favicon.svg
        cp favicon.svg src/mapper/static/favicon.svg
        cp favicon.png src/frontend/public/favicon.png
        cp favicon.png src/mapper/static/favicon.png

        # Then prevent tracking of the changes once overridden
        git update-index --assume-unchanged src/frontend/public/favicon.svg
        git update-index --assume-unchanged src/frontend/public/favicon.png
        git update-index --assume-unchanged src/mapper/static/favicon.svg
        git update-index --assume-unchanged src/mapper/static/favicon.png
    fi
}

pull_and_rebuild_frontends() {
    # Pull images (must run in a subshell to be within 'deploy' dir for ../compose.yaml extend)
    (cd deploy &&
        ../envsubst -i compose.sub.yaml | \
        docker compose -f - pull)

    handle_favicon_override

    # Rebuild frontends (required to have correct API vars)
    (export COMPOSE_BAKE=true && cd deploy &&
        ../envsubst -i compose.sub.yaml | \
        docker compose -f - build ui)
}

deploy() {
    (cd deploy &&
        ../envsubst -i compose.sub.yaml | \
        docker compose -f - up --detach \
        --remove-orphans --force-recreate)
}

install_envsubst_if_missing
gen_current_env
pull_and_rebuild_frontends
deploy
