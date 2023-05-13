FROM docker.io/node:18 as builder
ARG MAINTAINER=admin@hotosm.org

ARG APP_NAME
ARG APP_VERSION
ARG URL_SCHEME
ARG API_URL
ENV API_URL=${URL_SCHEME}://${API_URL}
ARG FRONTEND_MAIN_URL
ENV FRONTEND_MAIN_URL=${URL_SCHEME}://${FRONTEND_MAIN_URL}
ARG FRONTEND_MAP_URL
ENV FRONTEND_MAP_URL=${URL_SCHEME}://${FRONTEND_MAP_URL}

LABEL org.hotosm.fmtm.app-name="${APP_NAME}" \
      org.hotosm.fmtm.app-version="${APP_VERSION}" \
      org.hotosm.fmtm.maintainer="${MAINTAINER}" \
      org.hotosm.fmtm.api-url="${API_URL}" \
      org.hotosm.fmtm.main-url="${FRONTEND_MAIN_URL}" \
      org.hotosm.fmtm.fmtm_openlayer_map-url="${FRONTEND_MAP_URL}"

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
