# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-18T16:07:40Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/neutron repo=https://opendev.org/openstack/neutron.git branch=unmaintained/zed
ARG NEUTRON_GIT_REF=7227063997e4827a0cea5d59a466c55c53e914d2
ADD --keep-git-dir=true https://opendev.org/openstack/neutron.git#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas.git#zed-eol /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
# renovate: name=openstack/networking-baremetal repo=https://opendev.org/openstack/networking-baremetal.git branch=unmaintained/zed
ARG NETWORKING_BAREMETAL_GIT_REF=fc8ddc5f68eba645239e5faa3c370dab5cc94bc9
ADD --keep-git-dir=true https://opendev.org/openstack/networking-baremetal.git#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
# renovate: name=vexxhost/neutron-policy-server repo=https://github.com/vexxhost/neutron-policy-server.git branch=main
ARG POLICY_SERVER_GIT_REF=41c862a7e15955195ebac56a48ae98137aac146d
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-policy-server.git#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
# renovate: name=vexxhost/neutron-ovn-network-logging-parser repo=https://github.com/vexxhost/neutron-ovn-network-logging-parser.git branch=main
ARG LOG_PASER_GIT_REF=3895d8f9d004e612c71b4f798d31c758e113946b
ADD --keep-git-dir=true https://github.com/vexxhost/neutron-ovn-network-logging-parser.git#${LOG_PASER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
COPY patches/neutron /patches/neutron
RUN git -C /src/neutron apply --verbose /patches/neutron/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-vpnaas \
        /src/networking-baremetal \
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
