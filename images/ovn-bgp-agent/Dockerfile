# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-01-10T15:08:57Z

FROM openstack-venv-builder AS build
ARG OVN_BGP_AGENT_GIT_REPO=https://opendev.org/openstack/ovn-bgp-agent.git
ARG OVN_BGP_AGENT_GIT_REF=3.0.0
ADD --keep-git-dir=true ${OVN_BGP_AGENT_GIT_REPO}#${OVN_BGP_AGENT_GIT_REF} /src/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent fetch --unshallow
COPY patches/ovn-bgp-agent /patches/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent apply --verbose /patches/ovn-bgp-agent/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
#RUN <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/ovn-bgp-agent[frr_k8s]
EOF

FROM openstack-neutron
COPY --from=build --link /var/lib/openstack /var/lib/openstack
