# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS build
# renovate: name=vexxhost/netoffload repo=https://github.com/vexxhost/netoffload.git branch=main
ARG NETOFFLOAD_GIT_REF=94b8c0fdb0b83bd1b7e14b9a58077a047c78a800
ADD https://github.com/vexxhost/netoffload.git#${NETOFFLOAD_GIT_REF} /src
WORKDIR /src
RUN go build -v -o offloadctl ./cmd/offloadctl/main.go

FROM ubuntu
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    jq mstflint
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /src/offloadctl /usr/local/bin/offloadctl
