FROM docker.io/node:18 as builder
ARG MAINTAINER=admin@hotosm.org

ARG APP_VERSION
ARG VITE_API_URL
ENV VITE_API_URL="${VITE_API_URL}"

LABEL org.hotosm.fmtm.app-name="fmtm-frontend" \
      org.hotosm.fmtm.app-version="${APP_VERSION}" \
      org.hotosm.fmtm.maintainer="${MAINTAINER}" \
      org.hotosm.fmtm.api-url="${VITE_API_URL}"

WORKDIR /app
COPY ./package.json ./pnpm-lock.yaml ./
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
RUN pnpm install

ENV NODE_ENV production
COPY . .
RUN npm run build


FROM docker.io/devforth/spa-to-http:1.0.3 as prod
WORKDIR /app
# Add non-root user, permissions
RUN adduser -D -u 900 -h /home/appuser appuser
USER appuser
COPY --from=builder --chown=appuser:appuser /app/dist .
