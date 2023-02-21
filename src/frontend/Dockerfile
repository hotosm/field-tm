FROM docker.io/node:18 AS base
ARG APP_VERSION=1.0.0
ARG MAINTAINER=admin@hotosm.org
LABEL fmtm.hotosm.org.app-version="${APP_VERSION}" \
    fmtm.hotosm.org.maintainer="${MAINTAINER}" \
    fmtm.hotosm.org.api-port="3000"
WORKDIR /app
COPY main/package*.json ./
RUN npm install


FROM base AS debug
ENV NODE_ENV development
ENTRYPOINT ["npm", "run", "start:live"]


FROM base AS builder
ENV NODE_ENV production
COPY ./main .
RUN npm run build


FROM docker.io/devforth/spa-to-http:1.0.3 as prod
WORKDIR /app
# Add non-root user, permissions
RUN adduser -D -u 900 -h /home/appuser appuser
USER appuser
COPY --from=builder --chown=appuser:appuser /app/dist .
