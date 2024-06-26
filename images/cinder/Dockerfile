# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-26T11:52:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG CINDER_GIT_REF=0ff4262fba803152e94e32e0dc8e4a2e56fcb0f5
ADD --keep-git-dir=true https://opendev.org/openstack/cinder.git#${CINDER_GIT_REF} /src/cinder
RUN git -C /src/cinder fetch --unshallow
COPY patches/cinder /patches/cinder
RUN git -C /src/cinder apply --verbose /patches/cinder/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/cinder \
        purestorage \
        storpool \
        storpool.spopenstack
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common lsscsi nvme-cli python3-rados python3-rbd qemu-utils qemu-block-extra sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --from=build --link /var/lib/openstack /var/lib/openstack
