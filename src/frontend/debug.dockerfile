FROM docker.io/node:18
ARG VITE_API_URL
ENV VITE_API_URL="${VITE_API_URL}"
WORKDIR /app
COPY ./package.json ./pnpm-lock.yaml ./
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
RUN pnpm install
ENV NODE_ENV development
ENTRYPOINT ["npm", "run", "start:live"]
