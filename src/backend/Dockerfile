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
ARG MINIO_TAG=${MINIO_TAG:-RELEASE.2023-10-25T06-33-25Z}
FROM docker.io/minio/minio:${MINIO_TAG} as minio



FROM docker.io/python:${PYTHON_IMG_TAG}-slim-bookworm as base
ARG APP_VERSION
ARG COMMIT_REF
ARG PYTHON_IMG_TAG
LABEL org.hotosm.fmtm.app-name="backend" \
      org.hotosm.fmtm.app-version="${APP_VERSION}" \
      org.hotosm.fmtm.git-commit-ref="${COMMIT_REF:-none}" \
      org.hotosm.fmtm.python-img-tag="${PYTHON_IMG_TAG}" \
      org.hotosm.fmtm.maintainer="sysadmin@hotosm.org" \
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
    && pdm export -G debug --no-default \
    --without-hashes > requirements-debug.txt \
    && pdm export -G test -G docs --no-default \
    --without-hashes > requirements-ci.txt



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
    PYTHONPATH="/opt" \
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
        "libproj25" \
        "libgeos-c1v5" \
    && rm -rf /var/lib/apt/lists/*
# Copy minio mc client
COPY --from=minio /opt/bin/mc /usr/local/bin/
COPY *-entrypoint.sh /
ENTRYPOINT ["/app-entrypoint.sh"]
# Copy Python deps from build to runtime
COPY --from=build \
    /root/.local \
    /home/appuser/.local
WORKDIR /opt
# Add app code
COPY app/ /opt/app/
COPY migrations/ /opt/migrations/
# Add non-root user, permissions
RUN useradd -u 1001 -m -c "hotosm account" -d /home/appuser -s /bin/false appuser \
    && mkdir -p /opt/logs /opt/tiles \
    && chown -R appuser:appuser /opt /home/appuser \
    && chmod +x /app-entrypoint.sh /migrate-entrypoint.sh /backup-entrypoint.sh
# Add volumes for persistence
VOLUME /opt/logs
VOLUME /opt/tiles
# Change to non-root user
USER appuser
# Add Healthcheck
HEALTHCHECK --start-period=10s --interval=5s --retries=20 --timeout=5s \
    CMD curl --fail http://localhost:8000 || exit 1



FROM runtime as add-odk-certs
USER root
# Add the SSL cert for debug odkcentral
COPY --from=ghcr.io/hotosm/fmtm/proxy:debug \
    /etc/nginx/central-fullchain.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
USER appuser



FROM add-odk-certs as debug
COPY --from=extract-deps --chown=appuser \
    /opt/python/requirements-debug.txt \
    /opt/python/requirements-ci.txt \
    /opt/python/
RUN pip install --user --upgrade --no-warn-script-location \
    --no-cache-dir \
    -r /opt/python/requirements-debug.txt \
    -r /opt/python/requirements-ci.txt \
    && rm -r /opt/python
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", \
    "-m", "uvicorn", "app.main:api", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--reload", "--log-level", "critical", "--no-access-log"]



FROM add-odk-certs as ci
# Run all ci as root
USER root
ARG PYTHON_IMG_TAG
COPY --from=extract-deps \
    /opt/python/requirements-ci.txt /opt/python/
# Copy packages from user to root dirs (run ci as root)
RUN mv /home/appuser/.local/bin/* /usr/local/bin/ \
    && mv /home/appuser/.local/lib/python${PYTHON_IMG_TAG}/site-packages/* \
    /usr/local/lib/python${PYTHON_IMG_TAG}/site-packages/ \
    && set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "git" \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade --no-warn-script-location \
    --no-cache-dir -r \
    /opt/python/requirements-ci.txt \
    && rm -r /opt/python \
    # Pre-compile packages to .pyc (init speed gains)
    && python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
# Override entrypoint, as not possible in Github action
ENTRYPOINT []
CMD ["sleep", "infinity"]



FROM runtime as prod
# Pre-compile packages to .pyc (init speed gains)
RUN python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
# Note: 4 uvicorn workers as running with docker, change to 1 worker for Kubernetes
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "4", "--log-level", "critical", "--no-access-log"]
