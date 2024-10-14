# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-10-14T18:43:39Z

ARG RELEASE

FROM harbor.atmosphere.dev/library/openstack-runtime:${RELEASE}
# NOTE(mnaser): Noble ships with Ceph Reef, so we don't need to use upstream packages
# ADD --chmod=644 https://download.ceph.com/keys/release.gpg /etc/apt/trusted.gpg.d/ceph.gpg
# COPY <<EOF /etc/apt/sources.list.d/ceph.list
# deb http://download.ceph.com/debian-reef/ jammy main
# EOF
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common cgroup-tools dmidecode ebtables iproute2 ipxe-qemu kmod libvirt-clients libvirt-daemon-system openssh-client openvswitch-switch ovmf pm-utils qemu-block-extra qemu-efi-aarch64 qemu-kvm seabios
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
