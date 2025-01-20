# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG GLANCE_GIT_REPO
ARG GLANCE_GIT_REF
ADD --keep-git-dir=true ${GLANCE_GIT_REPO}#${GLANCE_GIT_REF} /src/glance
RUN git -C /src/glance fetch --unshallow
ARG GLANCE_STORE_GIT_REPO
ARG GLANCE_STORE_GIT_REF
ADD --keep-git-dir=true ${GLANCE_STORE_GIT_REPO}#${GLANCE_STORE_GIT_REF} /src/glance_store
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
    /var/lib/openstack/lib/python3.10/site-packages/os_brick/initiator/connectors/storpool.py

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
