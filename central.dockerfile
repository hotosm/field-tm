# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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
FROM docker.io/bitnami/git:2 as repo
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        "jq" \
    && rm -rf /var/lib/apt/lists/*
ARG ODK_CENTRAL_VERSION=v2023.1.0
RUN git clone --depth 1 --branch ${ODK_CENTRAL_VERSION} \
    "https://github.com/getodk/central.git" \
    && cd central && git submodule update --init
RUN tmp=$(mktemp) \
    && jq '.default.database.host = "central-db"' \
    central/files/service/config.json.template > \
    "$tmp" && mv "$tmp" central/files/service/config.json.template




FROM docker.io/node:16.17.0

WORKDIR /usr/odk

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(grep -oP 'VERSION_CODENAME=\K\w+' /etc/os-release)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list; \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg; \
    apt-get update; \
    apt-get install -y cron gettext postgresql-client-9.6

COPY --from=repo central/files/service/crontab /etc/cron.d/odk

COPY --from=repo central/server/package*.json ./

RUN npm clean-install --omit=dev --legacy-peer-deps --no-audit --fund=false --update-notifier=false
RUN npm install pm2@5.2.0 -g

COPY --from=repo central/server/ ./
COPY --from=repo central/files/service/scripts/ ./
COPY --from=repo central/files/service/pm2.config.js ./

COPY --from=repo central/files/service/config.json.template /usr/share/odk/
COPY --from=repo central/files/service/odk-cmd /usr/bin/

# Required to start via entrypoint
RUN mkdir /etc/secrets sentry-versions \
    && echo 'jhs9udhy987gyds98gfyds98f' > /etc/secrets/enketo-api-key \
    && echo '1' > sentry-versions/server \
    && echo '1' > sentry-versions/central \
    && echo '1' > sentry-versions/client

EXPOSE 8383