FROM debian:trixie-slim AS build

ARG LIGHTNINGCSS_VERSION=1.31.1
ARG TARGETARCH

RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --quiet --no-install-recommends \
        ca-certificates \
        curl \
        tar \
        libgcc-s1 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /out
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) pkg="lightningcss-cli-linux-x64-gnu" ;; \
      arm64) pkg="lightningcss-cli-linux-arm64-gnu" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fsSL "https://registry.npmjs.org/${pkg}/-/${pkg}-${LIGHTNINGCSS_VERSION}.tgz" -o /tmp/lightningcss.tgz; \
    tar -xzf /tmp/lightningcss.tgz -C /tmp; \
    install -m 0755 /tmp/package/lightningcss /out/lightningcss; \
    /out/lightningcss --version

FROM debian:trixie-slim
LABEL org.opencontainers.image.authors="sam.woodcock@hotosm.org"
RUN apt-get update --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --quiet --no-install-recommends \
        libgcc-s1 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/lightningcss /usr/local/bin/lightningcss
ENTRYPOINT ["/usr/local/bin/lightningcss"]
