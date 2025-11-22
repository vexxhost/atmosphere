# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/octavia repo=https://github.com/openstack/octavia.git branch=master
ARG OCTAVIA_GIT_REF=ff8ced223e689645521e1a8defc6b7bb464a34e7
ADD --keep-git-dir=true https://github.com/openstack/octavia.git#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
# renovate: name=openstack/ovn-octavia-provider repo=https://github.com/openstack/ovn-octavia-provider.git branch=master
ARG OVN_OCTAVIA_PROVIDER_GIT_REF=65a4e822ce88453cff171c1a5a38d328d23331d9
ADD --keep-git-dir=true https://github.com/openstack/ovn-octavia-provider.git#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/octavia[redis] \
        /src/ovn-octavia-provider
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    isc-dhcp-client openssh-client
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
