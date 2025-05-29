FROM docker.io/alpine/curl:8.11.1 AS base


# Download and verify tilepack binary
# FROM base AS tilepack
# ENV GO_TILEPACK_URL=https://github.com/tilezen/go-tilepacks/releases/download/v1.0.0-pre1/tilepack_1.0.0-pre1_linux_amd64.tar.gz \
#     TILEPACK_SHA1SUM=1f235fd3da7f9c8a2710a1a8d44a27c2c98df939
# RUN curl -fsSLO "$GO_TILEPACK_URL" \
#     && tar -xvzf tilepack_1.0.0-pre1_linux_amd64.tar.gz \
#     && echo "${TILEPACK_SHA1SUM}  tilepack" | sha1sum -c - \
#     && chmod +x tilepack \
#     && mv tilepack /tilepack
# FIXME temp workaround using fork until PRs merged
# - https://github.com/tilezen/go-tilepacks/pull/36
# - https://github.com/tilezen/go-tilepacks/pull/38
FROM base AS tilepack
ENV GO_TILEPACK_URL=https://github.com/spwoodcock/go-tilepacks/releases/download/0.4.0/tilepack_0.4.0_linux_amd64.tar.gz \
    TILEPACK_SHA1SUM=fcccfbdfbb06f3826192dd3898ce5e44b0bc241c
RUN curl -fsSLO "$GO_TILEPACK_URL" \
    && tar -xvzf tilepack_0.4.0_linux_amd64.tar.gz \
    && echo "${TILEPACK_SHA1SUM}  tilepack" | sha1sum -c - \
    && chmod +x tilepack \
    && mv tilepack /tilepack



# Download and verify pmtiles binary
FROM base AS pmtiles
ENV GO_PMTILES_URL=https://github.com/protomaps/go-pmtiles/releases/download/v1.25.0/go-pmtiles_1.25.0_Linux_x86_64.tar.gz \
    PMTILES_SHA1SUM=ed4795e24bfcccc4fd07a54dfc7926e15cc835de
RUN curl -fsSLO "$GO_PMTILES_URL" \
    && tar -xvzf go-pmtiles_1.25.0_Linux_x86_64.tar.gz \
    && echo "${PMTILES_SHA1SUM}  pmtiles" | sha1sum -c - \
    && chmod +x pmtiles \
    && mv pmtiles /pmtiles


# Add a non-root user to passwd file
FROM base AS useradd
RUN addgroup -g 1000 nonroot
RUN adduser -D -u 1000 -G nonroot nonroot


# Deploy the application binary into scratch image
FROM scratch AS release
WORKDIR /app
COPY --from=useradd /etc/group /etc/group
COPY --from=useradd /etc/passwd /etc/passwd
COPY --from=tilepack /tilepack /usr/bin/tilepack
COPY --from=pmtiles /pmtiles /usr/bin/pmtiles
USER nonroot:nonroot
ENTRYPOINT ["tilepack"]
