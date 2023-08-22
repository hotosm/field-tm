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

ARG node_version=16.19.1



FROM docker.io/bitnami/git:2 as repo
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        "jq" \
    && rm -rf /var/lib/apt/lists/*
ARG ODK_CENTRAL_VERSION=${ODK_CENTRAL_VERSION}
RUN git clone --depth 1 --branch ${ODK_CENTRAL_VERSION} \
    "https://github.com/getodk/central.git" \
    && cd central && git submodule update --init



FROM docker.io/node:${node_version}

WORKDIR /usr/odk

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(grep -oP 'VERSION_CODENAME=\K\w+' /etc/os-release)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list && \
  curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg && \
  apt-get update && \
  apt-get install -y cron gettext postgresql-client-14

COPY --from=repo central/files/service/crontab /etc/cron.d/odk

COPY --from=repo central/server/package*.json ./

RUN npm clean-install --omit=dev --legacy-peer-deps --no-audit --fund=false --update-notifier=false
RUN npm install pm2@5.2.2 -g

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

# Add entrypoint script to init user
COPY ./init-user-and-start.sh ./
RUN chmod +x ./init-user-and-start.sh
CMD ["./wait-for-it.sh", "central-db:5432", \
    "--", "./init-user-and-start.sh"]

EXPOSE 8383
