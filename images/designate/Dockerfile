# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  bind-utils \
  openstack-designate-api \
  openstack-designate-central \
  openstack-designate-mdns \
  openstack-designate-producer \
  openstack-designate-sink \
  openstack-designate-worker \
  uwsgi-plugin-python3
EOF

FROM scratch
COPY --link --from=installer /target/ /
