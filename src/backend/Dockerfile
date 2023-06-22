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
ARG PYTHON_IMG_TAG=3.10

FROM docker.io/python:${PYTHON_IMG_TAG}-slim-bullseye as base
ARG APP_VERSION
ARG PYTHON_IMG_TAG
ARG MAINTAINER=admin@hotosm.org
LABEL org.hotosm.fmtm.app-version="${APP_VERSION}" \
      org.hotosm.fmtm.python-img-tag="${PYTHON_IMG_TAG}" \
      org.hotosm.fmtm.maintainer="${MAINTAINER}" \
      org.hotosm.fmtm.api-port="8000"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends "locales" "ca-certificates" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



FROM base as extract-deps
WORKDIR /opt/python
COPY pyproject.toml pdm.lock /opt/python/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir pdm==2.6.1
RUN pdm export --prod > requirements.txt \
    && pdm export --dev --no-default > requirements-dev.txt 



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
COPY --from=extract-deps \
    /opt/python/requirements.txt /opt/python/
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
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/* 
COPY --from=build \
    /root/.local \
    /home/appuser/.local
WORKDIR /opt
COPY . /opt/
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
    && chown -R appuser:appuser /opt /home/appuser



FROM runtime as debug-no-odk
COPY --from=extract-deps \
    /opt/python/requirements-dev.txt /opt/python/
RUN pip install --no-warn-script-location \
    --no-cache-dir -r /opt/python/requirements-dev.txt 

RUN pip install osm-fieldwork==0.3.1

USER appuser
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", \
    "-m", "uvicorn", "app.main:api", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--reload", "--log-level", "error", "--no-access-log"]



FROM debug-no-odk as debug-with-odk
# Add the SSL cert for debug odkcentral
USER root
COPY --from=ghcr.io/hotosm/fmtm/odkcentral-proxy:latest \
    /etc/nginx/ca.crt /etc/nginx/central.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
USER appuser


FROM runtime as prod
USER appuser
# Note: 4 uvicorn workers as running with docker, change to 1 worker for Kubernetes
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "4", "--log-level", "error", "--no-access-log"]
# Pre-compile packages to .pyc (init speed gains)
RUN python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
