FROM docker.io/node:18 AS base
ARG APP_VERSION=1.0.0
ARG APP_NAME
ARG MAINTAINER=admin@hotosm.org
ARG API_URL
ENV API_URL=${API_URL}
ARG FRONTEND_SCHEME
ENV FRONTEND_SCHEME=${FRONTEND_SCHEME}
ARG FRONTEND_DOMAIN
ENV FRONTEND_DOMAIN=${FRONTEND_DOMAIN}
ENV MAIN_PORT=8080
ENV FMTM_OPENLAYER_MAP_PORT=8081
LABEL fmtm.hotosm.org.app-name="${APP_NAME}" \
    fmtm.hotosm.org.app-version="${APP_VERSION}" \
    fmtm.hotosm.org.maintainer="${MAINTAINER}" \
    fmtm.hotosm.org.main-port="${MAIN_PORT}" \
    fmtm.hotosm.org.fmtm_openlayer_map-port="${FMTM_OPENLAYER_MAP_PORT}"
WORKDIR /app
COPY ./${APP_NAME}/package*.json ./
RUN npm install


FROM base AS debug
ENV NODE_ENV development
ENTRYPOINT ["npm", "run", "start:live"]


FROM base AS builder
ENV NODE_ENV production
COPY ./${APP_NAME} .
RUN npm run build


FROM docker.io/devforth/spa-to-http:1.0.3 as prod
WORKDIR /app
# Add non-root user, permissions
RUN adduser -D -u 900 -h /home/appuser appuser
USER appuser
COPY --from=builder --chown=appuser:appuser /app/dist .
