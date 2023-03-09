FROM docker.io/node:18 as builder
ARG MAINTAINER=admin@hotosm.org

ARG API_URL=https://fmtm-api.hotosm.org
ENV API_URL=${API_URL}
ARG FRONTEND_MAIN_URL=https://localhost:8000
ENV FRONTEND_MAIN_URL=${FRONTEND_MAIN_URL}
ARG FRONTEND_MAP_URL=https://localhost:8001
ENV FRONTEND_MAP_URL=${FRONTEND_MAP_URL}

LABEL fmtm.hotosm.org.maintainer="${MAINTAINER}" \
    fmtm.hotosm.org.api-url="${API_URL}" \
    fmtm.hotosm.org.main-url="${FRONTEND_MAIN_URL}" \
    fmtm.hotosm.org.fmtm_openlayer_map-url="${FRONTEND_MAP_URL}"

WORKDIR /app
COPY ./package*.json ./
RUN npm install

ENV NODE_ENV production
COPY . .
RUN npm run build


FROM docker.io/devforth/spa-to-http:1.0.3
WORKDIR /app
# Add non-root user, permissions
RUN adduser -D -u 900 -h /home/appuser appuser
USER appuser
COPY --from=builder --chown=appuser:appuser /app/dist .
