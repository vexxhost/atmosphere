# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/openstack-venv-builder:main@sha256:bff09007027c2b6b908e2e970fe5cf06a4c025848e69bad73aa4970aff4978e2 AS build
# renovate: name=openstack/ovn-bgp-agent repo=https://github.com/openstack/ovn-bgp-agent.git branch=master
ARG OVN_BGP_AGENT_GIT_REF=36746cf1c18720e4a9ef45f779cd53c5a412bd6c
ADD --keep-git-dir=true https://github.com/openstack/ovn-bgp-agent.git#${OVN_BGP_AGENT_GIT_REF} /src/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent fetch --unshallow
COPY patches/ovn-bgp-agent /patches/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent apply --verbose /patches/ovn-bgp-agent/*
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/ovn-bgp-agent[frr_k8s]
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iproute2 openvswitch-switch
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
