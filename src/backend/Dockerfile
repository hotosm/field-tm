# Copyright (c) Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
ARG PYTHON_IMG_TAG=3.12
ARG UV_IMG_TAG=0.5.2
ARG MINIO_TAG=${MINIO_TAG:-RELEASE.2024-10-13T13-34-11Z}
FROM ghcr.io/astral-sh/uv:${UV_IMG_TAG} as uv
FROM docker.io/minio/minio:${MINIO_TAG} AS minio


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
COPY pyproject.toml uv.lock /_lock/
# Ensure caching & install with or without monitoring, depending on flag
RUN --mount=type=cache,target=/root/.cache <<EOT
    uv sync \
        --project /_lock \
        --locked \
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
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "nano" \
        "curl" \
        "gettext-base" \
        "libpcre3" \
        "mime-support" \
        "postgresql-client" \
        "libglib2.0-0" \
        "libspatialindex-c6" \
        "libproj25" \
        "libgeos-c1v5" \
    && rm -rf /var/lib/apt/lists/*
# Copy minio mc client
COPY --from=minio /usr/bin/mc /usr/local/bin/
COPY *-entrypoint.sh /
ENTRYPOINT ["/app-entrypoint.sh"]
# Copy Python deps from build to runtime
COPY --from=build /opt/python /opt/python
WORKDIR /opt
# Add app code
COPY app/ /opt/app/
COPY migrations/ /opt/migrations/
# Add non-root user, permissions
RUN useradd -u 1001 -m -c "fmtm account" -d /home/appuser -s /bin/false appuser \
    && mkdir -p /opt/logs /opt/tiles \
    && chown -R appuser:appuser /opt /home/appuser \
    && chmod +x /app-entrypoint.sh /migrate-entrypoint.sh /backup-entrypoint.sh
# Add volumes for persistence
VOLUME /opt/logs
VOLUME /opt/tiles
# Change to non-root user
USER appuser


# Add certificates to use ODK Central over SSL (HTTPS, required)
FROM runtime AS add-odk-certs
USER root
# Add the SSL cert for debug odkcentral
COPY --from=ghcr.io/hotosm/fmtm/proxy:debug \
    /etc/nginx/central-fullchain.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates


# Stage to use during local development
FROM add-odk-certs AS debug
USER appuser
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /_lock/
RUN --mount=type=cache,target=/root/.cache <<EOT
    uv sync \
        --project /_lock \
        --locked \
        --no-dev \
        --no-install-project \
        --group debug \
        --group test \
        --group docs \
        --group dev
EOT
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", \
    "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:api", \
    "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
    "--reload", "--log-level", "critical", "--no-access-log"]


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
RUN python -V
    python -Im site
    python -c 'import app'
