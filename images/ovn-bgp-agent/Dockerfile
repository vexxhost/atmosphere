# syntax=docker/dockerfile:1
# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG OVN_BGP_AGENT_GIT_REF=3.0.0
ADD --keep-git-dir=true https://opendev.org/openstack/ovn-bgp-agent.git#${OVN_BGP_AGENT_GIT_REF} /src/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent fetch --unshallow
COPY patches/ovn-bgp-agent /patches/ovn-bgp-agent
RUN git -C /src/ovn-bgp-agent apply --verbose /patches/ovn-bgp-agent/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
#RUN <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/ovn-bgp-agent[frr_k8s]
EOF

FROM registry.atmosphere.dev/library/neutron:${RELEASE}
COPY --from=build --link /var/lib/openstack /var/lib/openstack
