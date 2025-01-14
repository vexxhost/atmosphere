# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

FROM --platform=$BUILDPLATFORM quay.io/centos/centos:stream9 AS installer
ADD dnf.conf /etc/dnf/dnf.conf
ARG BUILDARCH
RUN --mount=type=cache,id=dnf-cache-${BUILDARCH},target=/var/cache/dnf <<EOF bash -xe
dnf config-manager --set-enabled crb
dnf install -y centos-release-openstack-dalmatian epel-release
dnf config-manager --save --setopt="epel.priority=100" --setopt="epel-next.priority=100"
EOF
ADD install-packages /usr/local/bin/install-packages
