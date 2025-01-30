# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM centos
ADD --chmod=755 https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
ARG OVS_SERIES=3.3
ARG OVS_VERSION=${OVS_SERIES}.0-80
RUN <<EOF sh -xe
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    centos-release-nfv-openvswitch.noarch
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    iptables \
    openvswitch${OVS_SERIES}-${OVS_VERSION}.el9s \
    openvswitch${OVS_SERIES}-test-${OVS_VERSION}.el9s \
    python3-netifaces \
    tcpdump \
    jq
dnf -y clean all
rm -rf /var/cache/dnf
usermod -u 42424 openvswitch
groupmod -g 42424 openvswitch
EOF
