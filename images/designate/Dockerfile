# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG DESIGNATE_GIT_REF=ff1986cbb755f0d74a7db98623d6d17816d933a6
ADD --keep-git-dir=true https://opendev.org/openstack/designate.git#${DESIGNATE_GIT_REF} /src/designate
RUN git -C /src/designate fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/designate
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    bind9utils
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
