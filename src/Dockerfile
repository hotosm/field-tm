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
ARG PYTHON_IMG_TAG=3.13
ARG UV_IMG_TAG=0.10.6
FROM ghcr.io/astral-sh/uv:${UV_IMG_TAG} AS uv
FROM ghcr.io/hotosm/lightningcss:1.31.1 AS lightningcss


# Includes all labels and timezone info to extend from
FROM docker.io/python:${PYTHON_IMG_TAG}-slim-trixie AS base
ARG APP_VERSION
ARG COMMIT_REF
ARG PYTHON_IMG_TAG
LABEL org.hotosm.field-tm.app-name="backend" \
      org.hotosm.field-tm.app-version="${APP_VERSION}" \
      org.hotosm.field-tm.git-commit-ref="${COMMIT_REF:-none}" \
      org.hotosm.field-tm.python-img-tag="${PYTHON_IMG_TAG}" \
      org.hotosm.field-tm.maintainer="sysadmin@hotosm.org" \
      org.hotosm.field-tm.api-port="8000"
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
# - select system python version,
# - declare `/opt/python` as the target for `uv sync` (i.e. instead of .venv).
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON="python$PYTHON_IMG_TAG" \
    UV_PROJECT_ENVIRONMENT=/opt/python
STOPSIGNAL SIGINT


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
        "libpcre2-dev" \
        "libpq-dev" \
        "libspatialindex-dev" \
        "libproj-dev" \
        "libgeos-dev" \
        "git" \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /usr/local/bin/uv
RUN mkdir -p /_lock
# Install third-party deps first (workspace members excluded) for better cache hits.
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/pyproject.toml,target=/_lock/pyproject.toml \
    --mount=type=bind,source=backend/uv.lock,target=/_lock/uv.lock <<EOT
    UV_CACHE_DIR=/root/.cache/uv uv sync \
        --project /_lock \
        --frozen \
        --no-editable \
        --no-dev \
        --no-install-workspace \
    $(if [ -z "$MONITORING" ]; then \
        echo ""; \
    else \
        echo "--group monitoring"; \
    fi)
EOT
COPY backend/pyproject.toml backend/uv.lock /_lock/
COPY backend/packages /_lock/packages
# Install workspace members without reinstalling the project package.
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv <<EOT
    UV_CACHE_DIR=/root/.cache/uv uv sync \
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


# Runtime base stage with all shared dependencies and entrypoints
FROM base AS runtime-base
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
# - gettext: msgfmt util for compiling gettext catalogs
# - gettext-base: envsubst util for dotenv substitution
# - postgresql-client: pg_isready util for healthchecks
# - mime-support: web mimetype support
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "nano" \
        "curl" \
        "procps" \
        "gettext" \
        "gettext-base" \
        "libpcre2-16-0" \
        "media-types" \
        "libpq5" \
        "postgresql-client" \
        "libglib2.0-0t64" \
        "libspatialindex-c8" \
        "libproj25" \
        "libgeos-c1t64" \
    # Enable to install a specific version of Postgresql client tools
    # && yes '' | /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh \
    # && DEBIAN_FRONTEND=noninteractive \
    #    apt-get install -y --quiet --no-install-recommends \
    #    "postgresql-client-17" \
    && rm -rf /var/lib/apt/lists/*
COPY ./*-entrypoint.sh /
ENTRYPOINT ["/app-entrypoint.sh"]
# Copy Python deps from build to runtime base
COPY --from=build /opt/python /opt/python
WORKDIR /opt
# Add non-root user, permissions
RUN useradd -u 1001 -m -c "field-tm account" -d /home/appuser -s /bin/false appuser \
    && mkdir -p /opt/logs /opt/migrations /opt/app \
    && chown -R appuser:appuser /opt /home/appuser \
    && chmod +x /app-entrypoint.sh /migrate-entrypoint.sh
# Add volumes for persistence
VOLUME /opt/logs
# Change to non-root user
USER appuser


# Runtime stage with app code, used for deployment
FROM runtime-base AS runtime
COPY --chown=appuser:appuser migrations/ /opt/migrations/
COPY --chown=appuser:appuser backend/app/ /opt/app/
RUN find /opt/app/locales -path '*/LC_MESSAGES/*.po' \
    -exec sh -c 'msgfmt "$1" -o "${1%.po}.mo"' _ {} \;


# Stage to use during local development
FROM runtime-base AS debug
USER root
COPY --from=uv /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock /_lock/
COPY backend/packages /_lock/packages
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv <<EOT
    UV_CACHE_DIR=/root/.cache/uv uv sync \
        --project /_lock \
        --locked \
        --no-editable \
        --no-install-project \
        --group debug \
        --group test \
        --group docs \
        --group dev
EOT
# As we rebuilt before running the tests anyway, just copy all the files in
COPY --chown=appuser:appuser migrations/ /opt/migrations/
COPY --chown=appuser:appuser backend/app/ /opt/app/
RUN find /opt/app/locales -path '*/LC_MESSAGES/*.po' \
    -exec sh -c 'msgfmt "$1" -o "${1%.po}.mo"' _ {} \;
COPY --chown=appuser:appuser backend/pyproject.toml /opt/pyproject.toml
COPY --chown=appuser:appuser backend/tests/ /opt/tests/
# We move the package tests for easier pytest discovery
COPY --chown=appuser:appuser backend/packages/osm-fieldwork/tests/ /opt/package_tests/test_osm_fieldwork/
COPY --chown=appuser:appuser backend/packages/area-splitter/tests/ /opt/package_tests/test_area_splitter/
USER appuser
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", \
    "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:api", \
    "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
    "--reload", "--reload-dir", "app", "--reload-dir", "tests", \
    "--log-level", "critical", "--no-access-log"]


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


# Minify CSS as we don't use a bundler
FROM runtime AS css
COPY --from=lightningcss /usr/local/bin/lightningcss /usr/local/bin
RUN lightningcss --minify /opt/app/static/css/app.css -o /opt/app/static/css/app.css


# Final stage used during deployment
FROM runtime AS prod
# Add minified CSS
COPY --from=css /opt/app/static/css/app.css /opt/app/static/css/app.css
# Note: 1 worker (process) per container, behind load balancer
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "1", "--log-level", "critical", "--no-access-log"]
# Sanity check to see if build succeeded
RUN python -V \
    && python -Im site \
    && python -c 'import app'
