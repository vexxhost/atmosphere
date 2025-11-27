# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/openstack-venv-builder:main@sha256:bff09007027c2b6b908e2e970fe5cf06a4c025848e69bad73aa4970aff4978e2 AS build
# renovate: name=openstack/ironic repo=https://github.com/openstack/ironic.git branch=master
ARG IRONIC_GIT_REF=5b2dd69ae16cb3c18c6d21c73e7ad716f078e50e
ADD --keep-git-dir=true https://github.com/openstack/ironic.git#${IRONIC_GIT_REF} /src/ironic
RUN git -C /src/ironic fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/ironic \
        python-dracclient \
        sushy
EOF

FROM ghcr.io/vexxhost/python-base:main@sha256:4ab6c0c1a31e169d3b158e8ad70963b91ea933ae63a279640ded5d37e92815b7
RUN \
    groupadd -g 42424 ironic && \
    useradd -u 42424 -g 42424 -M -d /var/lib/ironic -s /usr/sbin/nologin -c "Ironic User" ironic && \
    mkdir -p /etc/ironic /var/log/ironic /var/lib/ironic /var/cache/ironic && \
    chown -Rv ironic:ironic /etc/ironic /var/log/ironic /var/lib/ironic /var/cache/ironic
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ethtool ipmitool iproute2 ipxe lshw qemu-block-extra qemu-utils tftpd-hpa
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
