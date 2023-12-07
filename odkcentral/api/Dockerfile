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



FROM docker.io/node:${node_version}-slim

WORKDIR /usr/odk

COPY --from=repo central/files/service/crontab /etc/cron.d/odk
COPY --from=repo central/files/service/scripts/ ./
COPY --from=repo central/files/service/config.json.template /usr/share/odk/
COPY --from=repo central/files/service/odk-cmd /usr/bin/
# Add entrypoint script to init user
COPY init-user-and-start.sh /
# package.json must be added and installed prior to final COPY
COPY --from=repo central/server/package*.json ./

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gpg \
        cron \
        wait-for-it \
        gettext \
        procps \
        postgresql-client \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    # Install node_modules
    && npm clean-install --omit=dev --legacy-peer-deps --no-audit \
        --fund=false --update-notifier=false \
    # Required to start via entrypoint
    && mkdir /etc/secrets sentry-versions \
    && echo 'jhs9udhy987gyds98gfyds98f' > /etc/secrets/enketo-api-key \
    && echo '1' > sentry-versions/server \
    && echo '1' > sentry-versions/central \
    && echo '1' > sentry-versions/client \
    # Set entrypoint executable
    && chmod +x /init-user-and-start.sh

# Add remaining files after deps installed
COPY --from=repo central/server/ ./

ENTRYPOINT ["/init-user-and-start.sh"]
EXPOSE 8383

# Add Healthcheck
HEALTHCHECK --start-period=10s --interval=5s --retries=10 \
    CMD nc -z localhost 8383 || exit 1
