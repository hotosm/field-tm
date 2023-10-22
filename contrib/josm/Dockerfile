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

FROM docker.io/debian:bookworm as base
ARG MAINTAINER=admin@hotosm.org
LABEL org.hotosm.fmtm.maintainer="${MAINTAINER}" \
      org.hotosm.fmtm.josm-port="8111" \
      org.hotosm.fmtm.nginx-port="80"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends "locales" "ca-certificates" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



FROM base as gpg-key
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "curl" \
        "gnupg2" \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sS https://josm.openstreetmap.de/josm-apt.key \
    | gpg --dearmor | tee /opt/josm.gpg



FROM base as runtime
COPY --from=gpg-key \
    /opt/josm.gpg /etc/apt/trusted.gpg.d/josm.gpg
RUN echo \
    "deb [arch=$(dpkg --print-architecture) \
    signed-by=/etc/apt/trusted.gpg.d/josm.gpg] \
    https://josm.openstreetmap.de/apt alldist universe" \ 
    | tee /etc/apt/sources.list.d/josm.list > /dev/null
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "gosu" \
        "josm" \
        "nginx" \
    && rm -rf /var/lib/apt/lists/*
COPY container-entrypoint.sh /container-entrypoint.sh
# Add non-root user
RUN useradd --system -r -u 101 -m -c "nginx user" \
    -d /home/nginx -s /bin/false nginx \
    && chmod +x /container-entrypoint.sh
COPY --chown=nginx \
    preferences.xml /home/nginx/.config/JOSM/preferences.xml
# Replace default nginx config
COPY --chown=nginx \
    nginx-josm.conf /etc/nginx/sites-enabled/default
# Run as root, change to nginx user in entrypoint
ENTRYPOINT ["/container-entrypoint.sh"]
