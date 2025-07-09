# Copyright (c) Humanitarian OpenStreetMap Team
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
ARG PYTHON_IMG_TAG=3.12
ARG UV_IMG_TAG=0.5.2
ARG MINIO_TAG=RELEASE.2025-01-20T14-49-07Z
FROM ghcr.io/astral-sh/uv:${UV_IMG_TAG} AS uv
FROM docker.io/minio/minio:${MINIO_TAG} AS minio
FROM ghcr.io/hotosm/field-tm/basemap-generator:0.4.0 AS basemap-bins


# Includes all labels and timezone info to extend from
FROM docker.io/python:${PYTHON_IMG_TAG}-slim-bookworm AS base
ARG APP_VERSION
ARG COMMIT_REF
ARG PYTHON_IMG_TAG
LABEL org.hotosm.fmtm.app-name="backend" \
      org.hotosm.fmtm.app-version="${APP_VERSION}" \
      org.hotosm.fmtm.git-commit-ref="${COMMIT_REF:-none}" \
      org.hotosm.fmtm.python-img-tag="${PYTHON_IMG_TAG}" \
      org.hotosm.fmtm.maintainer="sysadmin@hotosm.org" \
      org.hotosm.fmtm.api-port="8000"
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "locales" "ca-certificates" "curl" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Set locale & env vars
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - use a temp dir instead of cache during install,
# - select system python version,
# - declare `/opt/python` as the target for `uv sync` (i.e. instead of .venv).
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_PYTHON="python$PYTHON_IMG_TAG" \
    UV_PROJECT_ENVIRONMENT=/opt/python
STOPSIGNAL SIGINT


# Get supercronic binary for userland scheduling (cron daemon needs root)
FROM base AS supercronic
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8 \
    SUPERCRONIC=supercronic-linux-amd64
RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" /supercronic


# Build stage will all dependencies required to build Python wheels
FROM base AS build
# NOTE the MONITORING argument is specified during production build on Github workflow
# NOTE only the production API image contains the monitoring dependencies
ARG MONITORING
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "build-essential" \
        "gcc" \
        "libpcre3-dev" \
        "libpq-dev" \
        "libspatialindex-dev" \
        "libproj-dev" \
        "libgeos-dev" \
        "git" \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock /_lock/
COPY backend/packages /_lock/packages
# Ensure caching & install with or without monitoring, depending on flag
RUN --mount=type=cache,target=/root/.cache <<EOT
    uv sync \
        --project /_lock \
        --locked \
        --no-editable \
        --no-dev \
        --no-install-project \
    $(if [ -z "$MONITORING" ]; then \
        echo ""; \
    else \
        echo "--group monitoring"; \
    fi)
EOT


# Run stage will minimal dependencies required to run Python libraries
FROM base AS runtime
ARG PYTHON_IMG_TAG
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/python/bin:$PATH" \
    PYTHONPATH="/opt" \
    PYTHON_LIB="/opt/python/lib/python$PYTHON_IMG_TAG/site-packages" \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# Packages:
