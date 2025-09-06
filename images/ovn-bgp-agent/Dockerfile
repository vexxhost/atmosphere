# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/ovn-bgp-agent repo=https://github.com/openstack/ovn-bgp-agent.git branch=master
ARG OVN_BGP_AGENT_GIT_REF=bca2e5f2d79e854fdef7194c7a31907f7fcbad16
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
