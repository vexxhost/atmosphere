# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/cinder repo=https://opendev.org/openstack/cinder.git branch=master
ARG CINDER_GIT_REF=a0b8f270e60606cf5ae1fe97fd1abe6030bb10c9
ADD --keep-git-dir=true https://opendev.org/openstack/cinder.git#${CINDER_GIT_REF} /src/cinder
RUN git -C /src/cinder fetch --unshallow
COPY patches/cinder /patches/cinder
RUN git -C /src/cinder apply --verbose /patches/cinder/*
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/cinder \
        kubernetes \
        purestorage \
        python-3parclient \
        sherlock \
        storpool \
        storpool.spopenstack
EOF
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/cinder/openstack/caracal/storpool.py \
    /var/lib/openstack/lib/python3.12/site-packages/cinder/volume/drivers/storpool.py
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/caracal/storpool.py \
    /var/lib/openstack/lib/python3.12/site-packages/os_brick/initiator/connectors/storpool.py

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common dmidecode lsscsi nfs-common nvme-cli python3-rados python3-rbd qemu-utils qemu-block-extra sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --from=build --link /var/lib/openstack /var/lib/openstack
