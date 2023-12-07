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

ARG node_version=18.17



FROM docker.io/bitnami/git:2 as repo
ARG ODK_CENTRAL_TAG
RUN git clone --depth 1 --branch ${ODK_CENTRAL_TAG} \
    "https://github.com/getodk/central.git" \
    && cd central && git submodule update --init



FROM docker.io/node:${node_version}-slim as build
WORKDIR /frontend
COPY --from=repo central/client/ /frontend/
RUN npm ci --no-audit --fund=false --update-notifier=false
RUN VUE_APP_OIDC_ENABLED="false" npm run build



FROM docker.io/rclone/rclone:1.64 as prod
VOLUME /frontend
COPY container-entrypoint.sh /
RUN chmod +x /container-entrypoint.sh
ENTRYPOINT ["/container-entrypoint.sh"]
WORKDIR /app
COPY --from=build /frontend/dist .
