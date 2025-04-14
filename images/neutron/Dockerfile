# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-24T11:51:19Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/neutron repo=https://opendev.org/openstack/neutron.git branch=master
ARG NEUTRON_GIT_REF=286541a57a8194b06985c2bf1778b73c56ca5e0f
ADD --keep-git-dir=true https://opendev.org/openstack/neutron.git#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
COPY patches/neutron /patches/neutron
RUN git -C /src/neutron apply --verbose /patches/neutron/*
# renovate: name=openstack/neutron-vpnaas repo=https://opendev.org/openstack/neutron-vpnaas.git branch=master
ARG NEUTRON_VPNAAS_GIT_REF=990e478b1e6db459b6cb9aec53ce808e2957bb65
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas.git#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
# renovate: name=openstack/networking-baremetal repo=https://opendev.org/openstack/networking-baremetal.git branch=master
ARG NETWORKING_BAREMETAL_GIT_REF=1fba63ce21619d3fe70117c6679e53629c612bc1
ADD --keep-git-dir=true https://opendev.org/openstack/networking-baremetal.git#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
# renovate: name=vexxhost/neutron-policy-server repo=https://github.com/vexxhost/neutron-policy-server.git branch=main
ARG POLICY_SERVER_GIT_REF=41c862a7e15955195ebac56a48ae98137aac146d
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-policy-server.git#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
# renovate: name=vexxhost/neutron-ovn-network-logging-parser repo=https://github.com/vexxhost/neutron-ovn-network-logging-parser.git branch=main
ARG LOG_PASER_GIT_REF=f9ca8427d074bf90638bed0b60e0d3656b6c2825
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-ovn-network-logging-parser.git#${LOG_PASER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
# renovate: name=openstack/tap-as-a-service repo=https://opendev.org/openstack/tap-as-a-service.git branch=master
ARG TAP_AS_A_SERVICE_GIT_REF=6ef9395531010fb27f364eca52474dd890db84af
ADD --keep-git-dir=true https://opendev.org/openstack/tap-as-a-service.git#${TAP_AS_A_SERVICE_GIT_REF} /src/tap-as-a-service
RUN git -C /src/tap-as-a-service fetch --unshallow

RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-vpnaas \
        /src/networking-baremetal \
        /src/neutron-policy-server \
        /src/neutron-ovn-network-logging-parser \
        /src/tap-as-a-service
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    conntrack dnsmasq dnsmasq-utils ebtables ethtool haproxy iproute2 ipset iptables iputils-arping jq keepalived lshw openvswitch-switch strongswan uuid-runtime
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=ovsinit /usr/local/bin/ovsinit /usr/local/bin/ovsinit
COPY --from=build --link /var/lib/openstack /var/lib/openstack