# - procps: pgrep util for heathchecks
# - gettext-base: envsubst util for dotenv substitution
# - postgresql-client: pg_isready util for healthchecks
# - mime-support: web mimetype support
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "nano" \
        "curl" \
        "procps" \
        "gettext-base" \
        "libpcre3" \
        "mime-support" \
        "postgresql-common" \
        "libglib2.0-0" \
        "libspatialindex-c6" \
        "libproj25" \
        "libgeos-c1v5" \
    # Temp until Debian supports Postgres v16 by default
    && yes '' | /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh \
    && DEBIAN_FRONTEND=noninteractive \
       apt-get install -y --quiet --no-install-recommends \
       "postgresql-client-17" \
    && rm -rf /var/lib/apt/lists/*
# Copy minio mc client
COPY --from=minio /usr/bin/mc /usr/local/bin/
# Copy basemap generation binaries
COPY --from=basemap-bins /usr/bin/tilepack /usr/local/bin/
COPY --from=basemap-bins /usr/bin/pmtiles /usr/local/bin/
COPY --from=supercronic /supercronic /usr/local/bin/
COPY backend/*-entrypoint.sh /
ENTRYPOINT ["/app-entrypoint.sh"]
# Copy Python deps from build to runtime
COPY --from=build /opt/python /opt/python
WORKDIR /opt
# Add app code
COPY migrations/ /opt/migrations/
COPY backend/app/ /opt/app/
COPY backend/stats/ /opt/stats/
COPY backend/scheduler/ /opt/scheduler/
# Add non-root user, permissions
RUN useradd -u 1001 -m -c "fmtm account" -d /home/appuser -s /bin/false appuser \
    && mkdir -p /opt/logs \
    && chown -R appuser:appuser /opt /home/appuser \
    && chmod +x /app-entrypoint.sh /migrate-entrypoint.sh /backup-entrypoint.sh /opt/scheduler/*.py
# Add log volume for persistence
VOLUME /opt/logs
# Change to non-root user
USER appuser


# Add certificates to use ODK Central over SSL (HTTPS, required)
FROM runtime AS add-odk-certs
USER root
# Add the SSL cert for local odkcentral install (debugging only)
RUN echo 'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUI5RENDQVhtZ0F3SUJBZ0lVWXFyb\
0dWRVdsK204eU9OY2pUU2pCWThkckN3d0NnWUlLb1pJemowRUF3SXcKRlRFVE1CRUdBMVVFQXd3S2Iy\
UnJZMlZ1ZEhKaGJEQWdGdzB5TkRBM01qTXhNakF6TVRWYUdBOHlNVEkwTURZeQpPVEV5TURNeE5Wb3d\
GVEVUTUJFR0ExVUVBd3dLYjJSclkyVnVkSEpoYkRCMk1CQUdCeXFHU000OUFnRUdCU3VCCkJBQWlBMk\
lBQktSZmpOQVFzWUI0ekNXckdETHdKNEVIRDRTNW5rL1Z3aG00TmYwN203c0RTai9RTzlYK0JnNjIKe\
WlMbWVzT1ZMRExHRklpZXZ2aHIrZkxNY0YwUDQwN0FWKytER1o5bXZ6VmNwMVdZMlE5NllpTVVuelM3\
MWx0RQo4K3BXbFBmanRLT0JoekNCaERBZEJnTlZIUTRFRmdRVWNVekZsNUpWN1dUM045VUhxbmhSRHl\
WT3ZjY3dId1lEClZSMGpCQmd3Rm9BVWNVekZsNUpWN1dUM045VUhxbmhSRHlWT3ZjY3dEd1lEVlIwVE\
FRSC9CQVV3QXdFQi96QXgKQmdOVkhSRUVLakFvZ2dwdlpHdGpaVzUwY21Gc2doUXFMbTlrYXk1bWJYU\
nRMbXh2WTJGc2FHOXpkSWNFQ2hRZQpNakFLQmdncWhrak9QUVFEQWdOcEFEQm1BakVBb2xuOGRubmlQ\
N0dKSEJPQW4rTHVCV0ZhaUY1NHFZRmpTYyt1Clpia1cwY1pyNWw2VnZ6WVlBdGdWbUtOdTB5WWRBakV\
BMWlvT2JRTERYdDV3S1JPWjV5VUtmbys2T21IbTV1NWkKQU5LUHd2MExqc2ZIYk5hbzJMWnduK0VxTj\
NtdUpPNXEKLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=' \
| base64 -d > /usr/local/share/ca-certificates/central.crt
RUN update-ca-certificates


# Stage to use during local development
FROM add-odk-certs AS debug
USER appuser
COPY --from=uv /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock /_lock/
COPY backend/packages /_lock/packages
RUN --mount=type=cache,target=/root/.cache <<EOT
    uv sync \
        --project /_lock \
        --locked \
        --no-editable \
        --no-install-project \
        --group debug \
        --group test \
        --group docs \
        --group dev
EOT
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", \
    "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:api", \
    "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
    "--reload", "--reload-dir", "app", "--reload-dir", "tests", \
    "--reload-dir", "scheduler", "--reload-dir", "stats", "--log-level", \
    "critical", "--no-access-log"]


# Used during CI workflows (as root), with docs/test dependencies pre-installed
FROM debug AS ci
USER root
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "git" \
    && rm -rf /var/lib/apt/lists/*
# Override entrypoint, as not possible in Github action
ENTRYPOINT []
CMD ["sleep", "infinity"]


# Final stage used during deployment
FROM runtime AS prod
# Note: 1 worker (process) per container, behind load balancer
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "1", "--log-level", "critical", "--no-access-log"]
# Sanity check to see if build succeeded
RUN python -V \
    && python -Im site \
    && python -c 'import app'
