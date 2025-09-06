# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/octavia repo=https://github.com/openstack/octavia.git branch=stable/2024.1
ARG OCTAVIA_GIT_REF=041b0795972afe103ea802b47105f38ad45f65cb
ADD --keep-git-dir=true https://github.com/openstack/octavia.git#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
COPY patches/octavia /patches/octavia
RUN git -C /src/octavia apply --verbose /patches/octavia/*
# renovate: name=openstack/ovn-octavia-provider repo=https://github.com/openstack/ovn-octavia-provider.git branch=stable/2024.1
ARG OVN_OCTAVIA_PROVIDER_GIT_REF=8f157246c2d13f5e093a69e1d41250e8f6d6301a
ADD --keep-git-dir=true https://github.com/openstack/ovn-octavia-provider.git#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
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
