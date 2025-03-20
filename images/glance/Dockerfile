# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-18T16:06:32Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/glance repo=https://opendev.org/openstack/glance.git branch=unmaintained/zed
ARG GLANCE_GIT_REF=8bbe205c6497032790505579accb4cf1ff341599
ADD --keep-git-dir=true https://opendev.org/openstack/glance.git#${GLANCE_GIT_REF} /src/glance
RUN git -C /src/glance fetch --unshallow
# renovate: name=openstack/glance_store repo=https://opendev.org/openstack/glance_store.git branch=unmaintained/zed
ARG GLANCE_STORE_GIT_REF=ff4513e715ebf407d27e31ef46a115174720926d
ADD --keep-git-dir=true https://opendev.org/openstack/glance_store.git#${GLANCE_STORE_GIT_REF} /src/glance_store
RUN git -C /src/glance_store fetch --unshallow
COPY patches/glance_store /patches/glance_store
RUN git -C /src/glance_store apply --verbose /patches/glance_store/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/glance \
        /src/glance_store[cinder] \
        storpool \
        storpool.spopenstack
EOF
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/zed/storpool.py \
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
