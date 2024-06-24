FROM docker.io/node:20-slim
WORKDIR /app
COPY ./package.json ./pnpm-lock.yaml ./
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack use pnpm@9.3.0
RUN pnpm install
ENV NODE_ENV development
ENTRYPOINT ["pnpm", "run", "dev"]
