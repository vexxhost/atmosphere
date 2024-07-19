# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG NOVA_GIT_REF=f732f8476851e6272d8ad9937f54b918795844e8
ADD --keep-git-dir=true https://opendev.org/openstack/nova.git#${NOVA_GIT_REF} /src/nova
RUN git -C /src/nova fetch --unshallow
ARG SCHEDULER_FILTERS_GIT_REF=eb17f39c68606cca7ec68bf3e40d58e0954326ee
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
ADD --chmod=644 \
    https://github.com/storpool/storpool-openstack-integration/raw/master/drivers/os_brick/openstack/antelope/storpool.py \
    /var/lib/openstack/lib/python3.10/site-packages/os_brick/initiator/connectors/storpool.py

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
ADD https://github.com/novnc/noVNC.git#v1.4.0 /usr/share/novnc
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common genisoimage iproute2 libosinfo-bin lsscsi ndctl nvme-cli openssh-client ovmf python3-libvirt python3-rados python3-rbd qemu-efi-aarch64 qemu-block-extra qemu-utils sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
