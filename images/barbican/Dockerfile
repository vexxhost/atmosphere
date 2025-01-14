# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  openstack-barbican \
  uwsgi-plugin-python3 \
  https://trunk.rdoproject.org/centos9-dalmatian/build-deps/latest/noarch/python3-pykmip-0.8.0-9.el9s.noarch.rpm
EOF

FROM scratch
COPY --link --from=installer /target/ /
