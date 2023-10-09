FROM docker.io/node:18
ARG API_URL
ENV API_URL="${API_URL}"
ARG FRONTEND_MAIN_URL
ENV FRONTEND_MAIN_URL="${FRONTEND_MAIN_URL}"
WORKDIR /app
COPY ./package*.json ./
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
RUN pnpm install
ENV NODE_ENV development
ENTRYPOINT ["npm", "run", "start:live"]
