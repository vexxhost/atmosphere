# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/octavia repo=https://opendev.org/openstack/octavia.git branch=zed-eol
ARG OCTAVIA_GIT_REF=ddfd2e4e42300ccf0cf0d865900d2ec252cee41a
ADD --keep-git-dir=true https://opendev.org/openstack/octavia.git#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
COPY patches/octavia /patches/octavia
RUN git -C /src/octavia apply --verbose /patches/octavia/*
# renovate: name=openstack/ovn-octavia-provider repo=https://opendev.org/openstack/ovn-octavia-provider.git branch=zed-eol
ARG OVN_OCTAVIA_PROVIDER_GIT_REF=2374cce13f6f5dc70cc5387e9c7b8fa2dc5bf0f0
ADD --keep-git-dir=true https://opendev.org/openstack/ovn-octavia-provider.git#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/octavia \
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
