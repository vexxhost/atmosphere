# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-15T02:05:46Z

FROM ghcr.io/vexxhost/ubuntu-cloud-archive:2025.2@sha256:393e3d9c51fe69efb34cf629d2c9c1c80613b5f09d5c9919a2d959c0a84ab5ec
RUN <<EOF bash -xe
groupadd -g 42424 nova
useradd -u 42424 -g 42424 -M -d /var/lib/nova -s /usr/sbin/nologin -c "nova User" nova
mkdir -p /etc/nova /var/log/nova /var/lib/nova /var/cache/nova
chown -Rv nova:nova /etc/nova /var/log/nova /var/lib/nova /var/cache/nova
EOF
ADD --chmod=644 https://download.ceph.com/keys/release.gpg /etc/apt/trusted.gpg.d/ceph.gpg
COPY <<EOF /etc/apt/sources.list.d/ceph.list
deb http://download.ceph.com/debian-reef/ jammy main
EOF
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common cgroup-tools dmidecode ebtables iproute2 ipxe-qemu kmod libtpms0 libvirt-clients libvirt-daemon-system openssh-client openvswitch-switch ovmf pm-utils qemu-block-extra qemu-efi-aarch64 qemu-kvm seabios swtpm swtpm-tools
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
