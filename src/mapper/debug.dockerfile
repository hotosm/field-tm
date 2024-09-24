FROM docker.io/node:20-slim
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
          "openssl" \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ./package.json ./pnpm-lock.yaml ./
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack use pnpm@9.3.0
RUN pnpm install
ENV NODE_ENV development
ENTRYPOINT ["pnpm", "run", "dev"]
