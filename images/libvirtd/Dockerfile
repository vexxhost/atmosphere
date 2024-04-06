# Copyright (c) 2024 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

FROM registry.atmosphere.dev/library/openstack-runtime:zed
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
