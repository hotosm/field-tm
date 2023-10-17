#!/bin/sh

set -e

########################################
# Note: run this from the repo root.
########################################

# TODO read personal access token
# read -p
# GITHUB_TOKEN=input
# Feed to act using -s flag: -s GITHUB_TOKEN=input_personal_access_token

# PR
act pull_request -W .github/workflows/pr_test.yml \
    -e .github/workflows/tests/pr_payload.json \
    --var-file=.env --secret-file=.env

# Build and deploy
act push -W .github/workflows/build_and_deploy.yml \
    -e .github/workflows/tests/push_payload.json \
    --var-file=.env --secret-file=.env

# CI Img Build
act push -W .github/workflows/build_ci_img.yml \
    -e .github/workflows/tests/push_payload.json \
    --var-file=.env --secret-file=.env

# ODK Img Build
act push -W .github/workflows/build_odk_imgs.yml \
    -e .github/workflows/tests/push_payload.json \
    --var-file=.env --secret-file=.env

# Docs
act push -W .github/workflows/docs.yml \
    -e .github/workflows/tests/push_payload.json \
    --var-file=.env --secret-file=.env

# Wiki
act push -W .github/workflows/wiki.yml \
    -e .github/workflows/tests/push_payload.json \
    --var-file=.env --secret-file=.env
