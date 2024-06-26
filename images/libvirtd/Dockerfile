# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-26T11:52:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-runtime:${RELEASE}
ADD --chmod=644 https://download.ceph.com/keys/release.gpg /etc/apt/trusted.gpg.d/ceph.gpg
COPY <<EOF /etc/apt/sources.list.d/ceph.list
deb http://download.ceph.com/debian-reef/ jammy main
EOF
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common cgroup-tools dmidecode ebtables iproute2 ipxe-qemu kmod libvirt-clients libvirt-daemon-system openssh-client openvswitch-switch ovmf pm-utils qemu-block-extra qemu-efi qemu-kvm seabios
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
