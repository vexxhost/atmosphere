# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-28T12:14:26Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG GLANCE_GIT_REF=06a18202ab52c64803f044b8f848ed1c160905d2
ADD --keep-git-dir=true https://opendev.org/openstack/glance.git#${GLANCE_GIT_REF} /src/glance
RUN git -C /src/glance fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/glance_store.git#unmaintained/zed /src/glance_store
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

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common lsscsi nvme-cli python3-rados python3-rbd qemu-block-extra qemu-utils sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --from=build --link /var/lib/openstack /var/lib/openstack
