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

# TODO this dockerfile is not complete, but is largely optimise
# over the official image (>800MB reduction)
ARG node_version=16


FROM docker.io/bitnami/git:2 as enketo
ARG ENKETO_TAG=6.2.2
RUN git clone --depth 1 --branch ${ENKETO_TAG} \
    "https://github.com/enketo/enketo-express.git"



FROM docker.io/bitnami/git:2 as central
ARG ODK_CENTRAL_TAG
RUN git clone --depth 1 --branch ${ODK_CENTRAL_TAG} \
    "https://github.com/getodk/central.git"



FROM docker.io/node:${node_version}-slim as build
WORKDIR /repo
COPY --from=enketo enketo-express/ .
RUN npm install -g npm@^6
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3 \
        openssh-client \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Skip chrome install for puppeteer
ENV PUPPETEER_SKIP_DOWNLOAD='true'
RUN npm ci
RUN npx grunt
RUN npm prune --production



FROM docker.io/node:${node_version}-slim as runtime
ENV ENKETO_SRC_DIR=/srv/src/enketo_express
WORKDIR ${ENKETO_SRC_DIR}
RUN npm install -g pm2@$(npm info pm2 version)
# Persist the `secrets` directory so the encryption key remains consistent.
RUN mkdir -p ${ENKETO_SRC_DIR}/setup/docker/secrets
VOLUME ${ENKETO_SRC_DIR}/setup/docker/secrets

# From ODK Central Config
COPY --from=central central/files/enketo/config.json.template \
    ${ENKETO_SRC_DIR}/config/config.json.template
COPY --from=central central/files/enketo/config.json.template \
    ${ENKETO_SRC_DIR}/config/config.json
COPY --from=central central/files/enketo/start-enketo.sh \
    ${ENKETO_SRC_DIR}/start-enketo.sh

RUN apt-get update && \
    apt-get install gettext-base \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /etc/secrets \
    && echo 'jhs9udhy987gyds98gfyds98f' > /etc/secrets/enketo-api-key \
    && echo 'jhs9udhy987gyds98gfyds98f' > /etc/secrets/enketo-secret \
    && echo 'jhs9udhy987gyds98gfyds98f' > /etc/secrets/enketo-less-secret 

COPY --from=build /repo/ ./

EXPOSE 8005

CMD ["./start-enketo.sh"]
