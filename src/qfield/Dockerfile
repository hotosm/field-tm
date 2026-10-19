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
      # Pinned to master SHAs (the old `#use_tabs_imp` fragment was ignored by pip)
      git+https://github.com/opengisch/xlsform2qgis.git@f7fdecc1a0c0249aa56b2258158bd234f7e85010 \
      git+https://github.com/opengisch/libqfieldsync.git@aad2ea69b21b72209db1df5be54c25138a32048f \
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
    && mkdir -p /tmp/qgis_jobs /usr/src/app/packager \
    && chown qgis:qgis /tmp/qgis_jobs
COPY --from=build /usr/local/lib /usr/local/lib
COPY *.py /usr/src/app/packager/
USER qgis
CMD ["python3", "/usr/src/app/packager/server.py"]
