ARG QFIELDCLOUD_TAG=26.3
FROM ghcr.io/opengisch/qfieldcloud-qgis:${QFIELDCLOUD_TAG} AS build
USER root
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "build-essential" \
        "gcc" \
        "libpq-dev" \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-warn-script-location --break-system-packages \
      --no-cache-dir \
      git+https://github.com/opengisch/xlsform2qgis.git \
      psycopg[c]


FROM ghcr.io/opengisch/qfieldcloud-qgis:${QFIELDCLOUD_TAG} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1
# libpq5 is required at runtime by psycopg's C extension
USER root
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends "libpq5" \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 1001 -m -s /bin/false qgis \
    && mkdir -p /tmp/qgis_jobs && chown qgis:qgis /tmp/qgis_jobs
COPY --from=build /usr/local/lib /usr/local/lib
COPY project_gen_svc.py /usr/src/app/
USER qgis
CMD ["python3", "/usr/src/app/project_gen_svc.py"]
