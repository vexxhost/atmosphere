# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-17T13:34:17Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG MANILA_GIT_REF=ed585103e4c26478b60b397b0bb064b50dc1acb5
ADD --keep-git-dir=true https://opendev.org/openstack/manila.git#${MANILA_GIT_REF} /src/manila
RUN git -C /src/manila fetch --unshallow
COPY patches/manila /patches/manila
RUN git -C /src/manila apply --verbose /patches/manila/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/manila
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iproute2 openvswitch-switch
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
