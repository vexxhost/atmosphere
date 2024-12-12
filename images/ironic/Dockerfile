# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

ARG RELEASE

FROM harbor.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG IRONIC_GIT_REF=19de7ae2f48705cfa0e59d0642cec3cca7b6ca22
ADD --keep-git-dir=true https://opendev.org/openstack/ironic.git#${IRONIC_GIT_REF} /src/ironic
RUN git -C /src/ironic fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/ironic \
        python-dracclient \
        sushy
EOF

FROM harbor.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ethtool ipmitool iproute2 ipxe lshw qemu-block-extra qemu-utils tftpd-hpa
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
