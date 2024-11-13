# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
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
ARG NGINX_TAG


FROM docker.io/nginx:${NGINX_TAG}-bookworm as brotli-module
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
          "wget" \
          "git" \
          "build-essential" \
          "libpcre3-dev" \
          "zlib1g-dev" \
          "libssl-dev" \
          "libgd-dev" \
          "libxml2-dev" \
          "uuid-dev" \
          "libxslt-dev" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
ARG NGINX_TAG
RUN wget "http://nginx.org/download/nginx-${NGINX_TAG}.tar.gz" \
    && tar -xzvf "nginx-${NGINX_TAG}.tar.gz"
RUN git clone https://github.com/google/ngx_brotli.git --recursive
RUN CONFARGS=$(nginx -V 2>&1 | sed -n -e 's/^.*arguments: //p') \
    && cd "nginx-${NGINX_TAG}" \
    && ./configure --with-compat "${CONFARGS}" \
       --add-dynamic-module=../ngx_brotli \
    && make modules \
    && mv objs/ngx_http_brotli_filter_module.so \
       objs/ngx_http_brotli_static_module.so /



FROM docker.io/nginx:${NGINX_TAG}-bookworm as base
ARG NGINX_TAG
ARG GIT_COMMIT
LABEL org.hotosm.fmtm.app-name="proxy" \
      org.hotosm.fmtm.app-version="${NGINX_TAG}" \
      org.hotosm.fmtm.git-commit-ref="${COMMIT_REF:-none}" \
      org.hotosm.fmtm.maintainer="sysadmin@hotosm.org"
# Install certbot, netcat
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
          "netcat-traditional" \
          "certbot" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
# Add modules
COPY --from=brotli-module \
     /ngx_http_brotli_filter_module.so \
     /ngx_http_brotli_static_module.so \
     /usr/lib/nginx/modules/
WORKDIR /usr/share/nginx/html
# Remove default Nginx static assets
RUN rm -rf ./* /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf
COPY nginx.conf \
     options-ssl-nginx.conf \
     options-security.conf \
     certs/ssl-dhparams.pem \
     /etc/nginx/
# Add Healthcheck
HEALTHCHECK --start-period=5s --interval=5s --retries=8 \
    CMD nc -z localhost 80 || exit 1



FROM base as debug
COPY certs /etc/nginx/
RUN cat /etc/nginx/central.crt /etc/nginx/ca.crt \
    >> /etc/nginx/central-fullchain.crt
COPY templates/dev/fmtm.conf.template \
     templates/dev/api.conf.template \
     templates/dev/odk.conf.template \
     templates/dev/minio.conf.template \
     templates/dev/sync.conf.template \
     /etc/nginx/templates/



FROM base as certs-init-main
# Replace existing /docker-entrypoint.sh
COPY container-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
COPY templates/cert-init/fmtm.conf.template \
     templates/cert-init/api.conf.template \
     templates/cert-init/minio.conf.template \
     templates/cert-init/sync.conf.template \
     /etc/nginx/templates/



FROM certs-init-main as certs-init-development
COPY templates/cert-init/odk.conf.template \
     /etc/nginx/templates/



FROM base as main
# API, Frontend, S3
COPY templates/fmtm.conf.template \
     templates/api.conf.template \
     templates/minio.conf.template \
     templates/sync.conf.template \
     /etc/nginx/templates/



FROM main as development
# API, Frontend, S3 + ODK
COPY templates/odk.conf.template \
     /etc/nginx/templates/
