# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-24T11:51:19Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/neutron-dynamic-routing repo=https://opendev.org/openstack/neutron-dynamic-routing.git branch=stable/2024.1
ARG NEUTRON_DYNAMIC_ROUTING_GIT_REF=4f6b9f262f44d532b8120507eef688c57cf28ec1
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-dynamic-routing.git#${NEUTRON_DYNAMIC_ROUTING_GIT_REF} /src/neutron-dynamic-routing
RUN git -C /src/neutron-dynamic-routing fetch --unshallow
# renovate: name=openstack/neutron-vpnaas repo=https://opendev.org/openstack/neutron-vpnaas.git branch=stable/2024.1
ARG NEUTRON_VPNAAS_GIT_REF=8655ef2b0f95a600639636665dd4b83b0a107bc7
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas.git#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
# renovate: name=openstack/networking-baremetal repo=https://opendev.org/openstack/networking-baremetal.git branch=stable/2024.1
ARG NETWORKING_BAREMETAL_GIT_REF=8dc6edadce564ad4896ecfd5d2bca68396d1d7e6
ADD --keep-git-dir=true https://opendev.org/openstack/networking-baremetal.git#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
# renovate: name=openstack/networking-generic-switch repo=https://opendev.org/openstack/networking-generic-switch.git branch=stable/2024.1
ARG NETWORKING_GENERIC_SWITCH_GIT_REF=dc142ec17910ebb0855f9cc21b77af2c554a7bbe
ADD --keep-git-dir=true https://opendev.org/openstack/networking-generic-switch.git#${NETWORKING_GENERIC_SWITCH_GIT_REF} /src/networking-generic-switch
RUN git -C /src/networking-generic-switch fetch --unshallow
# renovate: name=vexxhost/neutron-policy-server repo=https://github.com/vexxhost/neutron-policy-server.git branch=main
ARG POLICY_SERVER_GIT_REF=41c862a7e15955195ebac56a48ae98137aac146d
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-policy-server.git#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
# renovate: name=vexxhost/neutron-ovn-network-logging-parser repo=https://github.com/vexxhost/neutron-ovn-network-logging-parser.git branch=main
ARG LOG_PASER_GIT_REF=3895d8f9d004e612c71b4f798d31c758e113946b
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-ovn-network-logging-parser.git#${LOG_PASER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
RUN \
  --mount=type=bind,from=neutron-source,source=/,target=/src/neutron,readwrite \
  --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-dynamic-routing \
        /src/neutron-vpnaas \
        /src/networking-baremetal \
        /src/networking-generic-switch \
        /src/neutron-policy-server \
        /src/neutron-ovn-network-logging-parser
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
