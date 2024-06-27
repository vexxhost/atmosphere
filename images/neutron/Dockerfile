# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG NEUTRON_GIT_REF=019294c71d94b788c14b23dc1da3c21f51bcdb0b
ADD --keep-git-dir=true https://opendev.org/openstack/neutron.git#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas.git#master /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
ARG POLICY_SERVER_GIT_REF=4a86b140d5510823a8fb8a59137feddf5b111b26
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-policy-server.git#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-vpnaas \
        /src/neutron-policy-server
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    conntrack dnsmasq dnsmasq-utils ebtables ethtool haproxy iproute2 ipset iptables iputils-arping jq keepalived lshw openvswitch-switch strongswan uuid-runtime
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
