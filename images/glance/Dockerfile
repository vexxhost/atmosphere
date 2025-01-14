# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  ceph-common \
  openstack-glance \
  python3-pip \
  python3-rbd \
  uwsgi-plugin-python3
EOF

FROM scratch
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --link --from=installer /target/ /
# TODO(mnaser): Remove this + "python3-pip" dependency once this is packaged
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
python3 -m pip install \
  storpool \
  storpool.spopenstack
EOF
ADD --chmod=644 \
  https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/caracal/storpool.py \
  /usr/lib/python3.9/site-packages/os_brick/initiator/connectors/storpool.py
