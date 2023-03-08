
FROM node:14.20-alpine as build
ARG MAINTAINER=admin@hotosm.org

ARG API_URL=https://fmtm-api.hotosm.org
ENV API_URL=${API_URL}
ARG FRONTEND_MAIN_URL=http://localhost:8080
ENV FRONTEND_MAIN_URL=${FRONTEND_MAIN_URL}
ARG FRONTEND_MAP_URL=https://map.fmtm.hotosm.org
ENV FRONTEND_MAP_URL=${FRONTEND_MAP_URL}

WORKDIR /main
COPY package.json .
RUN npm install
COPY . .
RUN npm run build
FROM nginx:latest
COPY --from=build  /main/dist /usr/share/nginx/html


# FROM docker.io/devforth/spa-to-http:1.0.3
# WORKDIR /app
# # Add non-root user, permissions
# RUN adduser -D -u 900 -h /home/appuser appuser
# USER appuser
# COPY --from=builder --chown=appuser:appuser /app/dist .
