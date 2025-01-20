# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG REGISTRY
ARG RELEASE

FROM ${REGISTRY}/openstack-venv-builder:${RELEASE} AS build
ARG MANILA_GIT_REPO
ARG MANILA_GIT_REF=d8987589ae88ae9b2769fbe6f26d5b6994098038
ADD --keep-git-dir=true ${MANILA_GIT_REPO}#${MANILA_GIT_REF} /src/manila
RUN git -C /src/manila fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/manila
EOF

FROM ${REGISTRY}/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iproute2 openvswitch-switch
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
