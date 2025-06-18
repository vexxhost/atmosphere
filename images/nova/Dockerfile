# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-12-17T01:27:44Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/nova repo=https://opendev.org/openstack/nova.git branch=stable/2025.1
ARG NOVA_GIT_REF=6943e035182c0664d81d4fea6ce85596f119ecd7
ADD --keep-git-dir=true https://opendev.org/openstack/nova.git#${NOVA_GIT_REF} /src/nova
RUN git -C /src/nova fetch --unshallow
# renovate: name=vexxhost/nova-scheduler-filters repo=https://github.com/vexxhost/nova-scheduler-filters.git branch=main
ARG SCHEDULER_FILTERS_GIT_REF=77ed1c2ca70f4166a6d0995c7d3d90822f0ca6c0
ADD --keep-git-dir=true https://github.com/vexxhost/nova-scheduler-filters.git#${SCHEDULER_FILTERS_GIT_REF} /src/nova-scheduler-filters
RUN git -C /src/nova-scheduler-filters fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/nova \
        /src/nova-scheduler-filters \
        python-ironicclient \
        storpool \
        storpool.spopenstack
EOF
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/caracal/storpool.py \
    /var/lib/openstack/lib/python3.12/site-packages/os_brick/initiator/connectors/storpool.py

FROM openstack-python-runtime
ADD https://github.com/novnc/noVNC.git#v1.4.0 /usr/share/novnc
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common dmidecode genisoimage iproute2 libosinfo-bin lsscsi ndctl nfs-common nvme-cli openssh-client ovmf python3-libvirt python3-rados python3-rbd qemu-efi-aarch64 qemu-block-extra qemu-utils sysfsutils udev util-linux swtpm swtpm-tools libtpms0
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
