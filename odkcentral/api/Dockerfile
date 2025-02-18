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
ARG MINIO_TAG=${MINIO_TAG:-RELEASE.2024-10-13T13-34-11Z}
FROM docker.io/minio/minio:${MINIO_TAG} AS minio


FROM ghcr.io/getodk/central-service:${ODK_CENTRAL_TAG}
# Copy minio mc client to create S3 buckets
COPY --from=minio /usr/bin/mc /usr/local/bin/
COPY container-entrypoint.sh /
RUN chmod +x /container-entrypoint.sh
ENTRYPOINT ["/container-entrypoint.sh"]
HEALTHCHECK --start-period=10s --interval=5s --retries=10 \
    CMD nc -z localhost 8383 || exit 1
