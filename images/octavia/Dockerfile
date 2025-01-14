# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  dhclient \
  openssh-clients \
  openstack-octavia-api \
  openstack-octavia-health-manager \
  openstack-octavia-housekeeping \
  openstack-octavia-worker \
  python3-ovn-octavia-provider \
  uwsgi-plugin-python3
EOF

FROM scratch
COPY --link --from=installer /target/ /
