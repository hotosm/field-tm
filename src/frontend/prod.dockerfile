FROM docker.io/node:18 as builder
ARG MAINTAINER=admin@hotosm.org

ARG APP_NAME
ARG URL_SCHEME
ARG API_URL
ENV API_URL=${URL_SCHEME}://${API_URL}
ARG FRONTEND_MAIN_URL
ENV FRONTEND_MAIN_URL=${URL_SCHEME}://${FRONTEND_MAIN_URL}
ARG FRONTEND_MAP_URL
ENV FRONTEND_MAP_URL=${URL_SCHEME}://${FRONTEND_MAP_URL}

LABEL fmtm.hotosm.org.maintainer="${MAINTAINER}" \
      fmtm.hotosm.org.api-url="${API_URL}" \
      fmtm.hotosm.org.main-url="${FRONTEND_MAIN_URL}" \
      fmtm.hotosm.org.fmtm_openlayer_map-url="${FRONTEND_MAP_URL}"

WORKDIR /app
COPY ./${APP_NAME}/package*.json ./
RUN npm install

ENV NODE_ENV production
COPY ${APP_NAME}/ .
RUN npm run build


FROM docker.io/devforth/spa-to-http:1.0.3
WORKDIR /app
# Add non-root user, permissions
RUN adduser -D -u 900 -h /home/appuser appuser
USER appuser
COPY --from=builder --chown=appuser:appuser /app/dist .
