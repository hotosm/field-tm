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

# An image to copy the built ODK Central dist into an rclone
# container for copying to nginx at runtime

ARG ODK_CENTRAL_TAG
FROM ghcr.io/getodk/central-nginx:v2025.2.0 AS frontend


FROM docker.io/rclone/rclone:1 AS prod
ARG ODK_CENTRAL_TAG
# Disable OIDC when we generate client config json below
ENV OIDC_ENABLED="false"
VOLUME /frontend
WORKDIR /app
COPY container-entrypoint.sh /
RUN apk add --no-cache envsubst \
    && chmod +x /container-entrypoint.sh
ADD https://raw.githubusercontent.com/getodk/central/${ODK_CENTRAL_TAG}/files/nginx/client-config.json.template .
# See https://github.com/getodk/central/blob/2d95a612218e7c73ee8b3e715749401f08fc00ac/files/nginx/setup-odk.sh#L10
RUN envsubst < ./client-config.json.template > ./client-config.json \
    && rm ./client-config.json.template
COPY --from=frontend /usr/share/nginx/html .
ENTRYPOINT ["/container-entrypoint.sh"]
