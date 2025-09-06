# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/glance repo=https://github.com/openstack/glance.git branch=master
ARG GLANCE_GIT_REF=788172a6f7c7a214e87a80a27cb26ea33da67a58
ADD --keep-git-dir=true https://github.com/openstack/glance.git#${GLANCE_GIT_REF} /src/glance
RUN git -C /src/glance fetch --unshallow
# renovate: name=openstack/glance_store repo=https://github.com/openstack/glance_store.git branch=master
ARG GLANCE_STORE_GIT_REF=2fd7875820a531d26336a317d5c0841d452bc6f9
ADD --keep-git-dir=true https://github.com/openstack/glance_store.git#${GLANCE_STORE_GIT_REF} /src/glance_store
RUN git -C /src/glance_store fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/glance \
        /src/glance_store[cinder] \
        storpool \
        storpool.spopenstack
EOF
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/caracal/storpool.py \
    /var/lib/openstack/lib/python3.12/site-packages/os_brick/initiator/connectors/storpool.py

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common dmidecode lsscsi nvme-cli python3-rados python3-rbd qemu-block-extra qemu-utils sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --from=build --link /var/lib/openstack /var/lib/openstack
