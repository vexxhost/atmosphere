# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  iptables \
  openvswitch3.2 \
  openvswitch3.2-test \
  python3-netifaces \
  tcpdump
EOF

FROM scratch
ADD --chmod=755 https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
COPY --link --from=installer /target/ /
