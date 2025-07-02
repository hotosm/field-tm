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

# NOTE this dockerfile simply extends the official image
# to init an admin user at startup

ARG ODK_CENTRAL_TAG
ARG MINIO_TAG=RELEASE.2025-01-20T14-49-07Z
FROM docker.io/minio/minio:${MINIO_TAG} AS minio


# **TEMP override until PR merged
FROM ghcr.io/getodk/central-service:${ODK_CENTRAL_TAG} AS s3-sync
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "ca-certificates" \
        "git" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
WORKDIR /repo
RUN git clone --depth 1 --branch feat/s3-sync-api-2025.1.1 https://github.com/spwoodcock/central-backend.git


FROM ghcr.io/getodk/central-service:${ODK_CENTRAL_TAG}
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "ca-certificates" \
        "jq" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Copy minio mc client to create S3 buckets
COPY --from=minio /usr/bin/mc /usr/local/bin/

# Modify the S3 submission photo upload to every 15 minutes
RUN sed -i 's/^0 5 \* \* \*/\*\/15 * * * */' /etc/cron.d/odk

# **TEMP override to add s3 sync service
COPY --from=s3-sync /repo/central-backend/lib/http/service.js ./lib/http/service.js
COPY --from=s3-sync /repo/central-backend/lib/model/migrations/20250512-01-s3-sync-permission.js ./lib/model/migrations/20250512-01-s3-sync-permission.js
COPY --from=s3-sync /repo/central-backend/lib/resources/s3.js ./lib/resources/s3.js
COPY --from=s3-sync /repo/central-backend/lib/task/s3.js ./lib/task/s3.js

COPY container-entrypoint.sh /
RUN chmod +x /container-entrypoint.sh
ENTRYPOINT ["/container-entrypoint.sh"]
