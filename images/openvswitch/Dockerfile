# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM quay.io/centos/centos:stream9
ADD --chmod=755 https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
ARG OVS_SERIES=3.2
ARG OVS_VERSION=${OVS_SERIES}.0-80
RUN <<EOF sh -xe
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    centos-release-nfv-openvswitch.noarch
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    iptables \
    openvswitch${OVS_SERIES}-${OVS_VERSION}.el9s \
    openvswitch${OVS_SERIES}-test-${OVS_VERSION}.el9s \
    python3-netifaces \
    tcpdump
dnf -y clean all
rm -rf /var/cache/dnf
EOF
