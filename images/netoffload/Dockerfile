# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG REGISTRY
ARG RELEASE

FROM harbor.atmosphere.dev/docker.io/library/golang:1.20 AS build
ARG NETOFFLOAD_GIT_REPO
ARG NETOFFLOAD_GIT_REF
ADD ${NETOFFLOAD_GIT_REPO}#${NETOFFLOAD_GIT_REF} /src
WORKDIR /src
RUN go build -v -o offloadctl ./cmd/offloadctl/main.go

FROM ${REGISTRY}/ubuntu:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    jq mstflint
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /src/offloadctl /usr/local/bin/offloadctl
