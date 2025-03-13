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

# NOTE this dockerfile simply extends the official image
# to init an admin user at startup

ARG ODK_CENTRAL_TAG
ARG MINIO_TAG=${MINIO_TAG:-RELEASE.2025-01-20T14-49-07Z}
FROM docker.io/minio/minio:${MINIO_TAG} AS minio


FROM ghcr.io/getodk/central-service:${ODK_CENTRAL_TAG}
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --quiet --no-install-recommends \
        "ca-certificates" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Copy minio mc client to create S3 buckets
COPY --from=minio /usr/bin/mc /usr/local/bin/

# Modify the S3 submission photo upload to every 15 minutes
RUN sed -i 's/^0 5 \* \* \*/\*\/15 * * * */' /etc/cron.d/odk

# Add custom code s3-sync endpoint
# https://forum.getodk.org/t/possibility-of-an-endpoint-to-trigger-pending-uploads-to-s3/54110
COPY s3-sync/20250313-01-s3-sync-permission.js /usr/odk/lib/model/migrations/
COPY s3-sync/s3.js /usr/odk/lib/resources/
# Modify the lib/http/service.js file to include our new router
RUN sed -i "/require('\.\.\/resources\/oidc')(service, endpoint);/a \ \ require('../resources/s3')(service, endpoint);" lib/http/service.js

COPY container-entrypoint.sh /
RUN chmod +x /container-entrypoint.sh
ENTRYPOINT ["/container-entrypoint.sh"]
