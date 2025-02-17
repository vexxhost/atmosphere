# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-12-17T01:27:44Z

FROM openstack-venv-builder AS build
ARG NOVA_GIT_REF=11301e7e3f0d81a3368632f90608e30d9c647111
ADD --keep-git-dir=true https://opendev.org/openstack/nova.git#${NOVA_GIT_REF} /src/nova
RUN git -C /src/nova fetch --unshallow
COPY patches/nova /patches/nova
RUN git -C /src/nova apply --verbose /patches/nova/*
ARG SCHEDULER_FILTERS_GIT_REF=77ed1c2ca70f4166a6d0995c7d3d90822f0ca6c0
ADD --keep-git-dir=true https://github.com/vexxhost/nova-scheduler-filters.git#${SCHEDULER_FILTERS_GIT_REF} /src/nova-scheduler-filters
RUN git -C /src/nova-scheduler-filters fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/nova \
        /src/nova-scheduler-filters \
        python-ironicclient \
        storpool \
        storpool.spopenstack
EOF
<<<<<<< HEAD   (365139 Release 4.2.12)
=======
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/caracal/storpool.py \
    /var/lib/openstack/lib/python3.10/site-packages/os_brick/initiator/connectors/storpool.py
>>>>>>> CHANGE (4672c4 Upgrade Storpool driver to Caracal)

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
