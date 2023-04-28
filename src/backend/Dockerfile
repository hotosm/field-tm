# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
ARG PYTHON_IMG_TAG=3.9

FROM docker.io/python:${PYTHON_IMG_TAG}-slim-bullseye as base
ARG APP_VERSION=0.1.0
ARG PYTHON_IMG_TAG
ARG MAINTAINER=admin@hotosm.org
LABEL fmtm.hotosm.org.app-version="${APP_VERSION}" \
    fmtm.hotosm.org.python-img-tag="${PYTHON_IMG_TAG}" \
    fmtm.hotosm.org.maintainer="${MAINTAINER}" \
    fmtm.hotosm.org.api-port="8000"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends locales \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



FROM base as build
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "build-essential" \
        "gcc" \
        "libpcre3-dev" \
        "libpq-dev" \
        "libspatialindex-dev" \
        "libproj-dev" \
        "libgeos-dev" \
        # libgdal-dev \
        "git" \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /opt/python/
RUN pip install --user --no-warn-script-location \
    --no-cache-dir -r /opt/python/requirements.txt



FROM base as runtime
ARG PYTHON_IMG_TAG
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    PYTHON_LIB="/home/appuser/.local/lib/python$PYTHON_IMG_TAG/site-packages" \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY --from=ghcr.io/hotosm/fmtm/odkcentral-proxy:latest \
    /etc/nginx/central-cert.pem /usr/local/share/ca-certificates/central.crt
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "ca-certificates" \
        "nano" \
        "curl" \
        "libpcre3" \
        "mime-support" \
        "postgresql-client" \
        "libglib2.0-0" \
        "libspatialindex-c6" \
        "libproj19" \
        "libgeos-c1v5" \
        # "libgdal32" \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
COPY --from=build \
    /root/.local \
    /home/appuser/.local
WORKDIR /app
COPY . /app/backend
# ENTRYPOINT bash script to check db is ready
ARG FMTM_DB_HOST
RUN printf '#!/bin/bash\n\
    set -eo pipefail\n\
    while !</dev/tcp/${FMTM_DB_HOST:-fmtm-db}/5432; do sleep 1; done;\n\
    exec "$@"'\
    >> /docker-entrypoint.sh \
    && chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
# Add non-root user, permissions
RUN useradd -r -u 900 -m -c "hotosm account" -d /home/appuser -s /bin/false appuser \
    && chown -R appuser:appuser /app /home/appuser
USER appuser



FROM runtime as debug
RUN pip install --user --no-warn-script-location \
    --no-cache-dir -r ./backend/requirements-dev.txt
CMD ["python", "-m", "debugpy", "--wait-for-client", "--listen", \
    "0.0.0.0:5678", "-m", "uvicorn", "backend.main:api", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--reload", "--log-level", "error", "--no-access-log"]



FROM runtime as prod
# Pre-compile packages to .pyc (init speed gains)
RUN python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
CMD ["uvicorn", "backend.main:api", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "1", "--reload", "--log-level", "error", "--no-access-log"]
    