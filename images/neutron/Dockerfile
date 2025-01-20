# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-24T11:51:19Z

FROM openstack-venv-builder AS build
ARG NEUTRON_GIT_REPO
ARG NEUTRON_GIT_REF
ADD --keep-git-dir=true ${NEUTRON_GIT_REPO}#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
COPY patches/neutron /patches/neutron
RUN git -C /src/neutron apply --verbose /patches/neutron/*
ARG NEUTRON_VPNAAS_GIT_REPO
ARG NEUTRON_VPNAAS_GIT_REF
ADD --keep-git-dir=true ${NEUTRON_VPNAAS_GIT_REPO}#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
ARG NETWORKING_BAREMETAL_GIT_REPO
ARG NETWORKING_BAREMETAL_GIT_REF
ADD --keep-git-dir=true ${NETWORKING_BAREMETAL_GIT_REPO}#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
ARG POLICY_SERVER_GIT_REPO
ARG POLICY_SERVER_GIT_REF
ADD --keep-git-dir=true ${POLICY_SERVER_GIT_REPO}#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
ARG LOG_PARSER_GIT_REPO
ARG LOG_PARSER_GIT_REF
ADD --keep-git-dir=true ${LOG_PARSER_GIT_REPO}#${LOG_PARSER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
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
