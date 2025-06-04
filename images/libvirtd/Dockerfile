# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-15T02:05:46Z

FROM openstack-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common cgroup-tools dmidecode ebtables iproute2 ipxe-qemu kmod libtpms0 libvirt-clients libvirt-daemon-system openssh-client openvswitch-switch ovmf pm-utils qemu-block-extra qemu-efi-aarch64 qemu-kvm seabios swtpm swtpm-tools
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
