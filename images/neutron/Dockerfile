# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG NEUTRON_GIT_REF=ece6a9a7acab20d5a39f54784427258d54b72cfd
ADD --keep-git-dir=true https://opendev.org/openstack/neutron.git#${NEUTRON_GIT_REF} /src/neutron
RUN git -C /src/neutron fetch --unshallow
ARG NEUTRON_VPNAAS_GIT_REF=45d63e1e9adc2b3ce4e3b2b5728744f99ea70a97
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas.git#${NEUTRON_VPNAAS_GIT_REF} /src/neutron-vpnaas
RUN git -C /src/neutron-vpnaas fetch --unshallow
COPY patches/neutron /patches/neutron
RUN git -C /src/neutron apply --verbose /patches/neutron/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/neutron \
        /src/neutron-vpnaas
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
