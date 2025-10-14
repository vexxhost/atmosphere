# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/ovn-bgp-agent repo=https://github.com/openstack/ovn-bgp-agent.git branch=stable/2025.2
ARG OVN_BGP_AGENT_GIT_REF=fe0d730b960dd9d0b6731a81bea148b36e63af8d
ADD --keep-git-dir=true https://github.com/openstack/ovn-bgp-agent.git#${OVN_BGP_AGENT_GIT_REF} /src/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent fetch --unshallow
COPY patches/ovn-bgp-agent /patches/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent apply --verbose /patches/ovn-bgp-agent/*
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
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
