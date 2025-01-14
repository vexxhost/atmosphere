# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  python3-openstackclient \
  python3-osc-placement \
  python3-barbicanclient \
  python3-designateclient \
  python3-glanceclient \
  python3-heatclient \
  python3-ironicclient \
  python3-magnumclient \
  python3-manilaclient \
  python3-neutronclient \
  python3-octaviaclient \
  python3-swiftclient
EOF

FROM scratch
COPY --link --from=installer /target/ /

# NOTE(mnaser): The Magnum client relies on the SHELL environment variable
#               to determine the shell to use.
ENV SHELL=/bin/bash

# NOTE(mnaser): When we call this container, we mount the current directory
#               into `/opt` and then we can call `openstack` commands.
WORKDIR /opt
