# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-24T11:51:19Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/neutron-dynamic-routing repo=https://github.com/openstack/neutron-dynamic-routing.git branch=master
ARG NEUTRON_DYNAMIC_ROUTING_GIT_REF=9f21d9aa96427ca714b898ff966a33c09ff80696
ADD --keep-git-dir=true https://github.com/openstack/neutron-dynamic-routing.git#${NEUTRON_DYNAMIC_ROUTING_GIT_REF} /src/neutron-dynamic-routing
RUN git -C /src/neutron-dynamic-routing fetch --unshallow
# renovate: name=openstack/neutron-vpnaas repo=https://github.com/openstack/neutron-vpnaas.git branch=master
ARG NEUTRON_VPNAAS_GIT_REF=e0b5e2001b594edd350f0d87869e117b8bb464a1
ADD --keep-git-dir=true https://github.com/openstack/neutron-vpnaas.git#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
# renovate: name=openstack/networking-baremetal repo=https://github.com/openstack/networking-baremetal.git branch=master
ARG NETWORKING_BAREMETAL_GIT_REF=81d40be9ef65c0fd68c83358e316728fdcc9a9ac
ADD --keep-git-dir=true https://github.com/openstack/networking-baremetal.git#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
# renovate: name=openstack/networking-generic-switch repo=https://github.com/openstack/networking-generic-switch.git branch=master
ARG NETWORKING_GENERIC_SWITCH_GIT_REF=2f7f3e12369e46294a2be5c780db373ba831124c
ADD --keep-git-dir=true https://github.com/openstack/networking-generic-switch.git#${NETWORKING_GENERIC_SWITCH_GIT_REF} /src/networking-generic-switch
RUN git -C /src/networking-generic-switch fetch --unshallow
# renovate: name=vexxhost/neutron-policy-server repo=https://github.com/vexxhost/neutron-policy-server.git branch=main
ARG POLICY_SERVER_GIT_REF=41c862a7e15955195ebac56a48ae98137aac146d
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-policy-server.git#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
# renovate: name=vexxhost/neutron-ovn-network-logging-parser repo=https://github.com/vexxhost/neutron-ovn-network-logging-parser.git branch=main
ARG LOG_PASER_GIT_REF=3895d8f9d004e612c71b4f798d31c758e113946b
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-ovn-network-logging-parser.git#${LOG_PASER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
# renovate: name=openstack/tap-as-a-service repo=https://opendev.org/openstack/tap-as-a-service.git branch=master
ARG TAP_AS_A_SERVICE_GIT_REF=c06a9ff7963e23b2c7faff89b188bd9295a753cc
ADD --keep-git-dir=true https://opendev.org/openstack/tap-as-a-service.git#${TAP_AS_A_SERVICE_GIT_REF} /src/tap-as-a-service
RUN git -C /src/tap-as-a-service fetch --unshallow
RUN \
  --mount=type=bind,from=neutron-source,source=/,target=/src/neutron,readwrite \
  --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-dynamic-routing \
        /src/neutron-vpnaas \
        /src/networking-baremetal \
        /src/networking-generic-switch \
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
