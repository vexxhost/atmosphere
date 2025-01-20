# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG REGISTRY
ARG RELEASE

FROM ${REGISTRY}/openstack-venv-builder:${RELEASE} AS build
ARG NEUTRON_GIT_REPO
ARG NEUTRON_GIT_REF=019294c71d94b788c14b23dc1da3c21f51bcdb0b
ADD --keep-git-dir=true ${NEUTRON_GIT_REPO}#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
ARG NEUTRON_VPNAAS_GIT_REPO
ARG NEUTRON_VPNAAS_GIT_REF=7bc6d94305d34269d7522a9850c22aa42b50cdab
ADD --keep-git-dir=true ${NEUTRON_VPNAAS_GIT_REPO}#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
ARG NETWORKING_BAREMETAL_GIT_REPO
ARG NETWORKING_BAREMETAL_GIT_REF=8b92ad81c0bdbfde60a6f0c47ff0133c08bb617e
ADD --keep-git-dir=true ${NETWORKING_BAREMETAL_GIT_REPO}#${NETWORKING_BAREMETAL_GIT_REF} /src/networking-baremetal
RUN git -C /src/networking-baremetal fetch --unshallow
ARG POLICY_SERVER_GIT_REPO
ARG POLICY_SERVER_GIT_REF=85f47edbcf66aaf3a289dc3ae76191adce91018f
ADD --keep-git-dir=true ${POLICY_SERVER_GIT_REPO}#${POLICY_SERVER_GIT_REF} /src/neutron-policy-server
RUN git -C /src/neutron-policy-server fetch --unshallow
ARG LOG_PASER_GIT_REPO
ARG LOG_PASER_GIT_REF=9bc923c1294864ec709c538ba5c309065ef710d5
ADD --keep-git-dir=true ${LOG_PASER_GIT_REPO}#${LOG_PASER_GIT_REF} /src/neutron-ovn-network-logging-parser
RUN git -C /src/neutron-ovn-network-logging-parser fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-vpnaas \
        /src/networking-baremetal \
        /src/neutron-policy-server \
        /src/neutron-ovn-network-logging-parser
EOF

FROM ${REGISTRY}/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    conntrack dnsmasq dnsmasq-utils ebtables ethtool haproxy iproute2 ipset iptables iputils-arping jq keepalived lshw openvswitch-switch strongswan uuid-runtime
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
